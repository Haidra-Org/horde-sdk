---
title: "SDK glossary"
summary: "Define SDK-specific terms and link broader Horde concepts to the shared Haidra vocabulary."
topics: [architecture, generation, requests, workers]
order: 60
---

# SDK glossary

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [generation](../topics.md#generation), [requests](../topics.md#requests), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

| Term | Meaning in Horde SDK |
| --- | --- |
| API model | A Pydantic object representing a request, response, or nested wire value. |
| Client session | A connection-owning client that submits individual requests and tracks follow-up cleanup. |
| Dispatch | Selection and conversion that turns popped Horde work into backend-ready parameters. |
| Dry run | An API request that returns estimated kudos without creating generation work. |
| Generation | One produced image, text, or alchemy result within a request or worker job. |
| Manual client | A client exposing individual submission, poll, status, and delete operations. |
| Parameter model | A reusable typed representation of generation intent, separate from a particular endpoint. |
| Simple client | A convenience client that owns polling, final retrieval, timeouts, and cleanup. |
| Worker job | The SDK object coordinating one popped request and its individual generations. |

The shared [Horde definitions](../haidra-assets/docs/definitions.md) cover ecosystem terms such as worker, bridge,
kudos, model, request, and job. When a shared and SDK-specific term overlap, the shared definition describes the system
concept and this page describes its Python representation.

## Code map

| Concept | Module | Symbol |
| --- | --- | --- |
| Request | `horde_sdk/generic_api/apimodels.py` | `HordeRequest` |
| Simple client | `horde_sdk/ai_horde_api/ai_horde_clients.py` | `AIHordeAPISimpleClient` |
| Worker job | `horde_sdk/worker/job_base.py` | `HordeWorkerJob` |
