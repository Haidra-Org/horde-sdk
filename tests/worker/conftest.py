from collections.abc import Callable

import pytest

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters import (
    ImageGenerationParameters,
)
from horde_sdk.worker.job_base import (
    HordeWorkerJobConfig,
)
from horde_sdk.worker.jobs import ImageWorkerJob


@pytest.fixture
def basic_image_job_factory(
    simple_image_generation_parameters_and_upload_map: tuple[
        ImageGenerationParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
) -> Callable[[], ImageWorkerJob]:
    generation_parameters, upload_map = simple_image_generation_parameters_and_upload_map

    def factory() -> ImageWorkerJob:
        job_config = HordeWorkerJobConfig()
        return ImageWorkerJob(
            generation_parameters=generation_parameters,
            upload_map=upload_map,
            job_config=job_config,
        )

    return factory


@pytest.fixture
def basic_image_job(
    basic_image_job_factory: Callable[[], ImageWorkerJob],
) -> ImageWorkerJob:
    return basic_image_job_factory()
