
# horde_sdk Style Guide

This document covers conventions and requirements **specific to the horde_sdk codebase**. For the general Haidra Python style guide (naming, error handling, documentation, control flow, OOP, type hints, etc.), see the [Haidra Python Style Guide](../haidra-assets/docs/meta/python.md).

Everything in the shared style guide applies here. The sections below describe additional rules and conventions unique to horde_sdk.

## Table of Contents

- [horde_sdk Style Guide](#horde_sdk-style-guide)
    - [Table of Contents](#table-of-contents)
    - [Model Class Hierarchy](#model-class-hierarchy)
    - [Class Prefixes, Suffixes, and other Naming Conventions](#class-prefixes-suffixes-and-other-naming-conventions)
        - [General](#general)
        - [API/Client Specific](#apiclient-specific)
        - [API Model Specific](#api-model-specific)
        - [Generation/Inference Specific](#generationinference-specific)
    - [Request Protocol Methods](#request-protocol-methods)
    - [API Model Specific Documentation](#api-model-specific-documentation)
    - [Field Aliasing](#field-aliasing)
    - ["KNOWN" Constants](#known-constants)
    - [Validator Conventions](#validator-conventions)
    - [Pydantic BaseModel Usage (horde_sdk specifics)](#pydantic-basemodel-usage-horde_sdk-specifics)
    - [@Unhashable and @Unequatable](#unhashable-and-unequatable)
    - [API Model Verification](#api-model-verification)
    - [Test Data Conventions](#test-data-conventions)

## Model Class Hierarchy

The SDK has two separate base class branches for pydantic models. Understanding this distinction is important when adding new models.

- **`HordeAPIObject`** (ABC, not a `BaseModel`) — The abstract root for all **named** swagger models. Defines `get_api_model_name()` and `log_safe_model_dump()`. Concrete subclasses must override `get_api_model_name()`.
    - **`HordeAPIObjectBaseModel`** (`HordeAPIObject` + `BaseModel`) — The frozen pydantic base for named swagger sub-models (e.g., `ActiveModelLite`, `GenMetadataEntry`, `LorasPayloadEntry`).
    - **`HordeAPIMessage`** — Marker base for any request or response.
        - **`HordeResponse`** — Marker for any response. Adds `_time_constructed`.
            - **`HordeResponseBaseModel`** (`HordeResponse` + `BaseModel`) — Standard response model (e.g., `HordePerformanceResponse`, `UserDetailsResponse`).
            - **`HordeResponseRootModel`** (`HordeResponse` + `RootModel[T]`) — For responses that are a list at the top level (e.g., `AllCollectionsResponse`, `NewsResponse`).
        - **`HordeRequest`** (`HordeAPIMessage` + `BaseModel`) — Any request. Defines the [request protocol methods](#request-protocol-methods).
            - **`BaseAIHordeRequest`** — AI Horde-specific base (sets `get_api_url()` to the AI Horde base URL).

- **`HordeAPIData`** (`BaseModel`, frozen) — A **separate** branch for unnamed intermediate/mixin data objects. Does **not** inherit from `HordeAPIObject` and has no `get_api_model_name()` requirement. Used as the base for Mixin classes composed into concrete request/response classes via multiple inheritance (e.g., `JobRequestMixin`, `ContainsMessageResponseMixin`).

## Class Prefixes, Suffixes, and other Naming Conventions

Many classes contain standardized prefixes, suffixes, or identifiers within their names to indicate their purpose or behavior. These conventions help developers quickly understand the role of a class within the SDK.

#### General

- **Generic** (Always a Prefix): Refers to a class that is not specific to a particular API implementation. It serves as a base or abstract class that can be extended for different API clients or may be general-purpose.
    - Examples: `GenericHordeAPIManualClient`, `GenericAsyncHordeAPIManualClient`
- **Base** (Always a Prefix): Indicates a foundational class that provides core functionality and may be abstract or partially implemented. It is intended to be extended by more specific classes.
    - Examples: `BaseAIHordeClient`, `BaseAIHordeSimpleClient`

#### API/Client Specific

- **Manual**: Refers to classes that do not have context management or automatic session handling. These classes require the user to clean up server resources manually.
    - Examples: `AIHordeAPIManualClient`, `GenericHordeAPIManualClient`
- **Async**: Refers to classes that support asynchronous operations, allowing for non-blocking API calls and improved performance in concurrent environments. Generally, these classes will use `async` method definitions but may support synchronous operations as well.
    - Examples: `AIHordeAPIAsyncManualClient`, `GenericAsyncHordeAPIManualClient`
- **HordeAPI**: Indicates a class that is specifically designed for a Horde-style API. This *does not* imply that the class is specific to the AI Horde API, but rather that it is designed to work with any API that follows the Horde-style conventions.
    - Examples: `GenericHordeAPIManualClient`, `GenericAsyncHordeAPIManualClient`
- **AIHorde**: Refers to classes that are specifically designed for the AI Horde API. These classes are tailored to the specific requirements and features of the AI Horde API.
    - Examples: `AIHordeAPIManualClient`, `AIHordeAPIAsyncManualClient`
- **Simple**: Refers to high-level client classes that provide the easiest API for common operations. These are a distinct tier above Manual and Session — they manage sessions internally and expose simplified methods for common workflows.
    - Examples: `AIHordeAPISimpleClient`, `AIHordeAPIAsyncSimpleClient`, `BaseAIHordeSimpleClient`
- **Session** (Always a suffix): Indicates a class that manages a session with the API, handling authentication, connection management, and request/response handling. These classes should provide context management support (i.e., they should implement the `__enter__` and `__exit__` or `__aenter__` and `__aexit__` methods) to ensure proper cleanup of resources.
    - Examples: `GenericHordeAPISession`, `GenericAsyncHordeAPISession`

#### API Model Specific

- **Mixin** (Always a suffix): Refers to composition classes that add fields or behaviors to concrete request/response models via multiple inheritance. Mixin classes inherit from `HordeAPIData` (not `HordeAPIObject`) and do not stand alone as API models.
    - Examples: `ContainsMessageResponseMixin`, `APIKeyAllowedInRequestMixin`, `JobRequestMixin`, `ImageGenerateParamMixin`, `ResponseRequiringFollowUpMixin`
- **Request**/**Response** (Always a suffix): Indicates a concrete API request or response class. These are commonly prefixed with an **operation indicator**:
    - **Delete**: `DeleteTeamRequest`
    - **Modify**: `ModifyUserRequest`, `ModifyUserResponse`
    - **Create**: `CreateTeamRequest`
    - **All**: `AllCollectionsResponse`, `AllTeamDetailsResponse` (collection of all items)
    - **Single**: `SingleUserDetailsRequest` (one specific item)
    - **Find**: `FindUserRequest` (search/lookup)
- **Entry** (Always a suffix): Refers to sub-objects within payloads or parameters — individual items in a list or repeated structure.
    - Examples: `LoRaEntry`, `TIEntry`, `AuxModelEntry`, `ExtraSourceImageEntry`, `ExtraTextEntry`
- **Lite** (Always a suffix): Indicates a lightweight or summary version of a more detailed model, typically returned in list endpoints.
    - Examples: `ActiveModelLite`, `TeamDetailsLite`, `WorkerDetailLite`
- **Payload**: Indicates a data payload sent to or received from the API, typically as the body of a request or a nested structure within a response.
    - Examples: `ImageGenerationInputPayload`, `ModelPayloadKobold`, `AlchemyFormPayloadStable`

#### Generation/Inference Specific

- **FeatureFlags**: Refers to classes which describe what features are required by a generation *or* what features are supported by a worker/backend.
    - Example: `ImageGenerationFeatureFlags`
- **GenerationParameters**/**Parameters**: Refers to classes which describe the parameters required for a generation request.
    - Example: `ImageGenerationParameters`
- **ParametersTemplate**: Refers to classes which describe the parameters required for a generation request, but have the property that **all fields are optional**. These classes are intended to be used as templates during the construction of certain other feature, such as user styles and chaining.
    - Example: `ImageGenerationParametersTemplate`
- **Basic**: Classes which have the parameters shared across all (or virtually all) generation requests of that kind. Images, for example, universally have a width and height, so `BasicImageGenerationParameters` would be a class that contains those fields.
    - Example: `BasicImageGenerationParameters`
- **KNOWN_**: `Enums` or `StrEnums` which describe a set of known values for a particular field or parameter. These are intended to be used as a way to validate input and provide a clear set of options for consumers. However, by convention, these are not *required* to be used, and consumers are free to use any valid value for the field or parameter as long as its type is correct.
    - Example: `KNOWN_IMAGE_SAMPLERS`, `KNOWN_AUX_MODEL_SOURCE`

## Request Protocol Methods

Every concrete `HordeRequest` subclass must implement the following methods, each with `@override`:

- **`get_http_method()`** — Returns the `HTTPMethod` enum value (GET, POST, PUT, DELETE, PATCH).
- **`get_api_endpoint_subpath()`** — Returns the `AI_HORDE_API_ENDPOINT_SUBPATH` enum value identifying the URL path.
- **`get_default_success_response_type()`** — Returns the primary response class for this request.
- **`get_api_model_name()`** — Returns the swagger model name for the request payload, `None` for GET requests without payloads, `_ANONYMOUS_MODEL` for unnamed models, or `_OVERLOADED_MODEL` for conflicting representations.
- **`get_success_status_response_pairs()`** — Maps HTTP status codes to response types. The default returns `{HTTPStatusCode.OK: cls.get_default_success_response_type()}`. Override when an endpoint returns different models for different status codes:

    ```python
    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponse]]:
        return {
            HTTPStatusCode.OK: ImageGenerateAsyncDryRunResponse,
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }
    ```

## API Model Specific Documentation

Many docstrings in the SDK have additional requirements when they are related to API models or requests/responses. While these rules would be difficult to remember, they are luckily enforced by CI and the `horde_sdk.meta` module has helper functions to assist in generating the required docstrings. The correct docstrings will also be emitted by the `object_verify` tests. Be sure to run the tests with `-s` to see the output.

- Children classes of `HordeAPIObject`, `HordeAPIData` which have a named model described in the API docs must have a docstring whose final line looks like this (for a model with the name `HordePerformance` on the v2 API):

    ```python
        """...

        v2 API Model: `HordePerformance`
        """
    ```

    Where `HordePerformance` is the name of the model as described in the API docs. It must be followed by a carriage return.

- Children classes of `HordeResponse` must have additional specific information, for example:

    When the response is returned from **one** endpoint:

    ```python
        class HordePerformanceResponse(HordeResponseBaseModel):
        """Information about the performance of the horde, such as worker counts and queue sizes.

        Represents the data returned from the /v2/status/performance endpoint with http status code 200.

        v2 API Model: `HordePerformance`
        """
    ```

    Where `/v2/status/performance` is the endpoint that returns the performance information. This must match the corresponding request class's `get_api_endpoint_subpath()` and `get_success_status_response_pairs()` values.

    When the response can be returned from **multiple** endpoints:

    ```python
    class ResponseModelCollection(HordeResponseBaseModel):
    """A collection of styles.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/collection_by_name/{collection_name} | CollectionByNameRequest [GET] -> 200
        - /v2/collections/{collection_id} | CollectionByIDRequest [GET] -> 200

    v2 API Model: `ResponseModelCollection`
    """
    ```

    Where `/v2/collection_by_name/{collection_name}` and `/v2/collections/{collection_id}` are the endpoints that return the collection information. This must match the corresponding all of the requesting class's `get_api_endpoint_subpath()` and `get_success_status_response_pairs()` values.

- Children classes of `HordeRequest` must have additional specific information. The format is `Represents a {METHOD} request to the {endpoint} endpoint.` All HTTP methods (GET, POST, PUT, DELETE, PATCH) follow the same template. For example:

    ```python
        class HordePerformanceRequest(BaseAIHordeRequest):
        """Request performance information about the horde, such as worker counts and queue sizes.

        Represents a GET request to the /v2/status/performance endpoint.
        """
    ```

    ```python
        class ImageGenerateAsyncRequest(BaseAIHordeRequest):
        """Submit an asynchronous image generation request.

        Represents a POST request to the /v2/generate/async endpoint.

        v2 API Model: `GenerationInputStable`
        """
    ```

- If the API does not name the model, `get_api_model_name(...)` must be overloaded to return `horde_sdk.consts._ANONYMOUS_MODEL` and the docstring should be:

    ```python
        """...

        v2 API Model: `_ANONYMOUS_MODEL`
        """
    ```

- If the model has is overloaded (has two or more conflicting representations), `get_api_model_name(...)` must be overloaded to return `horde_sdk.consts._OVERLOADED_MODEL` and the docstring should be:

    ```python
        """...

        v2 API Model: `_OVERLOADED_MODEL`
        """
    ```

## Field Aliasing

When an API field name conflicts with a Python builtin, the Python attribute should use a trailing underscore and a `Field(alias=...)` to map to the API name:

```python
    # "id" conflicts with the Python builtin id()
    id_: str = Field(alias="id")

    # "type" conflicts with the Python builtin type()
    type_: str = Field(alias="type")
```

For fields that have been renamed across API versions, `AliasChoices` can be used to accept multiple names:

```python
    steps: int = Field(alias=AliasChoices("steps", "ddim_steps"))
```

## "KNOWN" Constants

- For consumer convenience, parameters which have a fixed set of known values should be defined as constants in an appropriate `consts.py` file. These constants should be named with the `KNOWN_` prefix and should be defined as `StrEnum`s or `Enum`s as appropriate.
- However, these values should **always be considered optional**. Consumers of the SDK should be able to use any valid value for the parameter as long as its type is correct. It would be ideal, but not required, that classes or functions which require these parameters validate them against the live API at runtime.
    - ***Rationale***: This prevents the SDK from needing to be updated every time a new value is added to an API, and allows consumers to use any valid value without needing to wait for an SDK update.

## Validator Conventions

When validators check a field value against a `KNOWN_` enum, they must **log a warning but never reject unknown values**. This ensures forward-compatibility — the SDK will still work if the API adds new values before the SDK is updated.

```python
    @field_validator("sampler_name")
    @classmethod
    def sampler_must_be_known(cls, v: str) -> str:
        if v not in KNOWN_IMAGE_SAMPLERS.__members__:
            logger.warning(f"Unknown sampler {v}. Is your SDK out of date?")
        return v
```

This principle is the behavioral complement to the ["KNOWN" Constants](#known-constants) convention.

## Pydantic BaseModel Usage (horde_sdk specifics)

In addition to the [shared Pydantic guidelines](../haidra-assets/docs/meta/python.md#pydantic-basemodel-usage), horde_sdk has the following additional requirements:

- `BaseModel` derived classes used as API responses or members of an API response should be frozen. Additionally, classes meant to represent data set by a client, server, or worker should also be frozen.
    - **Important**: This is not a blanket requirement for all `BaseModel` derived classes. Consider carefully how likely it would that a consumer would want to modify the data in the model and if doing so would have unintended consequences difficult for consumers to understand.
    - ***Rationale***: Classes of this kind being frozen reflects the fact that they are not meant to be modified after creation. Workers receiving jobs from the server (and specified by the client) should never need to modify that job data. Raising errors in the case a worker attempts to modify job data prevents accidental modification and prevents a category of bugs.
    - This is done by setting the field `model_config` to an instance of a `ConfigDict`.
        - See `get_default_frozen_model_config_dict()` (defined in `horde_sdk.consts`, re-exported from `horde_sdk.__init__`) for the default frozen model config.
            - This function should be used whenever possible to set the `model_config` field.
            - Using this function ensures that the model config is consistent across the codebase.
            - Further, the CI/Testing relies on using this function to ensure that the models are frozen in tests.
            - If you set your own `model_config`, you must ensure that it is consistent with the behavior of `get_default_frozen_model_config_dict()`.
        - **Dual-mode behavior**: `get_default_frozen_model_config_dict()` returns different configs depending on the environment:
            - **Production** (`TESTS_ONGOING` not set): `extra="allow"` — permits unknown fields for API forward-compatibility (new API fields won't break existing SDK versions).
            - **Tests** (`TESTS_ONGOING` set): `extra="forbid"` — rejects unexpected fields, catching model definition errors early.
            - Both modes set `frozen=True`, `use_attribute_docstrings=True`, and `from_attributes=True`.
- Values should never be coerced to `None` for optional fields when passed a non-`None` value.
    - ***Rationale***: If an invalid value is passed to a field, it should be raised as an error. This is especially important when implementing a "Template" class (which all fields are optional) - if a child class overrides a field to be non-optional but the parent class is coercing it to `None`, this can cause bugs or run-time errors.
- A good example of judicious `Any` usage in the SDK is type hinting `HordeSingleGeneration[Any]`, where the generic parameter represents the resulting types from the generation (e.g., `str` for text, `bytes` for images, etc.). This pattern allows accurately typing `HordeSingleGeneration` when working with arbitrary generations in contexts where the resulting type is not important, for example, in high-level generic worker classes.

## @Unhashable and @Unequatable

`@Unhashable` and `@Unequatable` (from `horde_sdk.generic_api.decoration`) are decorators used on models that contain unhashable fields (e.g., `list`, `dict`) or where field-by-field equality is meaningless. These two decorators must **always be applied together as a pair** — there are no cases where one is used without the other.

```python
    @Unhashable
    @Unequatable
    class AllCollectionsResponse(HordeResponseRootModel):
        ...
```

CI verifies that all request/response types are hashable and equatable unless explicitly marked with these decorators.

## API Model Verification

These rules are specific to (remote) API models (for example, any class in an `apimodels` namespace).

1. **All `HordeAPIObject` and `HordeAPIData` sub-classes must be imported** in their appropriate apimodels `__init__.py` files so that they match the live API surface.
    - For example, all AI Horde API models must be imported into `horde_sdk.ai_horde_api/apimodels/__init__.py`.
    - ***Rationale***: This ensures that the SDK's API surface matches the live API surface and that all models are properly documented and tested. The testing relies on these imports to function correctly. Further, this ensures that all models are appropriately exposed for consumers of the SDK.
2. **Any model in the API docs** must be defined in the SDK. Unreferenced or missing models will cause a test failure.
3. **All endpoints in the API docs** must be handled or marked as ignored (e.g., admin-only or deprecated). Unknown or unaddressed endpoints raise errors during testing.
4. **All models must have docstrings** conforming to the style documented above. If they do not, these tests will fail and suggest required changes.
5. **All models (including requests and responses) must be instantiable from example JSON** found in the test data directories. If instantiation fails, the test will provide details on what's wrong.
6. **All request/response types must be hashable** if they aren't explicitly marked as unhashable (`@Unhashable`), which ensures they can be properly used in collections.
7. **All request/response types must be equatable** if they aren't explicitly marked as unequatable (`@Unequatable`), which ensures they can be properly compared in tests.
8. **Example payloads, response data, and production responses** must be valid according to their corresponding model validation rules, ensuring that the models accurately represent real-world data.

## Test Data Conventions

Test data lives under `tests/test_data/ai_horde_api/` with the following structure:

```
test_data/ai_horde_api/
├── swagger.json                              # Full swagger spec from the live API
├── example_payloads/                          # POST/PUT/PATCH request bodies
│   └── _v2_generate_async_post.json
├── example_responses/                         # Response bodies per endpoint + status
│   └── _v2_generate_async_post_202.json
├── example_production_responses/              # Real-world responses captured from production
│   └── _v2_workers_get_200.json
└── production_responses/                      # Additional production data
```

**File naming convention**: `_{endpoint_path}_{http_method}[_{status_code}].json`

- Slashes become underscores: `/v2/generate/async` → `_v2_generate_async`
- Payloads include the method: `_v2_generate_async_post.json`
- Responses include the method and status code: `_v2_generate_async_post_202.json`
- Path parameters are kept descriptive: `{collection_id}` → `collection_id`

Every API endpoint must have corresponding test JSON files. CI validates that all models can be instantiated from these example files (see rule 5 above).
