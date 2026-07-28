---
title: "Implement a dispatch adapter"
summary: "Connect a popped Horde job to a backend-specific parameter converter and execution strategy."
status: stub
topics: [backends, dispatch, workers]
order: 130
---

# Implement a dispatch adapter

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [backends](../topics.md#backends), [dispatch](../topics.md#dispatch), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Dispatch interfaces live in `horde_sdk.worker.dispatch.base` and pop strategies in
`horde_sdk.worker.dispatch.pop_strategy`. AI Horde implementations demonstrate how typed pop responses become backend
parameters without leaking backend values into API models.
