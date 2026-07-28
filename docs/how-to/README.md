# How-to guides

These procedures assume you know the result you need. Each guide names its preconditions, verification, and cleanup or
reversal behavior.

## Documents

<!-- BEGIN GENERATED: documents (gen_doc_index.py) -->
| Document | Summary |
| --- | --- |
| [Generate images](generate-images.md) | Submit a typed image request, observe progress, download results, and handle a bounded timeout. |
| [Generate text](generate-text.md) | Build a bounded Kobold request and retrieve the first completed text result with the simple client. |
| [Use the asynchronous client](use-async-client.md) | Share an aiohttp session with the async simple client and keep request polling off the event-loop blocking path. |
| [Estimate request cost](estimate-cost.md) | Use dry-run request variants to obtain current kudos estimates without creating generation jobs. |
| [Run an alchemy operation](run-alchemy.md) | Submit captioning or post-processing forms for a public image and inspect typed per-form results. |
| [Clean up manual requests](clean-up-manual-requests.md) | Pair submission, polling, final retrieval, and cancellation when using manual Horde clients. |
| [Implement a backend value mapper](implement-backend-mapper.md) | Normalize Horde-facing values at a backend boundary while preserving typed internal representations. |
| [Drive the worker generation state machine](drive-worker-state.md) | Advance a worker generation through preparation, execution, submission, and terminal cleanup. |

### Planned

Not yet documented in full. Each page describes its subsystem briefly and names
the code that holds the behavior.

| Document | Scope |
| --- | --- |
| [Add an alchemy form](add-an-alchemy-form.md) | Extend alchemy constants, payload validation, dispatch conversion, and typed result handling together. |
| [Update endpoint models](update-endpoint-models.md) | Change a typed endpoint contract while keeping request metadata, response pairs, tests, and reference output aligned. |
| [Implement a dispatch adapter](implement-dispatch-adapter.md) | Connect a popped Horde job to a backend-specific parameter converter and execution strategy. |
| [Build a chained worker flow](build-chained-flow.md) | Compose worker operations as a dependency graph with explicit context, edges, and execution ordering. |
| [Use the ratings API](use-ratings-api.md) | Construct ratings requests with the dedicated client and validate their typed responses. |
<!-- END GENERATED: documents -->
