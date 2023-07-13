import asyncio

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration


async def main() -> None:
    simple_client = AIHordeAPISimpleClient()

    generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
        ImageGenerateAsyncRequest(
            apikey="0000000000",
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = simple_client.generation_to_image(generations[0])
    image.save("cat_in_hat.png")

    # Do 2 requests at once.
    multi_generations: tuple[list[ImageGeneration], list[ImageGeneration]] = await asyncio.gather(
        simple_client.async_image_generate_request(
            ImageGenerateAsyncRequest(
                apikey="0000000000",
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
        simple_client.async_image_generate_request(
            ImageGenerateAsyncRequest(
                apikey="0000000000",
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
    )

    multi_image_1 = simple_client.generation_to_image(multi_generations[0][0])
    multi_image_1.save("cat_in_hat_multi_1.png")

    multi_image_2 = simple_client.generation_to_image(multi_generations[1][0])
    multi_image_2.save("cat_in_hat_multi_2.png")


if __name__ == "__main__":
    asyncio.run(main())
