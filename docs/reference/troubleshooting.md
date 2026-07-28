---
title: "Troubleshooting"
summary: "Diagnose validation, availability, timeout, cleanup, download, async-session, and backend-conversion failures."
topics: [clients, errors, generation, workers]
order: 70
---

# Troubleshooting

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [errors](../topics.md#errors), [generation](../topics.md#generation), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

Start at the boundary that produced the failure: local validation, HTTP submission, queued work, result decoding, or
worker/backend conversion. Preserve the typed exception and request or generation ID in logs.

| Symptom | Check | Action |
| --- | --- | --- |
| Pydantic validation fails | field path and constraint in the error | correct the local request; no server cleanup is needed |
| API reports no available workers | model name and request constraints | select an available model or relax optional constraints |
| Queue never completes | check response `is_possible`, wait time, queue position | use a bounded timeout; cancel or retain partial results |
| Manual request remains pending | persisted ID and whether final status ran | send the matching delete request in a `finally` path |
| Download cannot decode | generation `img` form, HTTP status, content type | retain metadata, discard invalid bytes, retry only the download when safe |
| Async session warning | ownership and context-manager lifetime | create one `aiohttp.ClientSession` and close it after Horde cleanup |
| Backend rejects a value | dispatch conversion output | add or correct the edge mapper and cover the emitted payload in tests |

## Code map

| Diagnostic area | Module | Symbol |
| --- | --- | --- |
| API exception types | `horde_sdk/ai_horde_api/exceptions.py` | `AIHordeRequestError` and peers |
| Retry behavior | `horde_sdk/generic_api/generic_clients.py` | `RequestRetryConfiguration` |
| Image validation | `horde_sdk/ai_horde_api/ai_horde_clients.py` | `download_image_from_generation` |
| Worker failures | `horde_sdk/worker/exceptions.py` | worker exception classes |

Use the [client matrix](client-behavior.md) to confirm ownership and the [endpoint map](endpoint-map.md) to confirm the
request/response pair involved.
