import pytest

from horde_sdk.generation_parameters import (
    AlchemyParameters,
)
from horde_sdk.worker.consts import GENERATION_PROGRESS, WORKER_ERRORS
from horde_sdk.worker.generations import AlchemySingleGeneration, ImageSingleGeneration, TextSingleGeneration
from horde_sdk.worker.jobs import AlchemyWorkerJob, ImageWorkerJob, TextWorkerJob


@pytest.fixture(scope="function")
def simple_image_worker_job(
    simple_image_generation: ImageSingleGeneration,
) -> ImageWorkerJob:
    return ImageWorkerJob(
        generation=simple_image_generation,
    )


def test_init_image_worker_job(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration


def test_init_worker_job_end_to_end_happy_path(
    simple_image_worker_job: ImageWorkerJob,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_image_worker_job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=True,
    )


def test_image_job_abort_immediately(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration

    simple_image_worker_job.set_job_faulted(
        faulted_reason=WORKER_ERRORS.UNHANDLED_EXCEPTION,
        failure_exception=Exception("Test faulted exception"),
    )


def test_image_job_abort_during_generation(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration

    generation = simple_image_worker_job.generation

    assert generation.on_generating() == GENERATION_PROGRESS.GENERATING

    assert generation.on_abort(
        failed_message=WORKER_ERRORS.UNHANDLED_EXCEPTION,
        failure_exception=Exception("Test faulted exception"),
    )


@pytest.fixture(scope="function")
def simple_alchemy_job(
    simple_alchemy_generation_parameters: AlchemyParameters,
) -> AlchemyWorkerJob:
    assert len(simple_alchemy_generation_parameters.all_alchemy_operations) == 1
    alchemy_single_generation_parameters = simple_alchemy_generation_parameters.all_alchemy_operations[0]
    return AlchemyWorkerJob(
        generation=AlchemySingleGeneration(
            generation_parameters=alchemy_single_generation_parameters,
        ),
    )


def test_init_alchemy_job(
    simple_alchemy_job: AlchemyWorkerJob,
) -> None:
    assert simple_alchemy_job is not None
    assert simple_alchemy_job.generation is not None
    assert simple_alchemy_job.generation_cls is AlchemySingleGeneration


def test_init_alchemy_worker_job_end_to_end_happy_path(
    simple_alchemy_job: AlchemyWorkerJob,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_alchemy_job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=False,
        include_post_processing=True,
        include_safety_check=False,
    )


@pytest.fixture(scope="function")
def simple_text_job(
    simple_text_generation: TextSingleGeneration,
) -> TextWorkerJob:
    return TextWorkerJob(
        generation=simple_text_generation,
    )


def test_init_text_job(
    simple_text_job: TextWorkerJob,
) -> None:
    assert simple_text_job is not None
    assert simple_text_job.generation_cls is TextSingleGeneration


def test_init_text_worker_job_end_to_end_happy_path(
    simple_text_job: TextWorkerJob,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_text_job.generation,
        result="Dummy result",
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=False,
    )
