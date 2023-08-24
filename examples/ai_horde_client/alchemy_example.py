import argparse
import asyncio
import base64
from pathlib import Path

import aiohttp
from PIL.Image import Image

from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncSimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    KNOWN_ALCHEMY_TYPES,
    AlchemyAsyncRequest,
    AlchemyAsyncRequestFormItem,
    AlchemyStatusResponse,
)


async def async_alchemy_example(
    apikey: str = ANON_API_KEY,
    source_image_file_path: str = "examples/cat_in_a_hat.webp",
) -> None:
    async with aiohttp.ClientSession() as aiohttp_session:
        simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

        input_image_path = Path(source_image_file_path)

        if not input_image_path.exists():
            print(f"Error: {input_image_path} does not exist.")
            return

        base64_image: str = base64.b64encode(input_image_path.read_bytes()).decode()

        status_response: AlchemyStatusResponse | RequestErrorResponse
        status_response, job_id = await simple_client.alchemy_request(
            AlchemyAsyncRequest(
                apikey=apikey,
                forms=[
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.caption),
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus),
                ],
                source_image=base64_image,
            ),
        )

        print(f"Status: {status_response.state}")

        for caption_result in status_response.all_caption_results:
            print(f"Caption: {caption_result.caption}")

        for upscale_result in status_response.all_upscale_results:
            upscale_result_image: Image = await simple_client.download_image_from_url(upscale_result.url)

            example_path = Path("examples/requested_images")
            example_path.mkdir(exist_ok=True, parents=True)

            upscale_result_image.save(example_path / f"{job_id}_{upscale_result.upscaler_used}.webp")

            print(f"Upscale result saved to {example_path / f'{job_id}_{upscale_result.upscaler_used}.webp'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Horde API Manual Client Example")
    parser.add_argument(
        "--apikey",
        type=str,
        default=ANON_API_KEY,
        help="The API key to use. Defaults to the anon key.",
    )
    args = parser.parse_args()

    # Run the example.
    asyncio.run(async_alchemy_example(args.apikey))
