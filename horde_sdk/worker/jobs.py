from __future__ import annotations

import uuid
from collections.abc import Iterable

from typing_extensions import override

from horde_sdk.consts import GENERATION_ID_TYPES, HTTPMethod
from horde_sdk.generation_parameters import AlchemyParameters, ImageGenerationParameters, TextGenerationParameters
from horde_sdk.worker.consts import WORKER_TYPE
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
        generation_parameters: ImageGenerationParameters,
        upload_map: dict[GENERATION_ID_TYPES, str | None],
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the image worker job.

        Args:
            generation_parameters (ImageGenerationParameters): The response from the API.
            upload_map (dict[str, str | None]): A dict of generation IDs to the upload URLs. Set values to \
                `None` if the generation should not be uploaded.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation_parameters=generation_parameters,
            generation_ids=upload_map.keys() if upload_map is not None else None,
            # upload_map=upload_map,
            generation_cls=ImageSingleGeneration,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.image


class AlchemyWorkerJob(HordeWorkerJob[AlchemySingleGeneration, AlchemyParameters]):
    """A job containing only alchemy generations."""

    @override
    def _init_generations(
        self,
        generation_parameters: AlchemyParameters,
        generation_ids: Iterable[GENERATION_ID_TYPES] | None = None,
    ) -> None:
        if generation_ids is None:
            generation_ids = []
            for _ in range(generation_parameters.get_number_expected_results()):
                generation_ids.append(uuid.uuid4())

        generations: dict[GENERATION_ID_TYPES, AlchemySingleGeneration] = {}
        # FIXME: Some alchemy may result in multiple generations. This is not handled yet.
        for alchemy_operation in generation_parameters.all_alchemy_operations:
            generations[alchemy_operation.generation_id] = AlchemySingleGeneration(
                generation_id=alchemy_operation.generation_id,
                generation_parameters=alchemy_operation,
            )

        self._generations = generations

    def __init__(
        self,
        *,
        generation_parameters: AlchemyParameters,
        upload_map: dict[GENERATION_ID_TYPES, str | None],
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the alchemy worker job.

        Args:
            generation_parameters (AlchemyParameters): The response from the API.
            upload_map (dict[str, str | None]): A dict of generation IDs to the upload URLs. Set values to \
                `None` if the generation should not be uploaded.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation_parameters=generation_parameters,
            # upload_map=upload_map,
            generation_ids=upload_map.keys() if upload_map is not None else None,
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
        *,
        generation_parameters: TextGenerationParameters,
        job_config: HordeWorkerJobConfig | None = None,
    ) -> None:
        """Initialize the text worker job.

        Args:
            generation_parameters (TextGenerationParameters): The response from the API.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
        """
        super().__init__(
            generation_parameters=generation_parameters,
            generation_cls=TextSingleGeneration,
            generation_ids=generation_parameters.generation_ids,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.text
