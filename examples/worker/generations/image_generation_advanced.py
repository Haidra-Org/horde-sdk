"""
This example demonstrates an asynchronous image generation workflow using threading and semaphores.

It simulates the lifecycle of a worker, including preloading resources, generating images,
post-processing, safety checks, and submission. The example also shows how to handle errors
and manage concurrent generation processes.

This example does not include interactions with the Horde API or any real image generation logic.

For more details on the worker lifecycle, refer to:
- Worker Loop: docs/haidra-assets/docs/worker_loop.md
- Worker States Flow: docs/ai-horde-worker/worker_states_flow.md
"""

import os
import random
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from uuid import uuid4

from loguru import logger

# You could set this yourself using loguru. See their documentation for more details.
os.environ["HORDE_SDK_LOG_VERBOSITY"] = "10"

from horde_sdk.generation_parameters.alchemy import AlchemyParameters, UpscaleAlchemyParameters
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_UPSCALERS
from horde_sdk.generation_parameters.image import BasicImageGenerationParameters, ImageGenerationParameters
from horde_sdk.safety import SafetyResult, SafetyRules
from horde_sdk.worker.consts import GENERATION_PROGRESS
from horde_sdk.worker.generations import ImageSingleGeneration

# Semaphore to limit concurrent generation processes
# This value would depend on the system's capabilities and the expected load.
# Here, we set it to 3 to allow up to 3 concurrent image generations, which is likely not realistic,
# but helps to illustrate the concept.
#
# In a real-world scenario where you would like concurrency, you likely will need to survey your system's capabilities
# and set this value accordingly.
MAX_CONCURRENT_GENERATIONS = 3
generation_semaphore = Semaphore(MAX_CONCURRENT_GENERATIONS)


def preload_resources(generation: ImageSingleGeneration) -> None:
    """Simulates the preloading of resources required for image generation.

    Args:
        generation (ImageSingleGeneration): The generation instance to preload resources for.
    """
    generation.on_preloading()
    logger.info(f"{generation.short_id} - Preloading resources for image generation")
    time.sleep(2)  # Simulate time taken for preloading
    logger.info(f"{generation.short_id} - Preloading complete")
    generation.on_preloading_complete()


def _simulated_image_backend_handoff(
    generation: ImageSingleGeneration,
    include_post_processing: bool,
    status_callback: Callable[[GENERATION_PROGRESS], None],
    should_fail: bool = False,
) -> bytes | list[bytes] | None:
    """Simulates the handoff to the image generation backend.

    Args:
        generation (ImageSingleGeneration): The generation instance to hand off to the backend.
    """
    logger.info(f"{generation.short_id} - Handoff to image generation backend")
    status_callback(GENERATION_PROGRESS.GENERATING)

    if should_fail:
        logger.error(f"{generation.short_id} - Simulated failure during backend handoff")
        return None

    time.sleep(random.choice([1, 5]))  # Simulate time taken for backend to generation/do inference
    status_callback(GENERATION_PROGRESS.GENERATION_COMPLETE)

    if include_post_processing:
        status_callback(GENERATION_PROGRESS.POST_PROCESSING)
        time.sleep(1)  # Simulate time taken for post-processing
        status_callback(GENERATION_PROGRESS.POST_PROCESSING_COMPLETE)
    logger.info(f"{generation.short_id} - Handoff complete")

    # This should be the result of the image generation process.
    # In a real-world scenario, this would be the bytes of the generated image.
    # Here, we simulate it by encoding a string for demonstration purposes.
    if generation.batch_size == 1:
        return b"simulated_image_bytes"

    return [b"simulated_image_bytes" for _ in range(generation.batch_size)]


def generate_image(generation: ImageSingleGeneration, prompt: str, should_fail: bool = False) -> None:
    with generation_semaphore:
        while True:
            # The generation object has internal limits to the number of ERROR recoveries it allows.
            # By default, it allows 3 recoveries before it considers the generation failed.
            # In the case it is failed, GENERATING will not be a valid next state.
            # This method should be preferred over handling an exception from `on_generating`.
            #
            # You can override this by setting your `HordeWorkerJobConfig` appropriately.
            # See the docs for more details.
            if not generation.is_next_state_valid(GENERATION_PROGRESS.GENERATING):
                logger.error(f"{generation.short_id} - Generation failed.")
                break

            logger.info(f"{generation.short_id} - Attempting to generate image for prompt: {prompt}")

            def status_callback(progress: GENERATION_PROGRESS) -> None:
                """Callback to update the generation progress status."""
                logger.info(f"{generation.short_id} - Generation progress: {progress.name}")

                if progress == GENERATION_PROGRESS.GENERATING:
                    generation.on_generating()
                elif progress == GENERATION_PROGRESS.GENERATION_COMPLETE:
                    logger.info(
                        f"{generation.short_id} - Generation complete. "
                        f"requires_post_processing: {generation.requires_post_processing}",
                    )
                    generation.on_generation_work_complete()
                elif progress == GENERATION_PROGRESS.POST_PROCESSING:
                    generation.on_post_processing()
                elif progress == GENERATION_PROGRESS.POST_PROCESSING_COMPLETE:
                    generation.on_post_processing_complete()

            # Simulate image generation process. This would be the call to the backend or a service
            # which actually does the image generation.
            #
            # In a real-world scenario, this would involve sending the prompt to an API or a
            # local model and receiving the generated image.
            result = _simulated_image_backend_handoff(
                generation,
                include_post_processing=generation.requires_post_processing,
                status_callback=status_callback,
                should_fail=should_fail,
            )

            if result is None:
                logger.error(f"{generation.short_id} - Image generation failed")
                # It is important to signal the generation failure to the generation object.
                # Errors must either recover to the most recent valid state or be aborted.
                generation.on_error(
                    failed_message="Image generation failed during backend handoff.",
                )
                continue

            # Set the final result(s) of the generation. This method supports both single and multiple results
            # depending on the batch size of the generation.
            #
            # This value will be used in the next steps of the generation process.
            #
            # Notice that in this example, the `status_callback` function captured the state transitions
            # so the current state is already set to GENERATION_COMPLETE or POST_PROCESSING_COMPLETE before this call.
            generation.set_work_result(result=result)  # This could happen after a delay if needed.

            logger.info(f"{generation.short_id} - Image generation complete")
            break


def perform_safety_checks(generation: ImageSingleGeneration) -> None:
    """Simulates safety checks on the generated image.

    Iterates over the generated images and performs safety checks on each one. If a result is flagged as NSFW,
    it is logged and the generation is marked as such.

    Args:
        generation (ImageSingleGeneration): The generation instance to perform safety checks on.
    """
    generation.on_safety_checking()
    logger.info(f"{generation.short_id} - Performing safety check on generated images")
    for idx, generation_result in enumerate(generation.generation_results.values()):
        if generation_result is not None:
            time.sleep(2)  # Simulate time taken for safety checks
            safety_result = SafetyResult(
                is_csam=False,
                is_nsfw=random.choice([True, False]),
            )
            logger.info(f"{generation.short_id} - Safety check complete for result index {idx}")
            generation.on_safety_check_complete(batch_index=idx, safety_result=safety_result)
            if safety_result.is_nsfw:
                logger.warning(f"{generation.short_id} - Image flagged as NSFW for result index {idx}")


def submit_results(generation: ImageSingleGeneration) -> None:
    """Simulates submission of the generated image.

    Args:
        generation (ImageSingleGeneration): The generation instance to submit results for.
    """
    generation.on_submitting()
    for idx, generation_result in enumerate(generation.generation_results.values()):
        if generation_result is not None:
            logger.info(f"{generation.short_id} - Submitting generated image for result index {idx}")
            time.sleep(1)  # Simulate time taken for submission
            logger.info(f"{generation.short_id} - Submission complete for result index {idx}")
        else:
            logger.warning(
                f"{generation.short_id} - No generated image to submit for result index {idx}. Was it censored?",
            )

    generation.on_submit_complete()
    logger.success(f"{generation.short_id} - Submission complete")


class GenerationResultDetail:
    def __init__(self, result_index: int, status: str, nsfw_detail: SafetyResult | None) -> None:
        self.result_index = result_index
        self.status = status
        self.nsfw_detail = nsfw_detail


class GenerationRunResult:
    def __init__(
        self,
        generation_id: str,
        short_id: str,
        prompt: str,
        status: str,
        results: list[GenerationResultDetail],
    ) -> None:
        self.generation_id = generation_id
        self.short_id = short_id
        self.prompt = prompt
        self.status = status
        self.results = results


def generation_process(generation_params: ImageGenerationParameters, should_fail: bool) -> GenerationRunResult:
    """Simulates the entire generation process for a single generation request.

    Args:
        generation_params (ImageGenerationParameters): The parameters for the image generation.
    Returns:
        dict: Summary of the generation process.
    """
    generation_id = str(uuid4())
    logger.info(f"Generation ID: {generation_id}")

    generation = ImageSingleGeneration(
        generation_parameters=generation_params,
        generation_id=generation_id,
        safety_rules=SafetyRules(
            should_censor_nsfw=random.choice([True, False, False]),
        ),
    )

    logger.info(f"{generation.short_id} - Starting generation process")

    preload_resources(generation)

    prompt = generation_params.base_params.prompt
    generate_image(generation, prompt, should_fail=should_fail)

    # Abort if all generation attempts failed.
    if all(generation_result is None for generation_result in generation.generation_results):
        logger.error(f"{generation.short_id} - All generation attempts failed. Aborting.")
        generation.on_abort(failed_message="All generation attempts failed.")
        return GenerationRunResult(
            generation_id=generation_id,
            short_id=generation.short_id,
            prompt=prompt,
            status="failed",
            results=[],
        )

    perform_safety_checks(generation)
    submit_results(generation)
    logger.info(f"{generation.short_id} - Generation process finalized")

    # Collect useful results for summary
    results = []
    for idx, generation_result in enumerate(generation.generation_results.values()):
        safety_check_results = generation.get_safety_check_results()
        if generation_result is not None:
            results.append(
                GenerationResultDetail(
                    result_index=idx,
                    status="success",
                    nsfw_detail=(safety_check_results[idx] if safety_check_results else None),
                ),
            )
        else:
            results.append(
                GenerationResultDetail(
                    result_index=idx,
                    status="censored_or_failed",
                    nsfw_detail=safety_check_results[idx] if safety_check_results else None,
                ),
            )

    return GenerationRunResult(
        generation_id=generation_id,
        short_id=generation.short_id,
        prompt=prompt,
        status="completed",
        results=results,
    )


class GenerationTestCaseData:
    prompt: str
    result_ids: list[str]
    include_post_processing: bool
    should_fail_on_generation: bool

    def __init__(
        self,
        prompt: str,
        result_ids: list[str],
        include_post_processing: bool = False,
        should_fail_on_generation: bool = False,
    ) -> None:
        """Initializes a test case for image generation.

        Args:
            prompt (str): The prompt for the image generation.
            result_ids (list[str]): The result IDs for the image generation.
            include_post_processing (bool): Whether to include post-processing steps.
            should_fail_on_generation (bool): Whether the generation should fail (for testing purposes).
        """
        self.prompt = prompt
        self.result_ids = result_ids
        self.include_post_processing = include_post_processing
        self.should_fail_on_generation = should_fail_on_generation


class GenerationTestCase:
    def __init__(
        self,
        generation_parameters: ImageGenerationParameters,
        should_fail_on_generation: bool = False,
    ) -> None:
        self.generation_parameters = generation_parameters
        self.should_fail_on_generation = should_fail_on_generation


def get_generation_test_cases() -> list[GenerationTestCase]:
    """Simulates fetching generation parameters for multiple image generations.

    Returns:
        list[GenerationTestCase]: A list of test cases for different image generations.
    """

    test_case_data = [
        GenerationTestCaseData(
            prompt="A beautiful landscape with mountains and a river",
            result_ids=[str(uuid4())],
            include_post_processing=False,
            should_fail_on_generation=False,
        ),
        GenerationTestCaseData(
            prompt="A futuristic cityscape at night",
            result_ids=[str(uuid4()), str(uuid4())],
            include_post_processing=True,
            should_fail_on_generation=False,
        ),
        GenerationTestCaseData(
            prompt="A serene beach during sunset",
            result_ids=[str(uuid4())],
            include_post_processing=False,
            should_fail_on_generation=True,
        ),
        GenerationTestCaseData(
            prompt="A bustling market in a medieval town",
            result_ids=[str(uuid4())],
            include_post_processing=False,
            should_fail_on_generation=False,
        ),
        GenerationTestCaseData(
            prompt="A close-up of a flower in bloom",
            result_ids=[str(uuid4())],
            include_post_processing=False,
            should_fail_on_generation=False,
        ),
        GenerationTestCaseData(
            prompt="A majestic lion resting in the savannah",
            result_ids=[str(uuid4()), str(uuid4()), str(uuid4()), str(uuid4())],
            include_post_processing=False,
            should_fail_on_generation=False,
        ),
    ]

    # In a typical scenario using the SDK to get jobs, you would not need to manually create these parameters.
    # Instead, you would get job objects which would contain `ImageGenerationParameters` (or similar) as part of their
    # data.
    return [
        GenerationTestCase(
            generation_parameters=ImageGenerationParameters(
                result_ids=test_case_data.result_ids,
                batch_size=len(
                    test_case_data.result_ids,
                ),  # This is the number of images to concurrently generate during one inference call.
                base_params=BasicImageGenerationParameters(
                    prompt=test_case_data.prompt,
                    model="stable_diffusion",
                ),
                alchemy_params=AlchemyParameters(
                    upscalers=[
                        UpscaleAlchemyParameters(
                            result_id=result_id,
                            source_image=b"dummy_image_bytes",
                            upscaler=KNOWN_UPSCALERS.RealESRGAN_x4plus,
                        )
                        for result_id in test_case_data.result_ids
                    ],
                ),
            ),
            should_fail_on_generation=test_case_data.should_fail_on_generation,
        )
        for test_case_data in test_case_data
    ]


def main() -> None:
    """
    Entry point for the script. Simulates batch image generation with multiple prompts.
    Prints a summary of each generation at the end.
    """
    test_cases = get_generation_test_cases()
    results: list[GenerationRunResult] = []

    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_GENERATIONS) as executor:
        future_to_case = {
            executor.submit(
                generation_process,
                test_case.generation_parameters,
                test_case.should_fail_on_generation,
            ): test_case
            for test_case in test_cases
        }
        for future in as_completed(future_to_case):
            result = future.result()
            results.append(result)

    print("\n" + "=" * 30)
    print("         Generation Summary")
    print("=" * 30)
    for res in results:
        print(f"\nGeneration ID   : {res.generation_id}")
        print(f"Short ID        : {res.short_id}")
        print(f"Prompt          : {res.prompt}")
        print(f"Status          : {res.status}")
        print("Results:")
        for detail in res.results:
            print(f"  - Result Index : {detail.result_index}")
            print(f"    Status       : {detail.status}")
            print(f"    NSFW Detail  : {detail.nsfw_detail}")
        print("-" * 30)


if __name__ == "__main__":
    main()
