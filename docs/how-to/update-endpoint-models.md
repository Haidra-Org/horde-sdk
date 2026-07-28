---
title: "Update endpoint models"
summary: "Change a typed endpoint contract while keeping request metadata, response pairs, tests, and reference output aligned."
status: stub
topics: [api-models, contributing, requests]
order: 120
---

# Update endpoint models

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [api-models](../topics.md#api-models), [contributing](../topics.md#contributing), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Endpoint models implement `HordeRequest` metadata methods under
`horde_sdk.ai_horde_api.apimodels`. The Swagger parity test validates the external contract, while
`docs/build_docs.py` derives the endpoint map directly from those methods.
