---
title: "Generate text"
summary: "Build a bounded Kobold request and retrieve the first completed text result with the simple client."
topics: [clients, generation, requests, text]
order: 20
---

# Generate text

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [generation](../topics.md#generation), [requests](../topics.md#requests), [text](../topics.md#text)
<!-- END GENERATED: topics -->

Choose a text model currently reported by AI Horde and decide the maximum output and context lengths before submitting
the request. The simple client polls the text status endpoint and returns typed generations.

```python
--8 < --"examples/docs/client_recipes.py:text-request"
```

Call `generate_text(model="CURRENT_MODEL_NAME")` and verify that the returned string is non-empty. A model name can
become unavailable as workers enter or leave the network; query the model-status endpoint through the generated
[API reference](../reference/api/horde_sdk/README.md) when selecting dynamically.

Reducing `max_length` reverses an unexpectedly expensive or slow configuration. A submitted request cannot be edited;
cancel it through the manual client or let the simple client's cleanup run before submitting a replacement.
