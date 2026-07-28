# Topics

Topics connect tutorials, procedures, contracts, and design explanations that concern the same subsystem.

## Vocabulary

- `alchemy`: image interrogation and post-processing requests.
- `api-models`: typed request and response objects for Horde APIs.
- `architecture`: package boundaries, abstraction layers, and extension points.
- `backends`: normalization between Horde jobs and inference backends.
- `chaining`: dependency graphs that compose worker operations.
- `clients`: synchronous, asynchronous, simple, manual, and session clients.
- `configuration`: deployment and runtime configuration contracts.
- `contributing`: repository conventions and maintenance workflows.
- `dispatch`: selecting and preparing work for a backend.
- `errors`: failure types, cleanup behavior, and troubleshooting.
- `generation`: generation parameters, requests, progress, and results.
- `images`: image generation parameters, files, and utilities.
- `model-reference`: integration with the Horde model reference.
- `ratings`: ratings API clients and models.
- `requests`: request submission, polling, responses, and cleanup.
- `safety`: content-safety and localization utilities.
- `text`: text generation requests and parameters.
- `utilities`: logging, localization, image, and support helpers.
- `workers`: worker jobs, generations, state, and lifecycle.

## By topic

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
### alchemy

- How-to: [Run an alchemy operation](how-to/run-alchemy.md)
- How-to: [Add an alchemy form](how-to/add-an-alchemy-form.md) (planned)
- Reference: [Generation parameters and features](reference/generation-parameters.md)

### api-models

- Explanation: [Typed request and response design](explanation/typed-model-design.md)
- How-to: [Add an alchemy form](how-to/add-an-alchemy-form.md) (planned)
- How-to: [Update endpoint models](how-to/update-endpoint-models.md) (planned)
- Reference: [Request and response contracts](reference/request-response-contracts.md)
- Reference: [AI Horde endpoint map](reference/endpoint-map.md)

### architecture

- Explanation: [Client layers and ownership](explanation/client-layers.md)
- Explanation: [Typed request and response design](explanation/typed-model-design.md)
- Explanation: [Generation parameters and templates](explanation/generation-parameters-and-templates.md)
- Explanation: [Worker jobs, generations, and state](explanation/worker-model.md)
- Explanation: [Package architecture](explanation/package-architecture.md)
- Explanation: [Backend normalization](explanation/backend-normalization.md)
- Explanation: [Operation chaining](explanation/chaining.md) (planned)
- Explanation: [Ratings integration](explanation/ratings-integration.md) (planned)
- Explanation: [Model-reference integration design](explanation/model-reference-integration.md) (planned)
- How-to: [Implement a backend value mapper](how-to/implement-backend-mapper.md)
- Reference: [Package and code map](reference/package-map.md)
- Reference: [SDK glossary](reference/glossary.md)
- Reference: [Contributor conventions](reference/contributor-conventions.md)

### backends

- Explanation: [Worker jobs, generations, and state](explanation/worker-model.md)
- Explanation: [Backend normalization](explanation/backend-normalization.md)
- Explanation: [Dispatch normalization](explanation/dispatch-normalization.md) (planned)
- How-to: [Implement a backend value mapper](how-to/implement-backend-mapper.md)
- How-to: [Drive the worker generation state machine](how-to/drive-worker-state.md)
- How-to: [Implement a dispatch adapter](how-to/implement-dispatch-adapter.md) (planned)
- Reference: [Worker generation transitions](reference/worker-transitions.md)
- Reference: [Backend parsing contracts](reference/backend-parsing.md) (planned)
- Reference: [Dispatch interfaces](reference/dispatch-interfaces.md) (planned)
- Tutorial: [Build your first worker integration](tutorial/first-worker.md) (planned)

### chaining

- Explanation: [Operation chaining](explanation/chaining.md) (planned)
- How-to: [Build a chained worker flow](how-to/build-chained-flow.md) (planned)
- Reference: [Chaining interfaces](reference/chaining-interfaces.md) (planned)

### clients

- Explanation: [Client layers and ownership](explanation/client-layers.md)
- How-to: [Generate images](how-to/generate-images.md)
- How-to: [Generate text](how-to/generate-text.md)
- How-to: [Use the asynchronous client](how-to/use-async-client.md)
- How-to: [Estimate request cost](how-to/estimate-cost.md)
- How-to: [Run an alchemy operation](how-to/run-alchemy.md)
- How-to: [Clean up manual requests](how-to/clean-up-manual-requests.md)
- How-to: [Use the ratings API](how-to/use-ratings-api.md) (planned)
- Reference: [Client behavior and errors](reference/client-behavior.md)
- Reference: [Troubleshooting](reference/troubleshooting.md)
- Reference: [Ratings API reference](reference/ratings-api.md) (planned)
- Tutorial: [Create and verify your first image](tutorial/first-image.md)

### configuration

- Reference: [Deployment configuration](reference/deployment-configuration.md) (planned)

### contributing

- Explanation: [Package architecture](explanation/package-architecture.md)
- How-to: [Update endpoint models](how-to/update-endpoint-models.md) (planned)
- Reference: [Package and code map](reference/package-map.md)
- Reference: [Contributor conventions](reference/contributor-conventions.md)

### dispatch

- Explanation: [Backend normalization](explanation/backend-normalization.md)
- Explanation: [Dispatch normalization](explanation/dispatch-normalization.md) (planned)
- How-to: [Drive the worker generation state machine](how-to/drive-worker-state.md)
- How-to: [Add an alchemy form](how-to/add-an-alchemy-form.md) (planned)
- How-to: [Implement a dispatch adapter](how-to/implement-dispatch-adapter.md) (planned)
- Reference: [Dispatch interfaces](reference/dispatch-interfaces.md) (planned)
- Tutorial: [Build your first worker integration](tutorial/first-worker.md) (planned)

### errors

- How-to: [Clean up manual requests](how-to/clean-up-manual-requests.md)
- Reference: [Client behavior and errors](reference/client-behavior.md)
- Reference: [Request and response contracts](reference/request-response-contracts.md)
- Reference: [Troubleshooting](reference/troubleshooting.md)
- Reference: [Logging reference](reference/logging.md) (planned)

### generation

- Explanation: [Generation parameters and templates](explanation/generation-parameters-and-templates.md)
- Explanation: [Worker jobs, generations, and state](explanation/worker-model.md)
- Explanation: [Backend normalization](explanation/backend-normalization.md)
- Explanation: [Model-reference integration design](explanation/model-reference-integration.md) (planned)
- How-to: [Generate images](how-to/generate-images.md)
- How-to: [Generate text](how-to/generate-text.md)
- How-to: [Use the asynchronous client](how-to/use-async-client.md)
- How-to: [Estimate request cost](how-to/estimate-cost.md)
- How-to: [Implement a backend value mapper](how-to/implement-backend-mapper.md)
- How-to: [Drive the worker generation state machine](how-to/drive-worker-state.md)
- Reference: [Generation parameters and features](reference/generation-parameters.md)
- Reference: [Worker generation transitions](reference/worker-transitions.md)
- Reference: [SDK glossary](reference/glossary.md)
- Reference: [Troubleshooting](reference/troubleshooting.md)
- Reference: [Backend parsing contracts](reference/backend-parsing.md) (planned)
- Reference: [Model-reference integration](reference/model-reference-integration.md) (planned)
- Tutorial: [Create and verify your first image](tutorial/first-image.md)

### images

- Explanation: [Generation parameters and templates](explanation/generation-parameters-and-templates.md)
- How-to: [Generate images](how-to/generate-images.md)
- How-to: [Use the asynchronous client](how-to/use-async-client.md)
- How-to: [Run an alchemy operation](how-to/run-alchemy.md)
- Reference: [Generation parameters and features](reference/generation-parameters.md)
- Reference: [Image utilities](reference/image-utilities.md) (planned)
- Tutorial: [Create and verify your first image](tutorial/first-image.md)

### model-reference

- Explanation: [Model-reference integration design](explanation/model-reference-integration.md) (planned)
- Reference: [Model-reference integration](reference/model-reference-integration.md) (planned)

### ratings

- Explanation: [Ratings integration](explanation/ratings-integration.md) (planned)
- How-to: [Use the ratings API](how-to/use-ratings-api.md) (planned)
- Reference: [Ratings API reference](reference/ratings-api.md) (planned)

### requests

- Explanation: [Client layers and ownership](explanation/client-layers.md)
- Explanation: [Typed request and response design](explanation/typed-model-design.md)
- How-to: [Generate images](how-to/generate-images.md)
- How-to: [Generate text](how-to/generate-text.md)
- How-to: [Use the asynchronous client](how-to/use-async-client.md)
- How-to: [Estimate request cost](how-to/estimate-cost.md)
- How-to: [Run an alchemy operation](how-to/run-alchemy.md)
- How-to: [Clean up manual requests](how-to/clean-up-manual-requests.md)
- How-to: [Update endpoint models](how-to/update-endpoint-models.md) (planned)
- How-to: [Use the ratings API](how-to/use-ratings-api.md) (planned)
- Reference: [Client behavior and errors](reference/client-behavior.md)
- Reference: [Request and response contracts](reference/request-response-contracts.md)
- Reference: [SDK glossary](reference/glossary.md)
- Reference: [AI Horde endpoint map](reference/endpoint-map.md)
- Reference: [Ratings API reference](reference/ratings-api.md) (planned)
- Tutorial: [Create and verify your first image](tutorial/first-image.md)

### safety

- Reference: [Safety and localization utilities](reference/safety-localization.md) (planned)

### text

- Explanation: [Generation parameters and templates](explanation/generation-parameters-and-templates.md)
- How-to: [Generate text](how-to/generate-text.md)
- Reference: [Generation parameters and features](reference/generation-parameters.md)

### utilities

- Reference: [Logging reference](reference/logging.md) (planned)
- Reference: [Safety and localization utilities](reference/safety-localization.md) (planned)
- Reference: [Image utilities](reference/image-utilities.md) (planned)

### workers

- Explanation: [Worker jobs, generations, and state](explanation/worker-model.md)
- Explanation: [Dispatch normalization](explanation/dispatch-normalization.md) (planned)
- Explanation: [Operation chaining](explanation/chaining.md) (planned)
- How-to: [Drive the worker generation state machine](how-to/drive-worker-state.md)
- How-to: [Implement a dispatch adapter](how-to/implement-dispatch-adapter.md) (planned)
- How-to: [Build a chained worker flow](how-to/build-chained-flow.md) (planned)
- Reference: [Worker generation transitions](reference/worker-transitions.md)
- Reference: [SDK glossary](reference/glossary.md)
- Reference: [Troubleshooting](reference/troubleshooting.md)
- Reference: [Dispatch interfaces](reference/dispatch-interfaces.md) (planned)
- Reference: [Chaining interfaces](reference/chaining-interfaces.md) (planned)
- Reference: [Deployment configuration](reference/deployment-configuration.md) (planned)
- Tutorial: [Build your first worker integration](tutorial/first-worker.md) (planned)
<!-- END GENERATED: topics -->
