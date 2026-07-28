---
title: "Package and code map"
summary: "Locate public clients, models, parameters, worker primitives, backend adapters, and supporting utilities."
topics: [architecture, contributing]
order: 50
---

# Package and code map

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [contributing](../topics.md#contributing)
<!-- END GENERATED: topics -->

The package separates external API contracts, reusable generation intent, worker orchestration, and backend-specific
conversion. Import from the narrowest stable package that owns the concept.

| Responsibility | Package | Primary symbols |
| --- | --- | --- |
| Root shared contracts | `horde_sdk` | status codes, generic data models, exceptions |
| AI Horde client API | `horde_sdk.ai_horde_api` | six public client/session classes |
| AI Horde wire models | `horde_sdk.ai_horde_api.apimodels` | request and response classes |
| Reusable generation intent | `horde_sdk.generation_parameters` | image, text, alchemy parameter objects |
| Generic API extension | `horde_sdk.generic_api` | request bases, clients, endpoints, decorators |
| Worker orchestration | `horde_sdk.worker` | jobs, generations, config |
| Dispatch and conversion | `horde_sdk.worker.dispatch` | pop strategies and backend conversion |
| Operation chaining | `horde_sdk.worker.chaining` | graphs, flows, nodes, edges, executors |
| Backend parsing | `horde_sdk.backend_parsing` | backend-native model normalization |
| Ratings service | `horde_sdk.ratings_api` | ratings client and models |
| Support utilities | `horde_sdk.utils`, `localize`, `safety` | image and policy helpers |

Private modules beginning with `_`, telemetry internals, scripts, and generated version files are omitted from the
published API corpus. The [Python API index](api/horde_sdk/README.md) provides symbol-level entry points.
