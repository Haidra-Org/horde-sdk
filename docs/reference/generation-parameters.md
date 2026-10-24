---
title: "Generation parameters and features"
summary: "Map image, text, alchemy, generic, template, and versioned parameter models to their supported uses."
topics: [alchemy, generation, images, text]
order: 30
---

# Generation parameters and features

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [alchemy](../topics.md#alchemy), [generation](../topics.md#generation), [images](../topics.md#images), [text](../topics.md#text)
<!-- END GENERATED: topics -->

Generation-parameter models describe reusable settings independently of a particular API request. API payload models
compose or adapt them where the wire contract requires different names or bounds.

## Families

| Family | Module | Carries |
| --- | --- | --- |
| Generic | `horde_sdk.generation_parameters.generic` | shared generation concepts and constants |
| Image | `horde_sdk.generation_parameters.image` | dimensions, sampling, source processing, LoRAs, control, hires fix |
| Text | `horde_sdk.generation_parameters.text` | context length, output length, sampling, repetition controls |
| Alchemy | `horde_sdk.generation_parameters.alchemy` | form names, upscalers, annotations, caption/interrogation types |
| Versioning | `horde_sdk.generation_parameters.versioning` | compatibility metadata for evolving parameter sets |
| Templates | `horde_sdk.generation_parameters.templates` | package boundary reserved for reusable parameter templates |

`None` generally means the caller leaves selection to the API or backend; an explicit value requests a behavior. Check
the field's Pydantic bounds and docstring because zero, empty collections, and omission are not interchangeable.

## Code map

| Responsibility | Module | Symbol |
| --- | --- | --- |
| Image object model | `horde_sdk/generation_parameters/image/object_models.py` | `ImageGenerationParameters` |
| Image API payload | `horde_sdk/ai_horde_api/apimodels/generate/async_.py` | `ImageGenerationInputPayload` |
| Text API payload | `horde_sdk/ai_horde_api/apimodels/generate/text/async_.py` | `ModelGenerationInputKobold` |
| Alchemy names | `horde_sdk/generation_parameters/alchemy/consts.py` | `KNOWN_ALCHEMY_TYPES` |
| Chat policy | `horde_sdk/generation_parameters/text/chat_policy.py` | `required_chat_guarantees` |
| Chat limits | `horde_sdk/generation_parameters/text/chat_limits.py` | `check_chat_request_limits` |
| Chat worker builders | `horde_sdk/worker/chat_declaration.py` | `declare_from_backend` |

Parameter validation is covered under `tests/generation_parameters`; dispatch conversion tests verify backend-facing
representations.

## Image feature sets

`ImageGenerationFeatureFlags` is shared by generation requirements and worker support advertisements. The direction is
determined by where the model is used; field names and serialized shapes remain identical. See
[Dispatch normalization](../explanation/dispatch-normalization.md) for subset semantics, per-baseline restrictions,
lifecycle-specific extraction, generation-feature union/intersection, and complete worker-profile union.

## Chat policy

`horde_sdk.generation_parameters.text.chat_policy` holds the values a chat worker declares and a chat request is
checked against. `ChatFeature` lists capabilities, such as tools, a JSON Schema constraint, or serving tools and a
response format in one request (`tools_with_response_format`, the format applying to the final text answer and not
to tool calls). `ChatGuarantee` lists places where a backend follows the OpenAI chat contract exactly instead of
deviating from it, such as faulting an overlong prompt instead of trimming it. Both share one declared list,
`KNOWN_CHAT_DECLARATIONS`; `parse_chat_declaration` resolves a declared value to either enum and returns `None` for a
value this SDK release does not define. The vocabulary grows by adding values; a value never changes meaning.

`ChatReasoningEffort` holds OpenAI's `reasoning_effort` values, `none` through `xhigh`. A request that sets any of
them, `none` included, needs the `reasoning_effort` capability, and the server forwards the value to the worker
unchanged.

A request's `ChatConformance` is `strict` unless it selects `best_effort`. `required_chat_guarantees` derives the
guarantees a strict request needs from its `ChatRequestTraits`; a best-effort request needs none.
`violated_chat_limit` checks the `ChatWorkerLimits` that depend on request traits under either mode and returns the
`ChatLimitField` at fault. Context and reply lengths are compared by the server.

### Client helpers

These functions take an OpenAI chat completions request body as a mapping, as a client builds it. See
[Check a chat request before sending it](../how-to/check-chat-request.md).

| Function | Returns |
| --- | --- |
| `chat_request_traits(body)` | `ChatRequestTraits` after OpenAI's defaults: tool choice `auto`, parallel tool calls true, temperature 1 |
| `chat_request_conformance(body)` | The `horde.conformance` mode, `strict` when absent |
| `chat_request_requirements(body)` | `ChatRequirements`: capabilities, guarantees under the conformance mode, the mode and the traits |
| `chat_service_gap(requirements, declared, limits)` | `ChatServiceGap` with `missing_declarations` and `exceeded_limits`, or `None` |
| `check_chat_request_limits(body)` | A `ChatLimitViolation` (`param`, `message`) per exceeded limit below |

`ChatServiceGap` has the fields of the server's chat status `impossible_reason`. The server also lists
`image_transports` for a worker that declares `vision` without an image transport; a feature list carries no
transports, so the client check does not.

### Shared limits and defaults

`horde_sdk.generation_parameters.text.chat_limits` defines the request-side values of the AI Horde chat route. The
server imports them, so a client checks against the values the server applies.

| Constant | Value | Bounds |
| --- | --- | --- |
| `MAX_CHAT_TOOL_COUNT` | 128 | Tools one request defines |
| `MAX_CHAT_TOOL_SPEC_BYTES` | 256 KiB | Compact JSON of `tools`, `tool_choice` and `response_format` together |
| `MAX_CHAT_TEXT_BYTES` | 1 MiB | UTF-8 message text, with tool call names and arguments in the history |
| `MAX_CHAT_SCHEMA_NESTING` | 10 | Levels below the root of a tool `parameters` or `response_format` schema |
| `MIN_CHAT_MAX_TOKENS`, `MAX_CHAT_MAX_TOKENS` | 16, 4096 | `max_tokens` and `max_completion_tokens` |
| `OPENAI_MIN_MAX_TOKENS` | 1 | The smallest token limit OpenAI accepts |
| `MAX_CHAT_STOP_SEQUENCES` | 4 | Entries of a `stop` list |
| `OPENAI_SAMPLING_RANGES` | 0 to 2, 0 to 1, -2 to 2 | `temperature`; `top_p`; both penalties |
| `SUPPORTED_CHAT_CHOICE_COUNT` | 1 | `n` |
| `CHAT_SAMPLING_DEFAULTS` | OpenAI's defaults | Sampling values a chat job carries when the client sets none |
| `DEFAULT_PARALLEL_TOOL_CALLS` | true | `parallel_tool_calls` when tools are offered without it |

`chat_schema_exceeds_nesting` applies the nesting limit to one schema.

### Worker builders

`horde_sdk.worker.chat_declaration` builds the chat fields of a text pop (`ChatWorkerDeclaration.to_pop_fields`),
maps backend facts to the declarations they back (`ChatBackendFacts`, `declare_from_backend`, `ChatToolStrategy`),
reads a popped chat job (`ChatJobPayload.from_pop`) and builds submit bodies (`build_chat_reply_submit`,
`build_chat_fault_submit`) with `ChatFinishReason`, `ChatFaultReason` and `ChatImageTransport`. See
[Declare and serve chat jobs from a worker](../how-to/serve-chat-jobs.md).
