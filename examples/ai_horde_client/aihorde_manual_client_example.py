import time
from pathlib import Path

import requests

from horde_sdk.ai_horde_api import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerateStatusRequest
from horde_sdk.generic_api.apimodels import RequestErrorResponse


def do_generate_check(ai_horde_api_client: AIHordeAPIManualClient) -> None:
    pass


def main() -> None:
    print("Starting...")

    manual_client = AIHordeAPIManualClient()

    image_generate_async_request = ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="A cat in a hat",
        models=["Deliberate"],
    )

    print("Submitting image generation request...")

    response = manual_client.submit_request(
        image_generate_async_request,
        image_generate_async_request.get_default_success_response_type(),
    )

    if isinstance(response, RequestErrorResponse):
        print(f"Error: {response.message}")
        return

    print("Image generation request submitted!")
    image_done = False
    start_time = time.time()
    check_counter = 0
    # Keep making ImageGenerateCheckRequests until the job is done.
    while not image_done:
        if time.time() - start_time > 20 or check_counter == 0:
            print(f"{time.time() - start_time} seconds elapsed ({check_counter} checks made)...")
            start_time = time.time()

        check_counter += 1
        check_response = manual_client.get_generate_check(
            generation_id=response.id_,
        )

        if isinstance(check_response, RequestErrorResponse):
            print(f"Error: {check_response.message}")
            return

        if check_response.done:
            print("Image is done!")
            image_done = True
            break

        time.sleep(5)

    # Get the image with a ImageGenerateStatusRequest.
    image_generate_status_request = ImageGenerateStatusRequest(
        id=response.id_,
    )

    status_response = manual_client.submit_request(
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
        # image_gen.img is a url, download it using the requests library
        try:
            image_bytes = requests.get(image_gen.img).content
        except Exception as e:
            print(f"Error: {e}")
            return

        if image_bytes is None:
            print("Error: Could not download image.")
            return

        # Open a file in write mode and write the image bytes to it.
        dir_to_write_to = Path("examples/requested_images/")
        dir_to_write_to.mkdir(parents=True, exist_ok=True)
        filepath_to_write_to = dir_to_write_to / f"{image_gen.id_}.webp"
        with open(filepath_to_write_to, "wb") as image_file:
            image_file.write(image_bytes)

        print(f"Image downloaded to {filepath_to_write_to}!")


if __name__ == "__main__":
    main()
