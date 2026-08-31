---
title: "Generate images"
summary: "Submit a typed image request, observe progress, download results, and handle a bounded timeout."
topics: [clients, generation, images, requests]
order: 10
---

# Generate images

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [generation](../topics.md#generation), [images](../topics.md#images), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Use `AIHordeAPISimpleClient` when the caller can wait synchronously and wants the SDK to own polling and cleanup. You
need a currently available model name; registered users should pass their API key instead of `ANON_API_KEY`.

## Submit a bounded request

```python
--8 < --"examples/docs/client_recipes.py:image-request"
```

Pass `timeout=300` to `image_generate_request` when your application has a five-minute upper bound. The returned status
may contain completed images even when the timeout expires, so inspect `status.generations` before treating the request
as empty.

Verify success by decoding or saving every returned image. The client raises `AIHordeRequestError` for an API error and
`AIHordeGenerationTimedOutError` when its timeout policy cannot produce a usable result; see the
[client/error matrix](../reference/client-behavior.md).

The simple client performs best-effort cancellation for unfinished follow-up requests. If your application needs to
own that lifecycle, use the [manual-request procedure](clean-up-manual-requests.md).
