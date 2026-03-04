# Getting Started

To get started, install the package into your project:

``` console
pip install horde_sdk
```

<div class="note" markdown="1">
    <div class="title" markdown="1">
    Note
    </div>
    This library requires python >=3.12
</div>

## Choosing a Client

The SDK provides several client classes depending on your needs:

| Client | Sync/Async | Description |
|--------|-----------|-------------|
| [AIHordeAPISimpleClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPISimpleClient] | Sync | Easiest to use; handles polling and cleanup automatically |
| [AIHordeAPIAsyncSimpleClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncSimpleClient] | Async | Same ease of use, with `asyncio` support |
| [AIHordeAPIManualClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIManualClient] | Sync | More control; you manage polling and cleanup |
| [AIHordeAPIAsyncManualClient][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncManualClient] | Async | More control, with `asyncio` support |
| [AIHordeAPIClientSession][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIClientSession] | Sync | Context manager that auto-cleans up pending requests on exit |
| [AIHordeAPIAsyncClientSession][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncClientSession] | Async | Async context manager that auto-cleans up pending requests on exit |

For most use cases, start with `AIHordeAPISimpleClient` (sync) or `AIHordeAPIAsyncSimpleClient` (async).

## Image Generation

### Simple Client (Sync)

``` python
from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS

simple_client = AIHordeAPISimpleClient()

status_response, gen_id = simple_client.image_generate_request(
    ImageGenerateAsyncRequest(
        apikey=ANON_API_KEY,
        prompt="A cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            width=512,
            height=512,
            sampler_name=KNOWN_IMAGE_SAMPLERS.k_euler,
        ),
    ),
)

for generation in status_response.generations:
    image = simple_client.download_image_from_generation(generation)
    image.save(f"{generation.id_}.webp")
```

<div class="note" markdown="1">
    <div class="title" markdown="1">
    Note
    </div>
    The `apikey` parameter defaults to `ANON_API_KEY` if omitted. You only need to pass it explicitly if you have a registered API key.
</div>

### Simple Client (Async)

``` python
import aiohttp
from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncSimpleClient,
)
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)

async def generate_image() -> None:
    aiohttp_session = aiohttp.ClientSession()
    horde_client_session = AIHordeAPIAsyncClientSession(aiohttp_session)

    async with aiohttp_session, horde_client_session:
        simple_client = AIHordeAPIAsyncSimpleClient(
            horde_client_session=horde_client_session,
        )

        status_response, gen_id = await simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                apikey=ANON_API_KEY,
                prompt="A cat in a hat",
                models=["Deliberate"],
                params=ImageGenerationInputPayload(
                    height=512,
                    width=512,
                    n=2,
                ),
            ),
        )

        for generation in status_response.generations:
            image, image_gen_id = await simple_client.download_image_from_generation(generation)
            image.save(f"{image_gen_id}.webp")
```

### Manual Client

The manual client gives you direct control over the request/response cycle. You submit the initial async request, poll for status yourself, and retrieve results when ready.

``` python
import time
from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api import AIHordeAPIManualClient, download_image_from_generation
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
)

manual_client = AIHordeAPIManualClient()

image_generate_async_request = ImageGenerateAsyncRequest(
    apikey=ANON_API_KEY,
    prompt="A cat in a hat",
    models=["Deliberate"],
)

response: ImageGenerateAsyncResponse | RequestErrorResponse
response = manual_client.submit_request(
    image_generate_async_request,
    image_generate_async_request.get_default_success_response_type(),
)

if isinstance(response, RequestErrorResponse):
    raise RuntimeError(f"Error: {response.message}")

# Poll until the generation is done.
while True:
    check = manual_client.get_generate_check(gen_id=response.id_)
    if check.done:
        break
    time.sleep(5)

# Retrieve the finished images.
status = manual_client.get_generate_status(gen_id=response.id_)
for generation in status.generations:
    image = download_image_from_generation(generation)
    image.save(f"{generation.id_}.webp")
```

<div class="warning" markdown="1">
    <div class="title" markdown="1">
    Warning
    </div>
    Manual clients may leave server resources tied up if you do not implement handling. See the <a href="#important-note-about-manual-clients"> important note about manual clients </a> for more info.
</div>

### Dry Runs

You can check the kudos cost of a request without actually generating images:

``` python
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)

simple_client = AIHordeAPISimpleClient()

dry_run_response = simple_client.image_generate_request_dry_run(
    ImageGenerateAsyncRequest(
        prompt="A cat in a hat",
        params=ImageGenerationInputPayload(
            height=832,
            width=832,
        ),
        models=["Deliberate"],
        dry_run=True,
    ),
)

print(f"Estimated kudos cost: {dry_run_response.kudos}")
```

## Text Generation

``` python
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ModelGenerationInputKobold,
    TextGenerateAsyncRequest,
)

simple_client = AIHordeAPISimpleClient()

status_response, gen_id = simple_client.text_generate_request(
    TextGenerateAsyncRequest(
        prompt="Once upon a time",
        models=["koboldcpp/LLaMA2-13B-Psyfighter2"],
        params=ModelGenerationInputKobold(
            max_context_length=1024,
            max_length=80,
        ),
    ),
)

for generation in status_response.generations:
    print(generation.text)
```

## Alchemy (Image Post-Processing)

Alchemy lets you run operations like captioning and upscaling on existing images:

``` python
import asyncio
import base64
from pathlib import Path

import aiohttp
from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncSimpleClient,
)
from horde_sdk.ai_horde_api.apimodels import (
    AlchemyAsyncRequest,
    AlchemyAsyncRequestFormItem,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES

async def alchemy_example() -> None:
    source_image_base64 = base64.b64encode(Path("my_image.webp").read_bytes()).decode()

    aiohttp_session = aiohttp.ClientSession()
    horde_client_session = AIHordeAPIAsyncClientSession(aiohttp_session)
    async with aiohttp_session, horde_client_session:
        simple_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)

        status_response, gen_id = await simple_client.alchemy_request(
            AlchemyAsyncRequest(
                apikey=ANON_API_KEY,
                forms=[
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.caption),
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus),
                ],
                source_image=source_image_base64,
            ),
        )

        for caption_result in status_response.all_caption_results:
            print(f"Caption: {caption_result.caption}")

        for upscale_result in status_response.all_upscale_results:
            upscaled_image = await simple_client.download_image_from_url(upscale_result.url)
            upscaled_image.save(f"{gen_id}_{upscale_result.upscaler_used}.webp")
```

## Request and Response Types

Request objects are always found in the `apimodels` namespace of the corresponding API sub-package (e.g., `horde_sdk.ai_horde_api.apimodels`). See also: [naming](getting_started.md#naming).

Every request type has one or more response types mapped to it. You can get the default success response type like so:

``` python
>>> ImageGenerateAsyncRequest.get_default_success_response_type()
<class 'horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse'>
```

<div class="warning" markdown="1">
    <div class="title" markdown="1">
    Warning
    </div>
    <a href="../horde_sdk/generic_api/apimodels/#horde_sdk.generic_api.apimodels.RequestErrorResponse"> RequestErrorResponse </a> may also be returned depending on the client you are using. Check the <a href="../horde_sdk/generic_api/apimodels/#horde_sdk.generic_api.apimodels.RequestErrorResponse.message"> RequestErrorResponse.message </a> attribute for info on the error. Simple clients raise <code>AIHordeRequestError</code> on errors instead of returning <code>RequestErrorResponse</code>.
</div>

## General Notes and Guidance

### API Expectations

#### Important note about manual clients

A few endpoints, such as `/v2/generate/async` ([ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.async_.ImageGenerateAsyncRequest]), will have their operations live on the API server until they are retrieved or cancelled (in this case, with either a [ImageGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate.status.ImageGenerateStatusRequest] or [DeleteImageGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate.status.DeleteImageGenerateRequest]). **If you use a manual client, you are assuming responsibility for making a best-effort for cleaning up errant requests**, especially if your implementation crashes. If you use a simple client, you do not have to worry about this, as [context handlers][horde_sdk.generic_api.generic_clients.GenericHordeAPISession] take care of this.

You can also use [AIHordeAPIClientSession][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIClientSession] (or its async counterpart [AIHordeAPIAsyncClientSession][horde_sdk.ai_horde_api.ai_horde_clients.AIHordeAPIAsyncClientSession]) as a context manager which will automatically clean up pending requests if an exception occurs:

``` python
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIClientSession

with AIHordeAPIClientSession() as horde_session:
    response = horde_session.submit_request(
        my_request,
        my_request.get_default_success_response_type(),
    )
    # If an exception is raised here, the session will attempt to
    # cancel any pending generation requests on exit.
```

### Typing

- **This project is strongly typed.** Practically, this shouldn't leak out too much and should mostly be contained to validation logic.
    - If you find something won't work because of type issues but you think it should, please [file an issue on github](https://github.com/Haidra-Org/horde-sdk/issues).
- This project relies heavily on [pydantic](https://docs.pydantic.dev/latest/). If you are unfamiliar with pydantic, glancing at its documentation before consuming this library may be helpful.
    - Every class from this library potentially has validation on its `__init__(...)` function. You should be prepared to handle pydantic's `ValidationError` exception as a result.
    - Most classes have a `model_dump(...)` ([see the doc](https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump)) method which returns a dictionary representation of the object.
    - If you have JSON or a compatible dict, you can use [`model_validate`](https://docs.pydantic.dev/latest/api/main/#pydantic.main.BaseModel.model_validate) or [`model_validate_json`](https://docs.pydantic.dev/latest/api/main/#pydantic.main.BaseModel.model_validate_json).

### Naming

- Objects serializable to an API request are suffixed with `Request`.
- Objects serializable to an API response are suffixed with `Response`.
- Objects which are not meant to be instantiated are prefixed with `Base`.
    - These are typically parent classes of multiple API objects but do not represent an actual API object on their own.
    - See [horde_sdk.generic_api.apimodels][] for some of the key `Base*` classes.
- Certain API models have attributes which would collide with a python builtin, such as `id` or `type`. In these cases, the attribute has a trailing underscore, as in `id_`. Ingested JSON still works with the field `id` (it's an alias).

### Faux Immutability

*'Why can't I change this attribute?!'*

- All `*Request` and `*Response` classes, and many other classes, implement faux immutability — their attributes are **read only**.
- This prevents you from side-stepping validation.
- See [pydantic's docs](https://docs.pydantic.dev/latest/concepts/validators/#frozen) for more information.
- See also [FAQ](faq.md) for more information.
