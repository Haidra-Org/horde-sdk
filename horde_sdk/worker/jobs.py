from __future__ import annotations

from typing_extensions import override

from horde_sdk.consts import WORKER_TYPE, HTTPMethod
from horde_sdk.generation_parameters import (
    ImageGenerationParameters,
    SingleAlchemyParameters,
    TextGenerationParameters,
)
from horde_sdk.worker.generations import (
    AlchemySingleGeneration,
    ImageSingleGeneration,
    TextSingleGeneration,
)
from horde_sdk.worker.job_base import (
    HordeWorkerJob,
    HordeWorkerJobConfig,
)

DEFAULT_UPLOAD_METHOD = HTTPMethod.PUT


class ImageWorkerJob(HordeWorkerJob[ImageSingleGeneration, ImageGenerationParameters]):
    """A job containing only image generations."""

    def __init__(
        self,
        *,
        generation: ImageSingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the image worker job.

        Args:
            generation (ImageSingleGeneration): The generation to use for the job.
            result_ids (Iterable[ID_TYPES] | None): The result IDs for the job.
            job_config (HordeWorkerJobConfig | None): The configuration for the job.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation=generation,
            generation_cls=ImageSingleGeneration,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.image


class AlchemyWorkerJob(HordeWorkerJob[AlchemySingleGeneration, SingleAlchemyParameters]):
    """A job containing only alchemy generations."""

    def __init__(
        self,
        *,
        generation: AlchemySingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the alchemy worker job.

        Args:
            generation (AlchemySingleGeneration): The response from the API.
            result_ids (Iterable[ID_TYPES] | None): The result IDs for the job.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation=generation,
            generation_cls=AlchemySingleGeneration,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.alchemist


class TextWorkerJob(HordeWorkerJob[TextSingleGeneration, TextGenerationParameters]):
    """A job containing only text generations."""

    def __init__(
        self,
        generation: TextSingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the text worker job.

        Args:
            generation (TextSingleGeneration): The response from the API.
            result_ids (Iterable[ID_TYPES] | None): The result IDs for the job.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation=generation,
            generation_cls=TextSingleGeneration,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.text
