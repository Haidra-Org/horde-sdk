from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration


def simple_generate_example() -> None:
    simple_client = AIHordeAPISimpleClient()

    generations: list[ImageGeneration] = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey="0000000000",
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = simple_client.generation_to_image(generations[0])

    image.save("cat_in_hat.png")


if __name__ == "__main__":
    simple_generate_example()
