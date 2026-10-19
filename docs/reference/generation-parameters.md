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

Parameter validation is covered under `tests/generation_parameters`; dispatch conversion tests verify backend-facing
representations.

## Image feature sets

`ImageGenerationFeatureFlags` is shared by generation requirements and worker support advertisements. The direction is
determined by where the model is used; field names and serialized shapes remain identical. See
[Dispatch normalization](../explanation/dispatch-normalization.md) for subset semantics, per-baseline restrictions,
lifecycle-specific extraction, generation-feature union/intersection, and complete worker-profile union.

## Chat policy

`horde_sdk.generation_parameters.text.chat_policy` holds the names a chat worker declares and a chat request is
checked against. `ChatFeature` names capabilities, such as tools or a JSON Schema constraint. `ChatGuarantee` names
places where a backend follows the OpenAI chat contract exactly instead of deviating from it, such as faulting an
overlong prompt instead of trimming it. Both share one declared list; `parse_chat_declaration` resolves a name to
either enum and returns `None` for a name this SDK release does not define.

A request's `ChatConformance` is `strict` unless it selects `best_effort`. `required_chat_guarantees` derives the
guarantees a strict request needs from its `ChatRequestTraits`; a best-effort request needs none.
`violated_chat_limit` checks `ChatWorkerLimits` that depend on request traits under either mode. Context and reply
lengths are compared by the server.
