import asyncio

import aiohttp

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncSimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration


async def async_simple_generate_example() -> None:
    simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session=aiohttp.ClientSession())

    generations: list[ImageGeneration] = await simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey="0000000000",
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = await simple_client.generation_to_image(generations[0])
    image.save("cat_in_hat.png")

    # Do 2 requests at once.
    multi_generations: tuple[list[ImageGeneration], list[ImageGeneration]] = await asyncio.gather(
        simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                apikey="0000000000",
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
        simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                apikey="0000000000",
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
    )

    # FIXME: Do concurrently instead of sequentially.
    multi_image_1 = await simple_client.generation_to_image(multi_generations[0][0])
    multi_image_1.save("cat_in_hat_multi_1.png")

    multi_image_2 = await simple_client.generation_to_image(multi_generations[1][0])
    multi_image_2.save("cat_in_hat_multi_2.png")


if __name__ == "__main__":
    asyncio.run(async_simple_generate_example())
