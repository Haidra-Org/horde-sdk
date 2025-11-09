import pytest

from horde_sdk.worker.generations import ImageSingleGeneration
from horde_sdk.worker.jobs import ImageWorkerJob


@pytest.fixture(scope="function")
def simple_image_worker_job(
    simple_image_generation: ImageSingleGeneration,
) -> ImageWorkerJob:
    """Fixture providing a simple ImageWorkerJob for testing."""
    return ImageWorkerJob(
        generation=simple_image_generation,
    )
