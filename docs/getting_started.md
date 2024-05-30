# Getting Started

To get started, you need to install the package into your project:

``` console
pip install horde_sdk
```

<div class="note" markdown="1">
    <div class="title" markdown="1">
    Note
    </div>
    This library requires python >=3.10
</div>

## First steps

1. Choose a client for the API you wish to consume:
    - For AI Horde, this is either:
        - [AIHordeAPISimpleClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPISimpleClient] (easier, more safeties)

        - [AIHordeAPIManualClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIManualClient] (more control, manual cleanup required)

2. Find the `*Request` object type appropriate to what you want to do. (see also: [naming](getting_started.md#naming))
    - These objects types are always found in the `apimodels` namespace of the `*_api` sub package.
    - e.g., [ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncRequest]
    - **Note** that there is always one or more response types mapped to a request. You can get the default success response `type` like so:


    ```python
    >>> ImageGenerateAsyncRequest.get_success_response_type()
    <class 'horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse'>

    # Alternatively:
    >>> image_gen_request = ImageGenerateAsyncRequest( ... ) # Removed for brevity
    >>> image_gen_request.get_success_response_type()
    <class 'horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse'>
    ```
    Accordingly, the [ImageGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse] type is expected to be the return type from the API.

    <div class="warning" markdown="1">
        <div class="title" markdown="1">
        Warning
        </div>
        <a href="../horde_sdk/generic_api/apimodels/#horde_sdk.generic_api.apimodels.RequestErrorResponse"> RequestErrorResponse </a> may be also returned depending on the client you are using. Check the <a href="../horde_sdk/generic_api/apimodels/#horde_sdk.generic_api.apimodels.RequestErrorResponse.message"> RequestErrorResponse.message </a> attribute for info on the error encountered.
    </div>

3. Construct the request as appropriate:
``` python
image_generate_async_request = ImageGenerateAsyncRequest(
    apikey=ANON_API_KEY,
    prompt="A cat in a hat",
    models=["Deliberate"],
    params=ImageGenerationInputPayload(
        width=512,
        height=768,
        sampler_name=KNOWN_SAMPLERS.k_euler_a,
        clip_skip=1,
        n=2,
    ),
)
```

4. Submit the request:

    Simple Client:
    ``` python
    simple_client = AIHordeAPISimpleClient()
    status_response, job_id = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )
    # You can now download the image:
    image: PIL.Image.Image = simple_client.download_image_from_generation(status_response.generations[0])
    ```

    Manual Client:
    ``` python
    manual_client = AIHordeAPIManualClient()

    response: ImageGenerateAsyncResponse | RequestErrorResponse
    response = manual_client.submit_request(
        image_generate_async_request,
        image_generate_async_request.get_default_success_response_type(),
    )
    ```
    <div class="warning" markdown="1">
        <div class="title" markdown="1">
        Warning
        </div>
        Manual clients may leave server resources tied up if you do not implement handling. See the <a href="#important-note-about-manual-clients"> important note about manual clients </a> for more info.
    </div>



## General Notes and Guidance

### API Expectations
#### Important note about manual clients
A few endpoints, such as `/v2/generate/async` ([ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncRequest]), will have their operations live on the API server until they are retrieved or cancelled (in this case, with either a [ImageGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate._status.ImageGenerateStatusRequest] or [DeleteImageGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate._status.DeleteImageGenerateRequest]). If you use a manual client, you are assuming responsibility for making a best-effort for cleaning up errant requests, especially if your implementation crashes. If you use a simple client, you do not have to worry about this, as [context handlers][horde_sdk.generic_api.generic_clients.GenericHordeAPISession] take care of this.

### Typing

-   Under the hood, **this project is strongly typed**. Practically,
    this shouldn't leak out too much and should mostly be contained to
    validation logic.
    -   If you do find something won't work because of type issues, but
        you think it should, please [file an issue on
        github](https://github.com/Haidra-Org/horde-sdk/issues).
-   This project relies very heavily on [pydantic
    2.0](https://docs.pydantic.dev/2.0/). If you are unfamiliar with the
    concepts of pydantic, you may be served by glancing at the
    documentation for it before consuming this library.
    -   Every class from this library potentially has validation on its
        `__init__(...)` function. You should be prepared to handle
        pydantic's <span class="title-ref">ValidationError</span>
        exception as a result.
    -   Most classes from this library have a `model_dump(...)` ([see
        the
        doc](https://docs.pydantic.dev/2.0/usage/serialization/#modelmodel_dump))
        method which will return a dictionary representation of the
        object if you would rather deal with that than the object
        itself.
    -   If you have json or a compatible dict, you can use
        [model_validate](https://docs.pydantic.dev/2.0/api/main/#pydantic.main.BaseModel.model_validate)
        or
        [model_validate_json](https://docs.pydantic.dev/2.0/api/main/#pydantic.main.BaseModel.model_validate_json)


### Naming

-   Objects serializable to an API request are suffixed with `Request`.
-   Objects serializable to an API response are suffixed with
    `Response`.
-   Objects which are not meant to be instantiated are prefixed with
    `Base`.
    -   These in-between objects are typically logically-speaking parent
        classes of multiple API objects, but do not represent an actual
        API object on their own.
    -   See [horde_sdk.generic_api.apimodels][] for some of the key
        `Base*` classes.
-   Certain API models have attributes which would collide with a python
    builtin, such as `id` or `type`. In these cases, the attribute has a
    trailing underscore, as in `id_`. Ingested json still will work with
    the field <span class="title-ref">`id`</span> (its a alias).

### Faux Immutability
> 'Why can't I change this attribute?!

-   All of the \*Request and \*Response class, and many other classes,
    implement faux immutability, and their attributes are **read only**.
-   This is to prevent you from side stepping any validation.
-   See [pydantic's
    docs](https://docs.pydantic.dev/2.0/usage/validation_errors/#frozen_instance)
    for more information.
-   See also [FAQ](faq.md) for more information.
