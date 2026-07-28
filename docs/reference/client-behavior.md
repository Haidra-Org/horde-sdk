---
title: "Client behavior and errors"
summary: "Compare client ownership, synchronization, cleanup, return values, and failure behavior."
topics: [clients, errors, requests]
order: 10
---

# Client behavior and errors

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [errors](../topics.md#errors), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Choose the highest-level client that still exposes the control your application needs. Simple clients own polling;
manual clients expose one request at a time; session clients add connection reuse and tracked cleanup.

## Selection matrix

| Client | Execution | Owns polling | Tracks cleanup | Typical use |
| --- | --- | --- | --- | --- |
| `AIHordeAPISimpleClient` | synchronous | yes | yes | scripts and blocking services |
| `AIHordeAPIAsyncSimpleClient` | asynchronous | yes | yes | event-loop applications |
| `AIHordeAPIManualClient` | synchronous | no | no | persisted workflow engines |
| `AIHordeAPIAsyncManualClient` | asynchronous | no | no | async workflow engines |
| `AIHordeAPIClientSession` | synchronous | no | yes | repeated low-level calls |
| `AIHordeAPIAsyncClientSession` | asynchronous | no | yes | repeated async low-level calls |

Simple generation methods return `(status_response, generation_id)`. Async image download returns
`(PIL.Image.Image, generation_id)`; synchronous image download returns the image.

## Error contract

| Failure | Surface | Caller action |
| --- | --- | --- |
| Local model validation | Pydantic `ValidationError` | correct the request before retrying |
| Typed API error response | `AIHordeRequestError` | inspect its response and retry only when the API condition permits |
| Server protocol failure | `AIHordeServerException` | log endpoint/status and apply bounded retry policy |
| Generation exceeds policy | `AIHordeGenerationTimedOutError` | inspect partial results, then cancel or resubmit |
| Invalid image data | `AIHordeImageValidationError` | discard the result and retain generation metadata for diagnosis |

## Code map

| Responsibility | Module | Symbol |
| --- | --- | --- |
| AI Horde clients | `horde_sdk/ai_horde_api/ai_horde_clients.py` | `AIHordeAPISimpleClient` and peers |
| Generic HTTP behavior | `horde_sdk/generic_api/generic_clients.py` | `GenericHordeAPIManualClient` |
| API failures | `horde_sdk/ai_horde_api/exceptions.py` | `AIHordeRequestError` |
| Request cleanup contract | `horde_sdk/generic_api/apimodels.py` | `ResponseRequiringFollowUpMixin` |

Client behavior is exercised under `tests/ai_horde_api` and `tests/generic_api`. The dedicated facade pages in the
[Python API index](api/horde_sdk/README.md) expand inherited methods for the six public client classes.
