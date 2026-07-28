---
title: "Clean up manual requests"
summary: "Pair submission, polling, final retrieval, and cancellation when using manual Horde clients."
topics: [clients, errors, requests]
order: 60
---

# Clean up manual requests

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [errors](../topics.md#errors), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Manual clients expose one HTTP exchange at a time. Use them only when your application persists the request ID and can
guarantee a cancellation attempt after partial failure.

1. Submit `ImageGenerateAsyncRequest` and require an `ImageGenerateAsyncResponse`. Persist its `id_` before polling.
2. Poll `ImageGenerateCheckRequest(id=id_)`. Verify `done`, `wait_time`, `queue_position`, and `is_possible` on every
   response before scheduling the next poll.
3. Retrieve `ImageGenerateStatusRequest(id=id_)` when the request completes. This final retrieval also releases the
   server-side request lifecycle.
4. In `finally`, submit `DeleteImageGenerateRequest(id=id_)` if final retrieval did not succeed. Treat a missing or
   already-finalized request as a successful cleanup outcome.

Use `AIHordeAPIClientSession` as a context manager when you want low-level submission with tracked best-effort cleanup.
Verify cleanup by observing a terminal status or a successful delete response. A deleted request cannot be restored;
submit a new request if the work is still required.

The [request/response contracts](../reference/request-response-contracts.md) list the corresponding text and alchemy
follow-up types.
