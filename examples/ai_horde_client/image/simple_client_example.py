import argparse
from pathlib import Path

from loguru import logger
from PIL.Image import Image

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api import KNOWN_SAMPLERS
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient

# isort: off
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
    # ExtraTextEntry,
    LorasPayloadEntry,
    ImageGeneration,
)

# isort: on


def simple_generate_example(api_key: str = ANON_API_KEY) -> None:
    simple_client = AIHordeAPISimpleClient()

    status_response, job_id = simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=api_key,
            params=ImageGenerationInputPayload(
                sampler_name=KNOWN_SAMPLERS.k_euler,
                cfg_scale=4,
                width=512,
                height=512,
                # karras=False,
                hires_fix=False,
                clip_skip=1,
                steps=30,
                # workflow="qr_code",
                # extra_texts=[
                #     ExtraTextEntry(
                #         text="stablehorde.net",
                #         reference="qr_code",
                #     ),
                # ],
                loras=[
                    LorasPayloadEntry(
                        name="GlowingRunesAI",
                        model=1,
                        clip=1,
                        inject_trigger="any",  # Get a random color trigger
                    ),
                ],
                # n=3, # Number of images to generate via batch generation
            ),
            prompt="a dark magical crystal, GlowingRunes_paleblue, 8K resolution###blurry, out of focus",
            models=["Deliberate"],
        ),
    )

    if len(status_response.generations) == 0:
        raise ValueError("No generations returned in the response.")

    example_path = Path("requested_images")
    example_path.mkdir(exist_ok=True, parents=True)

    logger.info(
        f"{status_response.kudos} kudos were spent on this request for {len(status_response.generations)} images.",
    )

    def save_image_and_json(
        image: Image,
        generation: ImageGeneration,
        example_path: Path,
        filename_base: str,
    ) -> None:
        image.save(example_path / f"{filename_base}.webp")
        logger.info(f"Image saved to {example_path / f'{filename_base}.webp'}")

        with open(example_path / f"{filename_base}.json", "w") as f:
            f.write(generation.model_dump_json(indent=4))

        logger.info(f"Response JSON saved to {example_path / f'{filename_base}.json'}")

    filename_base = f"{job_id}_simple_sync_example"

    for generation in status_response.generations:
        logger.info("Image generation:")
        logger.info(f"ID: {generation.id_}")
        logger.info(f"URL: {generation.img}")

        logger.info("Downloading image...")

        image_pil = simple_client.download_image_from_generation(generation)

        save_image_and_json(image_pil, generation, example_path, filename_base)


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

    simple_generate_example(api_key)
