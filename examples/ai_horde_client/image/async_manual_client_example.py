import argparse
import asyncio
import sys
import time
from pathlib import Path

import aiofiles
import aiohttp
from loguru import logger

from horde_sdk import ANON_API_KEY, _default_sslcontext
from horde_sdk.ai_horde_api import AIHordeAPIAsyncManualClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerateStatusRequest
from horde_sdk.generic_api.apimodels import RequestErrorResponse


async def main(apikey: str = ANON_API_KEY) -> None:
    logger.info("Starting...")
    async with aiohttp.ClientSession() as aiohttp_session:
        manual_client = AIHordeAPIAsyncManualClient(aiohttp_session=aiohttp_session)

        image_generate_async_request = ImageGenerateAsyncRequest(
            apikey=apikey,
            prompt="A cat in a hat",
            models=["Deliberate"],
        )
        logger.info("Submitting image generation request...")
        response = await manual_client.submit_request(
            image_generate_async_request,
            image_generate_async_request.get_default_success_response_type(),
        )

        if isinstance(response, RequestErrorResponse):
            logger.error(f"Error: {response.message}")
            return

        logger.info("Image generation request submitted!")
        image_done = False

        start_time = time.time()
        cycle_time = start_time

        check_counter = 0
        # Keep making ImageGenerateCheckRequests until the job is done.
        while not image_done:
            current_time = time.time()
            if current_time - cycle_time > 20 or check_counter == 0:
                logger.info(f"{current_time - start_time} seconds elapsed ({check_counter} checks made)...")
                cycle_time = current_time

            check_counter += 1
            check_response = await manual_client.get_generate_check(
                job_id=response.id_,
            )

            if isinstance(check_response, RequestErrorResponse):
                logger.error(f"Error: {check_response.message}")
                return

            if check_response.done:
                logger.info("Image generation done!")
                logger.info(f"{check_response}")
                logger.info(f"{time.time() - cycle_time} seconds elapsed ({check_counter} checks made)...")

                image_done = True
                break

            await asyncio.sleep(5)

        # Get the image with a ImageGenerateStatusRequest.
        image_generate_status_request = ImageGenerateStatusRequest(
            id=response.id_,
        )

        status_response = await manual_client.submit_request(
            image_generate_status_request,
            image_generate_status_request.get_default_success_response_type(),
        )

        if isinstance(status_response, RequestErrorResponse):
            logger.error(f"Error: {status_response.message}")
            return

        for image_gen in status_response.generations:
            logger.info("Image generation:")
            logger.info(f"ID: {image_gen.id_}")
            logger.info(f"URL: {image_gen.img}")

            logger.info("Downloading image...")

            image_bytes = None
            # image_gen.img is a url, download it using aiohttp.
            async with aiohttp.ClientSession() as session, session.get(image_gen.img, ssl=_default_sslcontext) as resp:
                image_bytes = await resp.read()

            if image_bytes is None:
                logger.error("Failed to download image.")
                return

            example_path = Path("requested_images")
            example_path.mkdir(exist_ok=True, parents=True)

            filepath_to_write_to = example_path / f"{image_gen.id_}_man_async_example.webp"

            async with aiofiles.open(filepath_to_write_to, "wb") as file:
                await file.write(image_bytes)

            logger.info(f"Image saved to {filepath_to_write_to}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Horde API Manual Client Example")
    parser.add_argument(
        "--apikey",
        "--api-key",
        "-k",
        type=str,
        default=ANON_API_KEY,
        help="The API key to use. Defaults to the anon key.",
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(args.apikey))
