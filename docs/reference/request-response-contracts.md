---
title: "Request and response contracts"
summary: "Specify endpoint metadata, typed validation, success-response pairing, follow-up requests, and cleanup contracts."
topics: [api-models, errors, requests]
order: 20
---

# Request and response contracts

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [api-models](../topics.md#api-models), [errors](../topics.md#errors), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Every API operation is represented by a `HordeRequest` subtype. Its class methods bind the Python model to one HTTP
method, endpoint path, payload model name, and one or more successful response types.

## Contract

- `get_api_endpoint_subpath()` returns a format string for the operation path.
- `get_http_method()` selects the HTTP verb.
- `get_success_status_response_pairs()` maps each successful status to the model used to parse it.
- `get_default_success_response_type()` supplies the normal response expected by simple convenience methods.
- Pydantic fields validate and serialize the request body, query, path, and headers according to model mixins.
- `ResponseRequiringFollowUpMixin` names poll, finalize, and failure-cleanup request types for long-lived work.

The same endpoint and status can appear under multiple verbs. Consumers must identify an operation by endpoint plus
HTTP method; the [endpoint map](endpoint-map.md) preserves that distinction.

## Code map

| Responsibility | Module | Symbol |
| --- | --- | --- |
| Base request metadata | `horde_sdk/generic_api/apimodels.py` | `HordeRequest` |
| Shared AI Horde fields | `horde_sdk/ai_horde_api/apimodels/base.py` | `BaseAIHordeRequest` |
| Image async operation | `horde_sdk/ai_horde_api/apimodels/generate/async_.py` | `ImageGenerateAsyncRequest` |
| Follow-up lifecycle | `horde_sdk/generic_api/apimodels.py` | `ResponseRequiringFollowUpMixin` |
| Request serialization | `horde_sdk/generic_api/generic_clients.py` | `GenericHordeAPIManualClient` |

`tests/ai_horde_api/test_dynamically_validate_against_swagger.py` checks SDK metadata against the live Swagger contract.
Unit tests under `tests/ai_horde_api/apimodels` cover local validation and serialization.
