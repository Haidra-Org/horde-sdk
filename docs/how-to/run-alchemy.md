---
title: "Run an alchemy operation"
summary: "Submit captioning or post-processing forms for a public image and inspect typed per-form results."
topics: [alchemy, clients, images, requests]
order: 50
---

# Run an alchemy operation

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [alchemy](../topics.md#alchemy), [clients](../topics.md#clients), [images](../topics.md#images), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

The source image must be a public HTTP(S) URL or a base64 string. Choose one or more values from
`KNOWN_ALCHEMY_TYPES`; each form produces its own state and result.

```python
--8 < --"examples/docs/client_recipes.py:alchemy-request"
```

Call `caption_image("https://example.invalid/public-image.webp")` with a real public URL. Verify that `status.forms`
contains a caption form in a completed state and that its typed result contains text.

Alchemy jobs cannot be edited after submission. The simple client cleans up an unfinished request; a manual client must
send `AlchemyDeleteRequest` with the returned generation ID. See the
[alchemy model reference](../reference/api/horde_sdk/README.md)
for the other result types.
