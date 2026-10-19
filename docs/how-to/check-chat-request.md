---
title: "Check a chat request before sending it"
summary: "Test an OpenAI-shaped chat request against the shared limits and a model's declared chat features locally."
topics: [requests, text]
order: 25
---

# Check a chat request before sending it

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [requests](../topics.md#requests), [text](../topics.md#text)
<!-- END GENERATED: topics -->

A chat request the AI Horde cannot serve is refused with a `400` or waits with `is_possible` false. Both answers can
be predicted locally from the request body, the shared limits in `horde_sdk.generation_parameters.text.chat_limits`,
and the feature list a model card reports. This guide assumes a body built the way the OpenAI SDK builds one: a
mapping with `model`, `messages` and any optional keys.

```python
from horde_sdk.generation_parameters.text import (
    ChatWorkerLimits,
    chat_request_requirements,
    chat_service_gap,
    check_chat_request_limits,
)

body = {
    "model": "koboldcpp/Example-8B",
    "messages": [{"role": "user", "content": "What is the weather in Oslo?"}],
    "tools": [{"type": "function", "function": {"name": "get_weather"}}],
    "tool_choice": "required",
    "max_tokens": 256,
}

for violation in check_chat_request_limits(body):
    print(f"{violation.param}: {violation.message}")

requirements = chat_request_requirements(body)
print(sorted(requirements.declarations))
# ['prompt_overflow_refused', 'tool_choice_enforced', 'tools']

model_card_features = ["tools", "prompt_overflow_refused", "seed"]
worker_limits = ChatWorkerLimits(max_context_length=8192, max_length=512, tools_max_temperature=1.0)
gap = chat_service_gap(requirements, model_card_features, worker_limits)
if gap is not None:
    print(gap.kind.value, gap.missing_declarations, gap.exceeded_limits)
# declaration_gap ('tool_choice_enforced',) ()
```

## Steps

1. Call `check_chat_request_limits(body)`. Each `ChatLimitViolation` holds the request path at fault (`param`) and a
   sentence. An empty result covers the limits the SDK defines; the server also applies rules that need its full
   request models, such as OpenAI's tool history rule and the structure of a strict JSON Schema.
2. Call `chat_request_requirements(body)`. It reads `horde.conformance` and defaults to `strict`. The result holds
   the capabilities (`features`), the guarantees the conformance mode needs (`guarantees`) and both together as wire
   values (`declarations`).
3. Pass the requirements, the model's declared feature list and the limits of the workers you expect to serve it to
   `chat_service_gap`. `None` means the declarations cover the request. A `ChatServiceGap` has the fields of the
   server's `impossible_reason`: `missing_declarations` and `exceeded_limits`.

## Verification

A body with a gap sent to the AI Horde waits with `is_possible` false and an `impossible_reason` that lists the same
values, as long as the online workers declare what the model card reports.

## Adjusting the request

A missing guarantee under `strict` is removed by sending `"horde": {"conformance": "best_effort"}`, which keeps the
capabilities and drops every guarantee. A missing capability needs a different model or a request that does not use
it. An exceeded `tools_max_temperature` is resolved by a lower `temperature`.

A model's feature list is the union over its workers: each value is declared by some worker, not necessarily by one
worker that declares them all. `None` from `chat_service_gap` is therefore necessary for service and not sufficient.
