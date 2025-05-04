from __future__ import annotations

import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from loguru import logger
from pydantic import BaseModel, Field

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters import ComposedParameterSetBase
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    WORKER_ERRORS,
    WORKER_TYPE,
    HordeWorkerConfigDefaults,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration

SingleGenerationTypeVar = TypeVar("SingleGenerationTypeVar", bound=HordeSingleGeneration[Any])
ComposedParameterSetTypeVar = TypeVar("ComposedParameterSetTypeVar", bound=ComposedParameterSetBase)


class HordeWorkerJobConfig(BaseModel):
    """Configuration for a HordeWorkerJob."""

    max_consecutive_failed_job_submits: int = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_MAX_CONSECUTIVE_FAILED_JOB_SUBMITS,
        ge=1,
        le=HordeWorkerConfigDefaults.UNREASONABLE_MAX_CONSECUTIVE_FAILED_JOB_SUBMITS,
    )
    max_generation_failures: int = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_MAX_GENERATION_FAILURES,
        ge=0,
        le=HordeWorkerConfigDefaults.UNREASONABLE_MAX_GENERATION_FAILURES,
    )

    job_submit_retry_delay: float = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_JOB_SUBMIT_RETRY_DELAY,
        ge=0,
    )

    state_error_limits: dict[GENERATION_PROGRESS, int] = Field(
        default_factory=lambda: HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.copy(),
    )

    generation_strict_transition_mode: bool = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_GENERATION_STRICT_TRANSITION_MODE,
    )

    upload_timeout: float = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_UPLOAD_TIMEOUT,
        ge=0,
    )

    max_retries: int = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_MAX_RETRIES,
        ge=0,
    )

    retry_delay: float = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_RETRY_DELAY,
        ge=0,
    )

    result_image_format: str = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_RESULT_IMAGE_FORMAT,
    )

    result_image_quality: int = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_RESULT_IMAGE_QUALITY,
        ge=1,
        le=100,
    )

    result_image_pil_method: int = Field(
        default=HordeWorkerConfigDefaults.DEFAULT_RESULT_IMAGE_PIL_METHOD,
        ge=0,
    )


class HordeWorkerJob(
    ABC,
    Generic[SingleGenerationTypeVar, ComposedParameterSetTypeVar],
):
    """Base class for all worker jobs.

    Jobs wrap an underlying generation parameter set with meta-information about the job, including
    information sent along from the dispatch source. This includes the remote job ID, the time the job
    was received, and any other higher-level information that is useful for the worker to know in order
    to process the job.

    Consumers of this class should start by iterating over the job's `generation` field. See also
    :class:`horde_sdk.worker.generations_base.HordeSingleGeneration` for more information on
    generation objects and :class:`horde_sdk.generation_parameters.ComposedParameterSetBase` for more
    information on generation parameters.
    """

    _job_config: HordeWorkerJobConfig

    _consecutive_failed_job_submits: int = 0
    """The number of consecutive times the job has failed to submit to the API."""

    def _init_generations(
        self,
        generation_parameters: ComposedParameterSetTypeVar,
        generation_ids: Iterable[GENERATION_ID_TYPES] | None = None,
    ) -> None:
        """Initialize the generations for the job.

        Args:
            generation_parameters (JobPopResponseType): The parameters to construct the generations \
                from.
            generation_ids (Iterable[str]): The unique identifiers for the generations in the job.
        """
        if generation_ids is None:
            generation_ids = []
            for _ in range(generation_parameters.get_number_expected_results()):
                generation_ids.append(uuid.uuid4())

        generations: dict[GENERATION_ID_TYPES, SingleGenerationTypeVar] = {}

        for generation_id in generation_ids:
            generations[generation_id] = self._generation_cls(
                generation_id=generation_id,
                generation_parameters=generation_parameters,
                strict_transition_mode=self._job_config.generation_strict_transition_mode,
            )

        self._generations = generations

    _lock: threading.RLock = threading.RLock()

    def __init__(
        self,
        generation_parameters: ComposedParameterSetTypeVar,
        generation_cls: type[SingleGenerationTypeVar],
        *,
        generation_ids: Iterable[GENERATION_ID_TYPES] | None = None,
        job_config: HordeWorkerJobConfig | None = None,
        time_received: float | None = None,
    ) -> None:
        """Initialize the job.

        Args:
            generation_parameters (JobPopResponseType): The parameters to construct the generations \
                from.
            generation_cls (type[SingleGenerationType]): The class to use for the generations in the job.
            generation_ids (Iterable[str]): The unique identifiers for the generations in the job.
            should_censor_nsfw (bool): Whether or not the user has requested that NSFW content be censored. \
                Defaults to False.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            time_received (float | None): The time the job was received. If `None`, the time the response model was \
                constructed will be used. Defaults to None.
        """
        if job_config is None:
            job_config = HordeWorkerJobConfig()
        self._job_config = job_config

        self._generation_parameters = generation_parameters
        self._generation_cls = generation_cls
        self._init_generations(generation_parameters, generation_ids)

        if time_received is not None:
            self._time_received = time_received

        self._lock = threading.RLock()

    _generation_cls: type[SingleGenerationTypeVar]

    @property
    def generation_cls(self) -> type[SingleGenerationTypeVar]:
        """The (python) type created by the job."""
        return self._generation_cls

    _generations: dict[GENERATION_ID_TYPES, SingleGenerationTypeVar]

    _generation_parameters_cls: type[ComposedParameterSetTypeVar]

    @property
    def generation_parameters_cls(self) -> type[ComposedParameterSetTypeVar]:
        """The (python) type of the generation parameters."""
        return self._generation_parameters_cls

    @property
    def generations(self) -> dict[GENERATION_ID_TYPES, SingleGenerationTypeVar]:
        """The individual generations in this job."""
        with self._lock:
            return self._generations.copy()

    @property
    def ids(self) -> Iterable[GENERATION_ID_TYPES]:
        """The unique identifiers for the generations in this job."""
        with self._lock:
            return self.generations.keys()

    _generation_parameters: ComposedParameterSetTypeVar

    @property
    def generation_parameters(self) -> ComposedParameterSetTypeVar:
        """The dataclass that represents the response from the API."""
        return self._generation_parameters

    @classmethod
    @abstractmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        """Type of worker that can process this job."""

    # TODO
    # FIXME
    # _time_received: float | None = None

    # @property
    # def time_received(self) -> float:
    #     """The time the job response was either received or constructed (in epoch time).

    #     **Note:** This generally will be the time the job was popped from the server. However, manually constructed
    #     api responses or jobs that are not popped from a queue may imbue this property with a different meaning.

    #     You can manually set this value with the `time_received` parameter in the constructor.
    #     """
    #     return self._time_received or self.generation_parameters.time_constructed

    # @property
    # def time_since_received(self) -> float:
    #     """The time since the job was popped from the queue in seconds."""
    #     return time.time() - self.time_received

    _time_submitted: float | None = None

    @property
    def time_submitted(self) -> float | None:
        """The time the job was submitted to the API in epoch time or None if not submitted."""
        return self._time_submitted

    time_spent_generating: float = 0.0
    """The time spent generating the job in seconds."""
    time_to_download_aux_models: float = 0.0
    """The time spent downloading user-specified auxiliary models specific to the job (i.e., LoRas) in seconds."""

    # _job_state_api: GENERATION_STATE | None = None

    @property
    def job_identifier_string(self) -> str:
        """Returns a string that identifies the job.

        Example: (2021-09-01 12:13:12) ['00000000-0000-0000-0000-000000000000']
        """
        # TODO
        # FIXME
        # time_utc_formatted = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(self.time_received))
        # return f"({time_utc_formatted}) {self.ids}"
        return f"{self.ids}"

    _fault_reason: WORKER_ERRORS | None = None
    _faulted_at: float | None = None
    _faulted: bool = False

    @property
    def faulted_reason(self) -> WORKER_ERRORS | None:
        """The reason the job was faulted or None if not faulted."""
        with self._lock:
            return self._fault_reason

    @property
    def faulted_at(self) -> float | None:
        """The time the job was faulted in epoch time or None if not faulted."""
        with self._lock:
            return self._faulted_at

    @property
    def is_faulted(self) -> bool:
        """Whether or not the job has been marked as faulted."""
        with self._lock:
            return self._faulted

    # TODO
    # FIXME
    # @property
    # def job_state_api(self) -> GENERATION_STATE | None:
    # """The state of the job using the codes used by the API or None if there is no comparable state."""
    # return self._job_state_api

    _should_censor_nsfw: bool = False
    """Whether or not the user has requested that NSFW content be censored."""

    @property
    def should_censor_nsfw(self) -> bool:
        """Whether or not the user has requested that NSFW content be censored."""
        return self._should_censor_nsfw

    @property
    def any_generation_censored(self) -> bool | None:
        """Whether or not any generations in the job are censored."""
        with self._lock:
            if not self.generations:
                return None

            return any(gen.is_nsfw or gen.is_csam for gen in self.generations.values())

    def get_generation(self, generation_id: str) -> SingleGenerationTypeVar:
        """Get a generation by its ID."""
        with self._lock:
            if generation_id not in self.generations:
                raise ValueError(f"Generation {generation_id} not found in job {self.job_identifier_string}")

            return self.generations[generation_id]

    @property
    def any_generation_failing(self) -> bool:
        """Return true if any generation is in a failing, aborting, or ending state."""
        with self._lock:
            if not self.generations:
                return False

            return any(
                GENERATION_PROGRESS.is_state_failing(gen.get_generation_progress())
                for gen in self.generations.values()
            )

    def set_job_faulted(self, faulted_reason: WORKER_ERRORS) -> None:
        """Mark the entire job as faulted.

        Note: This will mark all generations in the job as faulted.
        """
        with self._lock:
            if self._faulted:
                logger.warning(
                    f"Job {self.job_identifier_string} is already marked faulted with "
                    f"reason {self._fault_reason} at {self._faulted_at}",
                )

            self._faulted = True
            self._fault_reason = faulted_reason
            self._faulted_at = time.time()

            for generation in self.generations.values():
                generation.on_abort(failed_message=faulted_reason, failure_exception=None)

    @property
    def is_job_finalized(self) -> bool:
        """Return true if all generations in the job are finalized.

        Note: This means that all generations have been submitted as either successful or failed, or have been
        abandoned. Accordingly, there is nothing more to do with the job.
        """
        with self._lock:
            for generation in self.generations.values():
                if generation.get_generation_progress() not in (
                    GENERATION_PROGRESS.SUBMIT_COMPLETE,
                    GENERATION_PROGRESS.REPORTED_FAILED,
                ):
                    return False

            return True

    @property
    def job_completed_successfully(self) -> bool:
        """Return true if all generations in the job are completed successfully."""
        with self._lock:
            for generation in self.generations.values():
                if generation.get_generation_progress() != GENERATION_PROGRESS.SUBMIT_COMPLETE:
                    return False

            return True

    def __eq__(self, value: Any) -> bool:  # noqa: ANN401 - this method is an exception to the rule
        """Check if two jobs are equal."""
        if not isinstance(value, HordeWorkerJob):
            return False

        with self._lock:
            all_ids_in_self = all(generation_id in value.ids for generation_id in self.ids)
            all_ids_in_value = all(generation_id in self.ids for generation_id in value.ids)

            return all_ids_in_self and all_ids_in_value
