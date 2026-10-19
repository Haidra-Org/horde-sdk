---
title: "Use the asynchronous client"
summary: "Share an aiohttp session with the async simple client and keep request polling off the event-loop blocking path."
topics: [clients, generation, images, requests]
order: 30
---

# Use the asynchronous client

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [generation](../topics.md#generation), [images](../topics.md#images), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Use the async client inside an existing `asyncio` application. The caller owns the `aiohttp.ClientSession`; closing it
is the observable end of its connection pool and must happen after all Horde calls finish.

```python
--8 < --"examples/docs/client_recipes.py:async-request"
```

Verify that the coroutine returns non-empty bytes and that no unclosed-session warning appears. For multiple requests,
create one session outside the individual coroutine calls and pass the same session to each client.

Cancellation propagates through the awaiting task. Keep the client/session context alive until cleanup completes; if
you require explicit cancellation control, use `AIHordeAPIAsyncManualClient` and the same lifecycle described in
[clean up manual requests](clean-up-manual-requests.md).
