import time
from pathlib import Path

from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api import AIHordeAPIManualClient, download_image_from_generation
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
)


def main(apikey: str = ANON_API_KEY) -> None:
    print("Starting...")

    manual_client = AIHordeAPIManualClient()

    image_generate_async_request = ImageGenerateAsyncRequest(
        apikey=apikey,
        prompt="A cat in a hat",
        models=["Deliberate"],
    )

    print("Submitting image generation request...")

    response: ImageGenerateAsyncResponse | RequestErrorResponse
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
    cycle_time = start_time
    check_counter = 0

    # Keep making ImageGenerateCheckRequests until the job is done.
    while not image_done:
        current_time = time.time()
        if current_time - cycle_time > 20 or check_counter == 0:
            print(f"{current_time - start_time} seconds elapsed ({check_counter} checks made)...")
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
            print(f"Error: {check_response.message}")
            return

        if check_response.done:
            print("Image is done!")
            print(f"{time.time() - cycle_time} seconds elapsed ({check_counter} checks made)...")

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
        print(f"Error: {status_response.message}")
        return

    for image_gen in status_response.generations:
        print("Image generation:")
        print(f"ID: {image_gen.id_}")
        print(f"URL: {image_gen.img}")

        print("Downloading image...")

        image_pil = download_image_from_generation(image_gen)

        example_path = Path("examples/requested_images")
        example_path.mkdir(exist_ok=True, parents=True)

        filepath_to_write_to = example_path / f"{image_gen.id_}_man_sync_example.webp"
        image_pil.save(filepath_to_write_to)

        print(f"Image downloaded to {filepath_to_write_to}!")


if __name__ == "__main__":
    main()
