"""Small client recipes embedded in the Horde SDK documentation."""

from __future__ import annotations

import aiohttp

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api import AIHordeAPIAsyncSimpleClient, AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    AlchemyAsyncRequest,
    AlchemyAsyncRequestFormItem,
    AlchemyCaptionResult,
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
    ModelGenerationInputKobold,
    TextGenerateAsyncRequest,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES


# --8<-- [start:image-request]
def image_request(api_key: str = ANON_API_KEY) -> ImageGenerateAsyncRequest:
    """Build one safe image request."""
    return ImageGenerateAsyncRequest(
        apikey=api_key,
        prompt="A lighthouse above a calm sea at dawn",
        models=["AlbedoBase XL (SDXL)"],
        params=ImageGenerationInputPayload(width=512, height=512, steps=20, n=1),
        nsfw=False,
        censor_nsfw=True,
    )


def generate_image(api_key: str = ANON_API_KEY) -> bytes:
    """Generate the first result and return its decoded pixel bytes."""
    client = AIHordeAPISimpleClient()
    status, _request_id = client.image_generate_request(image_request(api_key))
    if not status.generations:
        raise RuntimeError("The request completed without an image")
    image = client.download_image_from_generation(status.generations[0])
    return image.tobytes()


# --8<-- [end:image-request]


# --8<-- [start:text-request]
def text_request(model: str, api_key: str = ANON_API_KEY) -> TextGenerateAsyncRequest:
    """Build one bounded text request for a currently available model."""
    return TextGenerateAsyncRequest(
        apikey=api_key,
        prompt="Continue in two sentences: The observatory door opened",
        models=[model],
        params=ModelGenerationInputKobold(max_length=80, max_context_length=1024, n=1),
    )


def generate_text(model: str, api_key: str = ANON_API_KEY) -> str:
    """Return the first completed text generation."""
    client = AIHordeAPISimpleClient()
    status, _request_id = client.text_generate_request(text_request(model, api_key))
    if not status.generations or status.generations[0].text is None:
        raise RuntimeError("The request completed without text")
    return status.generations[0].text


# --8<-- [end:text-request]


# --8<-- [start:async-request]
async def generate_image_async(api_key: str = ANON_API_KEY) -> bytes:
    """Run the image recipe without blocking the event loop."""
    async with aiohttp.ClientSession() as http_session:
        client = AIHordeAPIAsyncSimpleClient(aiohttp_session=http_session, apikey=api_key)
        status, _request_id = await client.image_generate_request(image_request(api_key))
        if not status.generations:
            raise RuntimeError("The request completed without an image")
        image, _generation_id = await client.download_image_from_generation(status.generations[0])
        return image.tobytes()


# --8<-- [end:async-request]


# --8<-- [start:alchemy-request]
def caption_image(source_image_url: str, api_key: str = ANON_API_KEY) -> str:
    """Request a caption for an image available at a public URL."""
    request = AlchemyAsyncRequest(
        apikey=api_key,
        source_image=source_image_url,
        forms=[AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.caption)],
    )
    status, _request_id = AIHordeAPISimpleClient().alchemy_request(request)
    if not status.forms or not isinstance(status.forms[0].result, AlchemyCaptionResult):
        raise RuntimeError("The request completed without a caption")
    return status.forms[0].result.caption


# --8<-- [end:alchemy-request]
