---
title: "Declare and serve chat jobs from a worker"
summary: "Declare a chat backend on the text pop, read a popped chat job, and submit its reply or fault."
topics: [text, workers]
order: 85
---

# Declare and serve chat jobs from a worker

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [text](../topics.md#text), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

A text worker receives chat jobs when its text pop declares a chat model, the capabilities and guarantees its backend
supports, and the limits chat jobs run under. `horde_sdk.worker.chat_declaration` builds those pop fields, reads the
popped job and builds the submit body. Sending the pop and submit requests stays with the worker's client.

```python
from horde_sdk.generation_parameters.text import ChatWorkerLimits
from horde_sdk.worker.chat_declaration import (
    ChatBackendFacts,
    ChatFaultReason,
    ChatFinishReason,
    ChatJobPayload,
    ChatToolStrategy,
    ChatUsage,
    build_chat_fault_submit,
    build_chat_reply_submit,
    declare_from_backend,
)

facts = ChatBackendFacts(
    honours_seed=True,
    renders_tools=True,
    tool_strategy=ChatToolStrategy.TEMPLATE,
    refuses_prompt_overflow=True,
    tools_temperature_cap=1.0,
)
declaration = declare_from_backend(
    facts,
    model_id="koboldcpp/Example-8B",
    limits=ChatWorkerLimits(max_context_length=8192, max_length=512),
)
pop_body = {
    "name": "my-worker",
    "models": ["koboldcpp/Example-8B"],
    **declaration.to_pop_fields(),
}

# pop_response is the parsed JSON of the text pop.
if pop_response.get("chat") is True:
    chat_job = ChatJobPayload.from_pop(pop_response)
    if chat_job.undeclared_features(declaration):
        submit_body = build_chat_fault_submit(
            chat_job.job_id, "koboldcpp/Example-8B", ChatFaultReason.GENERATION_ERROR
        )
    else:
        reply_text = run_backend(chat_job)  # the worker's own generation call
        submit_body = build_chat_reply_submit(
            chat_job.job_id,
            "koboldcpp/Example-8B",
            {"content": reply_text},
            ChatFinishReason.STOP,
            ChatUsage(completion_tokens=42),
        )
```

## Declaring the backend

1. Fill `ChatBackendFacts` with what the backend implements. Every fact defaults to the conservative answer.
2. Call `declare_from_backend`. A guarantee is declared only when the fact behind it is true: `tool_choice_enforced`
   and `single_tool_call_enforced` need the `grammar` tool strategy, `structured_output_enforced` needs a JSON Schema
   constraint that faults when the schema cannot be built, and `prompt_overflow_refused` needs a worker that faults a
   prompt that does not fit rather than trimming it.
3. Pass operator settings through `exclude` and the `tools_max_temperature` of `limits`. Both narrow the declaration;
   neither can add a value the facts do not back.
4. Merge `to_pop_fields()` into every text pop. `model_id` has to be one of the pop's `models`. A pop without
   `chat_jobs` withdraws the declaration.

A worker that builds `ChatWorkerDeclaration` directly gets the same consistency checks: vision needs an image
transport, a chat declaration needs a model and limits, and a chat-only worker (`prompt_jobs=False`) needs
`chat_jobs`.

## Serving the job

`ChatJobPayload.from_pop` reads a pop response that carries `chat: true`. The tool keys arrive narrowed: under
`tool_choice: none` no tool key is sent, and a choice of one function arrives as that one tool with
`tool_choice: required`. Every sampling field is present, so the backend's own defaults never apply.

`undeclared_features` compares the job's capabilities with the declaration. The server routes only jobs a worker
declared support for, so a non-empty result points at a routing fault; faulting the job is better than a reply that
ignores part of the request. The pop payload carries no conformance mode, so guarantees are not compared.

## Submitting

`build_chat_reply_submit` returns the structured submit body: an assistant `message` with `content`, `tool_calls` or
both, the `finish_reason`, and the token counts the backend reported. A reply that finishes with `tool_calls` has to
carry calls. `build_chat_fault_submit` returns a faulted submit with a `ChatFaultReason`; the AI Horde stores its own
sentence for the reason, never worker text. Use `prompt_overflow` for a prompt that does not fit,
`unbuildable_grammar` when the backend cannot build the grammar for the tool choice or response format,
`tool_violation` for a reply that broke the tool controls, `reply_refused` after the AI Horde refused the reply with a
`400`, and `generation_error` for a backend failure.

## Verification

A pop with the declaration returns `200`; a declaration the server refuses returns `400 ChatDeclarationInvalid`. A
submit the server accepts returns `200`; a reply it refuses returns `400 ChatSubmitInvalid` or
`ChatSubmitNonconformant`, after which the worker submits `reply_refused`.
