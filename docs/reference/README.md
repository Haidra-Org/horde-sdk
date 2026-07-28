# Reference

Reference pages specify SDK contracts and map them to Python modules and symbols. The generated API corpus is available
through the [Python API index](api/horde_sdk/README.md).

## Documents

<!-- BEGIN GENERATED: documents (gen_doc_index.py) -->
| Document | Summary |
| --- | --- |
| [Client behavior and errors](client-behavior.md) | Compare client ownership, synchronization, cleanup, return values, and failure behavior. |
| [Request and response contracts](request-response-contracts.md) | Specify endpoint metadata, typed validation, success-response pairing, follow-up requests, and cleanup contracts. |
| [Generation parameters and features](generation-parameters.md) | Map image, text, alchemy, generic, template, and versioned parameter models to their supported uses. |
| [Worker generation transitions](worker-transitions.md) | Specify generation lifecycle states, allowed progress, terminal outcomes, and job ownership. |
| [Package and code map](package-map.md) | Locate public clients, models, parameters, worker primitives, backend adapters, and supporting utilities. |
| [SDK glossary](glossary.md) | Define SDK-specific terms and link broader Horde concepts to the shared Haidra vocabulary. |
| [Troubleshooting](troubleshooting.md) | Diagnose validation, availability, timeout, cleanup, download, async-session, and backend-conversion failures. |
| [Contributor conventions](contributor-conventions.md) | Collect SDK naming, typing, model, test, documentation, and generated-file requirements. |
| [AI Horde endpoint map](endpoint-map.md) | Map each AI Horde endpoint and HTTP method to its SDK request and successful response types. |

### Planned

Not yet documented in full. Each page describes its subsystem briefly and names
the code that holds the behavior.

| Document | Scope |
| --- | --- |
| [Backend parsing contracts](backend-parsing.md) | Describe typed normalization contracts for backend-native payloads and results. |
| [Dispatch interfaces](dispatch-interfaces.md) | Specify pop strategies, dispatch parameters, adapters, and backend conversion boundaries. |
| [Chaining interfaces](chaining-interfaces.md) | Specify flow graphs, contexts, nodes, edges, executors, and failure propagation. |
| [Ratings API reference](ratings-api.md) | Specify ratings endpoints, client behavior, request models, and response models. |
| [Deployment configuration](deployment-configuration.md) | Describe the worker deployment configuration namespace and its compatibility boundary. |
| [Model-reference integration](model-reference-integration.md) | Describe the boundary between SDK requests and the external Horde model-reference package. |
| [Logging reference](logging.md) | Describe SDK logger setup, progress and completion levels, and sensitive-field handling. |
| [Safety and localization utilities](safety-localization.md) | Describe prompt-safety checks, localization helpers, and their policy boundaries. |
| [Image utilities](image-utilities.md) | Describe image encoding, decoding, resizing, and validation helpers used at API and backend boundaries. |
<!-- END GENERATED: documents -->
