from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Iterable

import aiohttp
import requests
import yarl
from loguru import logger
from typing_extensions import override

from horde_sdk import _async_client_exceptions, _default_sslcontext
from horde_sdk.consts import GENERATION_ID_TYPES, HTTPMethod
from horde_sdk.generation_parameters import AlchemyParameters, ImageGenerationParameters, TextGenerationParameters
from horde_sdk.worker.consts import WORKER_TYPE
from horde_sdk.worker.generations import (
    AlchemySingleGeneration,
    ImageSingleGeneration,
    TextSingleGeneration,
)
from horde_sdk.worker.job_base import (
    ComposedParameterSetTypeVar,
    HordeWorkerJob,
    HordeWorkerJobConfig,
    SingleGenerationTypeVar,
)

DEFAULT_UPLOAD_METHOD = HTTPMethod.PUT


class _UploadJob(HordeWorkerJob[SingleGenerationTypeVar, ComposedParameterSetTypeVar]):
    """A job type which uploads its results to specified URLs."""

    _upload_map: dict[GENERATION_ID_TYPES, str | None]
    """A dict of generation IDs to the upload URLs."""

    _upload_method: HTTPMethod

    def __init__(
        self,
        generation_parameters: ComposedParameterSetTypeVar,
        upload_map: dict[GENERATION_ID_TYPES, str | None],
        *,
        generation_cls: type[SingleGenerationTypeVar],
        job_config: HordeWorkerJobConfig | None = None,
        upload_method: HTTPMethod = DEFAULT_UPLOAD_METHOD,
    ) -> None:
        """Initialize the job.

        Args:
            generation_parameters (ComposedParameterSetTypeVar): The response from the API.
            upload_map (dict[str, str | None]): A dict of generation IDs to the upload URLs. Set values to \
                `None` if the generation should not be uploaded.
            generation_cls (type[SingleGenerationTypeVar]): The class to use for the generations.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            upload_method (HTTPMethod, optional): The HTTP method to use for the uploads. \
                Defaults to DEFAULT_UPLOAD_METHOD.
        """
        self._upload_map = upload_map
        self._upload_method = upload_method

        super().__init__(
            generation_parameters=generation_parameters,
            generation_cls=generation_cls,
            generation_ids=upload_map.keys(),
            job_config=job_config,
        )

    def _do_single_upload(
        self,
        generation_id: GENERATION_ID_TYPES,
        generation: SingleGenerationTypeVar,
        upload_url: str,
    ) -> bool:
        """Upload a single generation."""
        if generation.generation_result is None:
            raise ValueError(f"Generation {generation_id} has no result to upload.")

        if not isinstance(generation.generation_result, bytes):
            logger.debug(f"Generation {generation_id} result is not bytes: {type(generation.generation_result)}")

        attempts = 0

        while attempts < self._job_config.max_retries:
            attempts += 1
            try:
                response: requests.Response
                if self._upload_method == HTTPMethod.PUT:
                    response = requests.put(
                        upload_url,
                        data=generation.generation_result,
                        timeout=self._job_config.upload_timeout,
                    )
                elif self._upload_method == HTTPMethod.POST:
                    response = requests.post(
                        upload_url,
                        data=generation.generation_result,
                        timeout=self._job_config.upload_timeout,
                    )
                else:
                    raise ValueError(f"Unsupported upload method: {self._upload_method}")

                if response.status_code == 500:
                    logger.warning(
                        "Retrying upload. This is a issue at the remote server and only is a concern if "
                        "you see this message 5 or more times a minute.",
                    )
                elif response.status_code != 200:
                    logger.error(f"Failed to upload image: {response}")
                else:
                    logger.debug(f"Uploaded image: {generation_id}")
                    return True
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to upload image ({type(e)}): {e}")
            except Exception as e:
                logger.warning(f"Failed to upload image ({type(e)}): {e}")

            time.sleep(self._job_config.retry_delay)

        logger.error(f"Failed to upload image to after {attempts} attempts: {generation_id}")
        return False

    def do_uploads(self) -> bool:
        """Perform uploads for image jobs."""
        all_successful = True
        for generation_id, generation in self._generations.items():
            upload_url = self._upload_map.get(generation_id)
            if upload_url is None:
                raise ValueError(f"No upload URL found for generation {generation_id}.")

            if not self._do_single_upload(
                generation_id=generation_id,
                generation=generation,
                upload_url=upload_url,
            ):
                all_successful = False
        return all_successful

    async def _do_single_upload_async(
        self,
        generation_id: GENERATION_ID_TYPES,
        generation: SingleGenerationTypeVar,
        upload_url: str,
        client_session: aiohttp.ClientSession,
    ) -> bool:
        """Upload a single generation."""
        if generation.generation_result is None:
            raise ValueError(f"Generation {generation_id} has no result to upload.")

        if not isinstance(generation.generation_result, bytes):
            logger.debug(f"Generation {generation_id} result is not bytes: {type(generation.generation_result)}")

        attempts = 0

        while attempts < self._job_config.max_retries:
            attempts += 1
            try:
                if self._upload_method == HTTPMethod.PUT:
                    async with client_session.put(
                        yarl.URL(upload_url, encoded=True),
                        data=generation.generation_result,
                        skip_auto_headers={"content-type"},
                        timeout=aiohttp.ClientTimeout(total=self._job_config.upload_timeout),
                        ssl=_default_sslcontext,
                    ) as response:
                        if response.status == 500:
                            logger.warning(
                                "Retrying upload to . This is a server issue and only is a concern if "
                                "you see this message 5 or more times a minute.",
                            )
                        elif response.status != 200:
                            logger.error(f"Failed to upload image: {response}")
                        else:
                            logger.debug(f"Uploaded image: {generation_id}")
                            return True
                elif self._upload_method == HTTPMethod.POST:
                    async with client_session.post(
                        yarl.URL(upload_url, encoded=True),
                        data=generation.generation_result,
                        skip_auto_headers={"content-type"},
                        timeout=aiohttp.ClientTimeout(total=self._job_config.upload_timeout),
                        ssl=_default_sslcontext,
                    ) as response:
                        if response.status == 500:
                            logger.warning(
                                "Retrying upload. This is a server issue and only is a concern if "
                                "you see this message 5 or more times a minute.",
                            )
                        elif response.status != 200:
                            logger.error(f"Failed to upload image to : {response}")
                        else:
                            logger.debug(f"Uploaded image to : {generation_id}")
                            return True
                else:
                    raise ValueError(f"Unsupported upload method: {self._upload_method}")

            except _async_client_exceptions as e:
                logger.warning(f"Failed to upload image to ({type(e)}): {e}")
            except Exception as e:
                logger.warning(f"Failed to upload image to ({type(e)}): {e}")

            await asyncio.sleep(self._job_config.retry_delay)

        logger.error(f"Failed to upload image to after {attempts} attempts: {generation_id}")
        return False

    async def do_uploads_async(self, client_session: aiohttp.ClientSession) -> bool:
        """Perform uploads for image jobs."""
        upload_tasks: list[asyncio.Task[bool]] = []
        for generation_id, generation in self._generations.items():

            upload_url = self._upload_map.get(generation_id)
            if upload_url is None:
                raise ValueError(f"No upload URL found for generation {generation_id}.")

            upload_tasks.append(
                asyncio.create_task(
                    self._do_single_upload_async(
                        generation_id=generation_id,
                        generation=generation,
                        upload_url=upload_url,
                        client_session=client_session,
                    ),
                ),
            )

        upload_task_results = await asyncio.gather(*upload_tasks)

        return all(upload_task_results)


class ImageWorkerJob(_UploadJob[ImageSingleGeneration, ImageGenerationParameters]):
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
            upload_map=upload_map,
            generation_cls=ImageSingleGeneration,
            job_config=job_config,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.image


class AlchemyWorkerJob(_UploadJob[AlchemySingleGeneration, AlchemyParameters]):
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
            upload_map=upload_map,
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
