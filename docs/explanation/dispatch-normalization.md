---
title: "Dispatch normalization"
summary: "Explain how pop strategies, capability checks, and parameter conversion select executable worker jobs."
status: stub
topics: [backends, dispatch, workers]
order: 110
---

# Dispatch normalization

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [backends](../topics.md#backends), [dispatch](../topics.md#dispatch), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Dispatch selects compatible popped work, records why a job is skipped, and converts
accepted parameters at the backend edge. Implementations live under `horde_sdk.worker.dispatch`.
