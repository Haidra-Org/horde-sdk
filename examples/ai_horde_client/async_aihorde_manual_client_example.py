import asyncio
import time
from pathlib import Path

import aiohttp

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api import AIHordeAPIAsyncManualClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerateStatusRequest
from horde_sdk.generic_api.apimodels import RequestErrorResponse


async def main() -> None:
    print("Starting...")

    async with aiohttp.ClientSession() as aiohttp_session:
        manual_client = AIHordeAPIAsyncManualClient(aiohttp_session=aiohttp_session)

        image_generate_async_request = ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            models=["Deliberate"],
        )
        print("Submitting image generation request...")
        response = await manual_client.submit_request(
            image_generate_async_request,
            image_generate_async_request.get_default_success_response_type(),
        )

        if isinstance(response, RequestErrorResponse):
            print(f"Error: {response.message}")
            return

        print("Image generation request submitted!")
        image_done = False

        start_time = time.time()
        cycle_time = start_time

        check_counter = 0
        # Keep making ImageGenerateCheckRequests until the job is done.
        while not image_done:
            current_time = time.time()
            if current_time - cycle_time > 20 or check_counter == 0:
                print(f"{current_time - start_time} seconds elapsed ({check_counter} checks made)...")
                cycle_time = current_time

            check_counter += 1
            check_response = await manual_client.get_generate_check(
                job_id=response.id_,
            )

            if isinstance(check_response, RequestErrorResponse):
                print(f"Error: {check_response.message}")
                return

            if check_response.done:
                print("Image is done!")
                print(f"{time.time() - cycle_time} seconds elapsed ({check_counter} checks made)...")

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
            print(f"Error: {status_response.message}")
            return

        for image_gen in status_response.generations:
            print("Image generation:")
            print(f"ID: {image_gen.id_}")
            print(f"URL: {image_gen.img}")
            #  debug(image_gen)
            print("Downloading image...")

            image_bytes = None
            # image_gen.img is a url, download it using aiohttp.
            async with aiohttp.ClientSession() as session, session.get(image_gen.img) as resp:
                image_bytes = await resp.read()

            if image_bytes is None:
                print("Error: Could not download image.")
                return

            example_path = Path("examples/requested_images")
            example_path.mkdir(exist_ok=True, parents=True)

            filepath_to_write_to = example_path / f"{image_gen.id_}_man_async_example.webp"

            with open(filepath_to_write_to, "wb") as image_file:
                image_file.write(image_bytes)

            print(f"Image downloaded to {filepath_to_write_to}!")


if __name__ == "__main__":
    asyncio.run(main())
