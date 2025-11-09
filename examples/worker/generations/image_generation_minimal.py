"""
This is a bare bones example of how to use the generation classes from horde-sdk.

This example demonstrates a basic image generation workflow, including preloading resources,
generating an image, performing a safety check, and submitting the result.

Note that this example does not include error handling or advanced features. See the
`image_generation_advanced.py` example for a more comprehensive workflow.
"""

import time
from uuid import uuid4

from loguru import logger

from horde_sdk.generation_parameters.image import BasicImageGenerationParameters, ImageGenerationParameters
from horde_sdk.safety import SafetyResult
from horde_sdk.worker.generations import ImageSingleGeneration


def do_preload() -> None:
    logger.info("Preloading resources for image generation")
    time.sleep(2)
    logger.info("Preloading complete")


def do_generate() -> bytes:
    logger.info("Generating image")
    time.sleep(3)
    logger.info("Image generation complete")

    return b"Generated image bytes here"


def do_safety_check(result: bytes) -> SafetyResult:
    logger.info("Performing safety check on generated image")
    time.sleep(2)
    logger.info("Safety check complete")

    return SafetyResult(
        is_csam=False,
        is_nsfw=False,
    )


def do_submit() -> None:
    logger.info("Submitting generated image")
    time.sleep(2)
    logger.info("Submission complete")


def main() -> None:
    # Define generation parameters
    result_ids = [str(uuid4())]

    print(f"Expected result IDs: {result_ids}")

    generation_params = ImageGenerationParameters(
        result_ids=result_ids,
        base_params=BasicImageGenerationParameters(
            prompt="A beautiful landscape with mountains and a river",
            model="stable_diffusion",
        ),
    )

    generation_id = str(uuid4())
    print(f"Generation ID: {generation_id}")

    # Initialize the generation
    generation = ImageSingleGeneration(
        generation_parameters=generation_params,
        generation_id=generation_id,
    )

    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")

    # Preload resources
    generation.on_preloading()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")
    do_preload()
    generation.on_preloading_complete()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")

    # Generate the image
    generation.on_generating()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")
    generation.set_work_result(do_generate())
    generation.on_generation_work_complete()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")

    # Perform safety check
    generation.on_safety_checking()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")

    for idx, generation_result in enumerate(generation.generation_results.values()):
        if generation_result is not None:
            safety_result = do_safety_check(generation_result)
            generation.on_safety_check_complete(
                batch_index=idx,
                safety_result=safety_result,
            )

    # Submit the generation
    generation.on_submitting()
    logger.info(f"{generation.generation_id} - {generation.get_generation_progress()}")
    do_submit()


if __name__ == "__main__":
    main()
