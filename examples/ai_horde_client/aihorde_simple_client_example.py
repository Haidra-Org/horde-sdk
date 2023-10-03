import argparse
from pathlib import Path

from loguru import logger

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api import KNOWN_SAMPLERS
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload, LorasPayloadEntry


def simple_generate_example(api_key: str = ANON_API_KEY) -> None:
    simple_client = AIHordeAPISimpleClient()

    status_response, job_id = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=api_key,
            workers=["facf2d67-9e83-4a9e-a7ae-8e555d55af08"],
            params=ImageGenerationInputPayload(
                sampler_name=KNOWN_SAMPLERS.k_euler,
                cfg_scale=4,
                width=768,
                height=512,
                karras=False,
                hires_fix=False,
                clip_skip=1,
                steps=30,
                loras=[
                    LorasPayloadEntry(
                        name="GlowingRunesAI",
                        model=1,
                        clip=1,
                        inject_trigger="any",  # Get a random color trigger
                    ),
                ],
                n=3,
            ),
            prompt="a dark magical crystal, GlowingRunes_paleblue, 8K resolution###blurry, out of focus",
            models=["Deliberate"],
        ),
    )

    if len(status_response.generations) == 0:
        raise ValueError("No generations returned in the response.")

    example_path = Path("examples/requested_images")
    example_path.mkdir(exist_ok=True, parents=True)

    logger.info(
        f"{status_response.kudos} kudos were spent on this request for {len(status_response.generations)} images.",
    )

    if len(status_response.generations) == 1:
        image = simple_client.download_image_from_generation(status_response.generations[0])
        image.save(example_path / f"{job_id}_simple_sync_example.webp")
    else:
        for i, generation in enumerate(status_response.generations):
            image = simple_client.download_image_from_generation(generation)
            image.save(example_path / f"{job_id}_{i}_simple_sync_example.webp")


if __name__ == "__main__":
    # Use arg parser to get the API key
    argParser = argparse.ArgumentParser()

    argParser.add_argument("-k", "--api-key", required=False, default=ANON_API_KEY, help="Your horde API key.")
    args = argParser.parse_args()

    api_key = args.api_key

    while True:
        simple_generate_example(api_key)
