# Explanation

Explanation pages connect the SDK's abstractions to the constraints they solve. Use them when you need a mental model
before choosing an extension point or debugging an interaction.

## Documents

<!-- BEGIN GENERATED: documents (gen_doc_index.py) -->
| Document | Summary |
| --- | --- |
| [Client layers and ownership](client-layers.md) | Explain why the SDK separates transport, sessions, manual operations, and simple polling clients. |
| [Typed request and response design](typed-model-design.md) | Explain how Pydantic models bind Python types, wire aliases, endpoint metadata, and compatibility behavior. |
| [Generation parameters and templates](generation-parameters-and-templates.md) | Explain why reusable generation intent is separated from API payload and backend representations. |
| [Worker jobs, generations, and state](worker-model.md) | Explain how worker jobs coordinate popped requests while generations own individual backend results. |
| [Package architecture](package-architecture.md) | Explain package boundaries from generic API contracts through AI Horde models, workers, and backend adapters. |
| [Backend normalization](backend-normalization.md) | Explain why backend-native names and shapes are converted at dispatch and parsing boundaries. |
| [Dispatch normalization](dispatch-normalization.md) | Explain how feature requirements, worker advertisements, and parameter conversion select executable work. |

### Planned

Not yet documented in full. Each page describes its subsystem briefly and names
the code that holds the behavior.

| Document | Scope |
| --- | --- |
| [Operation chaining](chaining.md) | Explain why worker operations are represented as dependency graphs with explicit shared context. |
| [Ratings integration](ratings-integration.md) | Explain the separate ratings-service boundary and how its client relates to generation results. |
| [Model-reference integration design](model-reference-integration.md) | Explain how static model metadata complements live worker availability without replacing it. |
<!-- END GENERATED: documents -->
