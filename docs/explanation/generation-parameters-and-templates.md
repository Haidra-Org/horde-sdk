---
title: "Generation parameters and templates"
summary: "Explain why reusable generation intent is separated from API payload and backend representations."
topics: [architecture, generation, images, text]
order: 30
---

# Generation parameters and templates

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [generation](../topics.md#generation), [images](../topics.md#images), [text](../topics.md#text)
<!-- END GENERATED: topics -->

Generation intent appears in three contexts: user-facing API requests, worker pop payloads, and backend-native
execution. Horde SDK keeps a reusable parameter layer so those contexts can share meaning without sharing wire shapes.

API payload models adapt the reusable concepts to endpoint names and bounds. Worker conversion resolves defaults and
turns Horde values into backend values. Template namespaces provide a home for reusable parameter selections that do
not belong to one transport or backend.

## Tradeoffs

A single universal payload class would reduce the number of types, but it would accumulate endpoint aliases, backend
details, and fields invalid in most contexts. Separate models create explicit conversion work and more types to learn;
in return, each boundary can validate the contract it actually owns.

Optional values preserve the difference between caller intent and downstream defaults. Filling every default early
would make payloads predictable, but it would also prevent API and backend defaults from evolving independently. The
conversion boundary resolves only values it must know.

The [parameter reference](../reference/generation-parameters.md) maps the implemented families, and the
[backend normalization explanation](backend-normalization.md) covers the final conversion step.
