---
title: "Backend normalization"
summary: "Explain why backend-native names and shapes are converted at dispatch and parsing boundaries."
topics: [architecture, backends, dispatch, generation]
order: 60
---

# Backend normalization

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [backends](../topics.md#backends), [dispatch](../topics.md#dispatch), [generation](../topics.md#generation)
<!-- END GENERATED: topics -->

Horde requests describe intent shared across workers, while inference backends expose their own sampler names, payload
shapes, defaults, and result formats. Dispatch and backend-parsing layers absorb that mismatch.

Conversion happens as close as possible to the backend. API models remain faithful to the Horde wire contract;
generation-parameter models retain backend-neutral meaning; adapters resolve backend names and required defaults only
when execution is selected.

## Costs and alternatives

Embedding backend fields in API models would remove some mapping code but would make the public API grow with every
backend and allow invalid cross-backend combinations. Passing untyped dictionaries through the worker would maximize
flexibility but defer errors until execution and make contracts hard to inspect.

Typed edge adapters add maintenance when either side changes. They provide a single place to reject unsupported values,
test exact emitted payloads, and keep backend upgrades from leaking across the package. Reverse conversion uses a
separate path because aliases and defaults are rarely invertible.

The [backend-mapper procedure](../how-to/implement-backend-mapper.md) gives the implementation steps. The planned
[dispatch interface reference](../reference/dispatch-interfaces.md) identifies the formal extension points.
