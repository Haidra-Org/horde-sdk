# Example Clients

See `examples/` for a complete list. These examples are all made in mind with your current working directory as `horde_sdk` (e.g., `cd horde_sdk`).

## Simple Client (sync) Example
From `examples/ai_horde_client/aihorde_simple_client_example.py`:

``` python
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration


def simple_generate_example() -> None:
    simple_client = AIHordeAPISimpleClient()

    generations: list[ImageGeneration] = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = simple_client.generation_to_image(generations[0])

    image.save("cat_in_hat.webp")

if __name__ == "__main__":
    simple_generate_example()
```

## Simple Client (using asyncio) Example
From `examples/ai_horde_client/async_aihorde_simple_client_example.py`:

``` python

import asyncio

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGeneration


async def async_simple_generate_example() -> None:
    simple_client = AIHordeAPISimpleClient()

    generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = simple_client.generation_to_image(generations[0])
    image.save("cat_in_hat.webp")

    # Do 2 requests at once.
    multi_generations: tuple[list[ImageGeneration], list[ImageGeneration]] = await asyncio.gather(
        simple_client.async_image_generate_request(
            ImageGenerateAsyncRequest(
                apikey=ANON_API_KEY,
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
        simple_client.async_image_generate_request(
            ImageGenerateAsyncRequest(
                apikey=ANON_API_KEY,
                prompt="A cat in a hat",
                models=["Deliberate"],
            ),
        ),
    )

    multi_image_1 = simple_client.generation_to_image(multi_generations[0][0])
    multi_image_1.save("cat_in_hat_multi_1.webp")

    multi_image_2 = simple_client.generation_to_image(multi_generations[1][0])

    multi_image_2.save("cat_in_hat_multi_2.webp")
if __name__ == "__main__":
    asyncio.run(async_simple_generate_example())
```
