---
title: "Operation chaining"
summary: "Explain why worker operations are represented as dependency graphs with explicit shared context."
status: stub
topics: [architecture, chaining, workers]
order: 120
---

# Operation chaining

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [chaining](../topics.md#chaining), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Chaining models operation dependencies as a graph so ordering, reusable context, and
failure propagation are explicit. The implementation lives under `horde_sdk.worker.chaining`.
