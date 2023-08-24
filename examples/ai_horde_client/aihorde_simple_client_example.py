from pathlib import Path

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest


def simple_generate_example() -> None:
    simple_client = AIHordeAPISimpleClient()

    status_response, job_id = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            models=["Deliberate"],
        ),
    )

    image = simple_client.download_image_from_generation(status_response.generations[0])

    example_path = Path("examples/requested_images")
    example_path.mkdir(exist_ok=True, parents=True)

    image.save(example_path / f"{job_id}_simple_sync_example.webp")


if __name__ == "__main__":
    simple_generate_example()
