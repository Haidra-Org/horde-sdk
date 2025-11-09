"""
This example demonstrates a more advanced image generation workflow using horde-sdk.

It simulates the typical steps involved in generating images, including preloading resources,
generating images, performing safety checks, and submitting results.

This example includes simulated errors and failed safety checks to demonstrate expectations
surrounding the generation process.

"""

import os
import random
import time
from uuid import uuid4

from loguru import logger

# You could set this yourself using loguru. See their documentation for more details.
os.environ["HORDE_SDK_LOG_VERBOSITY"] = "10"

from horde_sdk.generation_parameters.image import BasicImageGenerationParameters, ImageGenerationParameters
from horde_sdk.safety import SafetyResult, SafetyRules
from horde_sdk.worker.consts import GENERATION_PROGRESS
from horde_sdk.worker.generations import ImageSingleGeneration


def do_preload(generation: ImageSingleGeneration) -> None:
    generation.on_preloading()
    logger.info(f"{generation.generation_id} - Preloading resources for image generation")
    time.sleep(2)
    logger.info(f"{generation.generation_id} - Preloading complete")
    generation.on_preloading_complete()


def do_generate(
    generation: ImageSingleGeneration,
    prompt: str,
    should_fail: bool = False,
) -> None:
    while True:
        if not generation.is_next_state_valid(GENERATION_PROGRESS.GENERATING):
            logger.error(f"{generation.generation_id} - Generation failed.")
            break

        generation.on_generating()
        logger.info(f"{generation.generation_id} - Generating image for prompt: {prompt}")

        if should_fail:
            time.sleep(0.5)
            generation.on_error(
                failed_message="Simulated generation failure",
                failure_exception=RuntimeError("Simulated generation failure"),
            )
            logger.error(f"{generation.generation_id} - Generation error")
            continue

        time.sleep(3)
        logger.info(f"{generation.generation_id} - Image generation complete")

        result = f"Generated image bytes for prompt: {prompt}".encode()
        generation.set_work_result(result)
        generation.on_generation_work_complete()
        break


def do_safety_checks(generation: ImageSingleGeneration) -> None:
    generation.on_safety_checking()
    logger.info(f"{generation.generation_id} - Performing safety check on generated images")
    for idx, generation_result in enumerate(generation.generation_results.values()):
        if generation_result is not None:
            time.sleep(2)
            safety_result = SafetyResult(
                is_csam=False,
                is_nsfw=random.choice([True, False]),
            )
            logger.info(f"{generation.generation_id} - Safety check complete for result index {idx}")
            generation.on_safety_check_complete(batch_index=idx, safety_result=safety_result)
            if safety_result.is_nsfw:
                logger.warning(f"{generation.generation_id} - Image flagged as NSFW for result index {idx}")


def do_submit(generation: ImageSingleGeneration) -> None:
    generation.on_submitting()
    for idx, generation_result in enumerate(generation.generation_results.values()):
        if generation_result is not None:
            logger.info(f"{generation.generation_id} - Submitting generated image for result index {idx}")
            time.sleep(1)
            logger.info(f"{generation.generation_id} - Submission complete for result index {idx}")
        else:
            logger.warning(
                f"{generation.generation_id} - No generated image to submit for result index {idx}. Was it censored?",
            )

    generation.on_submit_complete()
    logger.success(f"{generation.generation_id} - Submission complete")


def main() -> None:
    # Define multiple prompts for batch generation
    prompts = [
        "A beautiful landscape with mountains and a river",
        "A futuristic cityscape at night",
        "A serene beach during sunset",
        "A bustling market in a medieval town",
        "A close-up of a flower in bloom",
        "A majestic lion resting in the savannah",
    ]

    result_ids = [str(uuid4()) for _ in prompts]
    print(f"Expected result IDs: {result_ids}")

    generation_params_list = [
        ImageGenerationParameters(
            result_ids=[result_id],
            base_params=BasicImageGenerationParameters(prompt=prompt, model="stable_diffusion"),
        )
        for result_id, prompt in zip(result_ids, prompts, strict=False)
    ]

    for generation_params in generation_params_list:
        generation_id = str(uuid4())
        logger.info(f"Generation ID: {generation_id}")

        generation = ImageSingleGeneration(
            generation_parameters=generation_params,
            generation_id=generation_id,
            safety_rules=SafetyRules(
                should_censor_nsfw=random.choice([True, False, False]),
            ),
        )

        logger.info(f"{generation.generation_id} - Starting generation process")

        do_preload(generation)

        prompt = generation_params.base_params.prompt

        do_generate(generation, prompt, should_fail=random.choice([True, False, False, False]))

        if all(generation_result is None for generation_result in generation.generation_results):
            logger.error(f"{generation.generation_id} - All generation failed. Aborting.")
            generation.on_abort(
                failed_message="All generation attempts failed.",
            )
            logger.info(f"{generation.generation_id} - Generation process aborted")
            continue

        do_safety_checks(generation)

        do_submit(generation)
        logger.info(f"{generation.generation_id} - Finalized")


if __name__ == "__main__":
    main()
