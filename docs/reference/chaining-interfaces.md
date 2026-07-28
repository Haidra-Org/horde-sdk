---
title: "Chaining interfaces"
summary: "Specify flow graphs, contexts, nodes, edges, executors, and failure propagation."
status: stub
topics: [chaining, workers]
order: 140
---

# Chaining interfaces

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [chaining](../topics.md#chaining), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Chaining types live under `horde_sdk.worker.chaining`. Graph structure determines
dependency order; executors carry shared context and propagate terminal failures to dependent operations.
