import argparse
import asyncio
import base64
from pathlib import Path

import aiohttp
from loguru import logger
from PIL.Image import Image

from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncClientSession, AIHordeAPIAsyncSimpleClient
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
    aiohttp_session: aiohttp.ClientSession = aiohttp.ClientSession()
    horde_client_session: AIHordeAPIAsyncClientSession = AIHordeAPIAsyncClientSession(aiohttp_session)
    async with aiohttp_session, horde_client_session:
        simple_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)

        input_image_path = Path(source_image_file_path)

        if not input_image_path.exists():
            logger.error(f"Input image file not found: {input_image_path}")
            return

        source_image_base64: str = base64.b64encode(input_image_path.read_bytes()).decode()

        status_response: AlchemyStatusResponse | RequestErrorResponse
        status_response, job_id = await simple_client.alchemy_request(
            AlchemyAsyncRequest(
                apikey=apikey,
                forms=[
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.caption),
                    AlchemyAsyncRequestFormItem(name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus),
                ],
                source_image=source_image_base64,
            ),
        )

        logger.info(f"Status: {status_response.state}")

        for caption_result in status_response.all_caption_results:
            logger.info(f"Caption: {caption_result.caption}")

        for upscale_result in status_response.all_upscale_results:
            upscale_result_image: Image = await simple_client.download_image_from_url(upscale_result.url)

            example_path = Path("requested_images")
            example_path.mkdir(exist_ok=True, parents=True)

            upscale_result_image.save(example_path / f"{job_id}_{upscale_result.upscaler_used}.webp")

            logger.info(f"Upscaled image saved to {example_path / f'{job_id}_{upscale_result.upscaler_used}.webp'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Horde API Manual Client Example")
    parser.add_argument(
        "-k",
        "--apikey",
        "--api-key",
        "--api_key",
        type=str,
        default=ANON_API_KEY,
        help="The API key to use. Defaults to the anon key.",
    )
    args = parser.parse_args()

    asyncio.run(async_alchemy_example(args.apikey))
