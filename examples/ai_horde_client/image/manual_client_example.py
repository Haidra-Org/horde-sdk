import argparse
import time
from pathlib import Path

from loguru import logger

from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api import AIHordeAPIManualClient, download_image_from_generation
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
)


def manual_image_generation(apikey: str = ANON_API_KEY) -> None:
    #  Please see the documentation for important information about the potential
    #  pitfalls of manually managing requests and responses.
    #
    #  See the simple client examples for a more user-friendly way to interact with the API.

    logger.info("Starting...")

    manual_client = AIHordeAPIManualClient()

    image_generate_async_request = ImageGenerateAsyncRequest(
        apikey=apikey,
        prompt="A cat in a hat",
        models=["Deliberate"],
    )

    logger.info("Submitting image generation request...")

    response: ImageGenerateAsyncResponse | RequestErrorResponse
    response = manual_client.submit_request(
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
        check_response: ImageGenerateCheckResponse | RequestErrorResponse
        check_response = manual_client.get_generate_check(
            job_id=response.id_,
        )

        # The above is short hand for:
        # check_response = manual_client.submit_request(
        #     ImageGenerateCheckRequest(
        #         id=response.id_,
        # )

        if isinstance(check_response, RequestErrorResponse):
            logger.error(f"Error: {check_response.message}")
            return

        if check_response.done:
            logger.info("Image generation done!")
            logger.info(f"{time.time() - cycle_time} seconds elapsed ({check_counter} checks made)...")

            image_done = True
            break

        time.sleep(5)

    # Get the image with a ImageGenerateStatusRequest.
    image_generate_status_request = ImageGenerateStatusRequest(
        id=response.id_,
    )

    status_response: ImageGenerateStatusResponse | RequestErrorResponse
    status_response = manual_client.submit_request(
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

        image_pil = download_image_from_generation(image_gen)

        example_path = Path("requested_images")
        example_path.mkdir(exist_ok=True, parents=True)

        filename_base = f"{image_gen.id_}_man_sync_example"

        image_file_path = example_path / f"{filename_base}.webp"
        image_pil.save(image_file_path)

        logger.info(f"Image saved to {image_file_path}")

        with open(example_path / f"{filename_base}.json", "w") as f:
            f.write(image_gen.model_dump_json(indent=4))

        logger.info(f"Response JSON saved to {example_path / f'{filename_base}.json'}")


if __name__ == "__main__":
    argParser = argparse.ArgumentParser()

    argParser.add_argument(
        "-k",
        "--apikey",
        "--api-key",
        "--api_key",
        required=False,
        default=ANON_API_KEY,
        help="Your horde API key.",
    )
    args = argParser.parse_args()

    api_key = args.apikey

    manual_image_generation(api_key)
