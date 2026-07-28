---
title: "Model-reference integration design"
summary: "Explain how static model metadata complements live worker availability without replacing it."
status: stub
topics: [architecture, generation, model-reference]
order: 140
---

# Model-reference integration design

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [generation](../topics.md#generation), [model-reference](../topics.md#model-reference)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Static model records supply known metadata and naming; live AI Horde endpoints report
which models workers currently serve. SDK selection logic must keep those two sources distinct.
