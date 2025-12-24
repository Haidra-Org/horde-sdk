from __future__ import annotations

import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence
from enum import auto
from typing import Any, TypeVar

from loguru import logger
from pydantic import BaseModel, Field
from strenum import StrEnum

from horde_sdk.consts import ID_TYPES, WORKER_TYPE
from horde_sdk.generation_parameters import CompositeParametersBase
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    WORKER_ERRORS,
    HordeWorkerConfigDefaults,
    finalized_generation_states,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration

SingleGenerationTypeVar = TypeVar("SingleGenerationTypeVar", bound=HordeSingleGeneration[Any])
ComposedParameterSetTypeVar = TypeVar("ComposedParameterSetTypeVar", bound=CompositeParametersBase)


class JOB_EXECUTION_MODE(StrEnum):
    """How the job should be executed in a chain context."""

    LOCAL_ONLY = auto()
    """Execute job locally on the worker without submitting back to API."""
    SUBMIT_TO_API = auto()
    """Submit job results back to API for distributed chain execution."""


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


class HordeWorkerJob[
    SingleGenerationTypeVar: HordeSingleGeneration[Any],
    ComposedParameterSetTypeVar: CompositeParametersBase,
](
    ABC,
):
    """Base class for all worker jobs.

    Jobs wrap an underlying generation parameter set with meta-information about the job, including
    information sent along from the dispatch source. This includes the remote job ID, the time the job
    was received, and any other higher-level information that is useful for the worker to know in order
    to process the job.

    """

    _local_job_id: ID_TYPES
    _dispatch_job_id: ID_TYPES | None = None
    _job_config: HordeWorkerJobConfig

    _consecutive_failed_job_submits: int = 0
    """The number of consecutive times the job has failed to submit to the API."""

    _lock: threading.RLock = threading.RLock()

    def __init__(
        self,
        generation: SingleGenerationTypeVar,
        generation_cls: type[SingleGenerationTypeVar],
        job_id: ID_TYPES | None = None,
        *,
        dispatch_job_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        job_config: HordeWorkerJobConfig | None = None,
        time_received: float | None = None,
        preserve_generation_id: bool = False,
    ) -> None:
        """Initialize the job.

        Args:
            generation (SingleGenerationType): The generation to use for the job.
            generation_cls (type[SingleGenerationType]): The class to use for the generations in the job.
            job_id (ID_TYPES | None): The unique identifier for the job. If `None`, a new UUID will be generated.
            dispatch_job_id (ID_TYPES | None): Identifier supplied by the dispatch source. Defaults to None when
                the job has not been announced remotely.
            dispatch_result_ids (Sequence[ID_TYPES] | None): Result identifiers supplied by dispatch for the attached
                generation, if available. Defaults to None.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            time_received (float | None): The time the job was received. If `None`, the time the response model was \
                constructed will be used. Defaults to None.
            preserve_generation_id (bool): When True, retain the generation's existing identifier instead of
                rebinding it to the job identifier. Defaults to False.
        """
        if job_config is None:
            job_config = HordeWorkerJobConfig()
        self._job_config = job_config

        self._generation = generation
        self._generation_cls = generation_cls

        effective_job_id = job_id
        if preserve_generation_id:
            if effective_job_id is None:
                effective_job_id = generation.generation_id
                if effective_job_id is None:
                    effective_job_id = uuid.uuid4()
        else:
            if effective_job_id is None:
                effective_job_id = uuid.uuid4()
            self._generation.generation_id = effective_job_id

        self._local_job_id = effective_job_id
        self._dispatch_job_id = dispatch_job_id

        if dispatch_result_ids is not None:
            self._generation.set_dispatch_result_ids(dispatch_result_ids)
        elif dispatch_job_id is not None and not self._generation.dispatch_result_ids:
            self._generation.set_dispatch_result_ids([dispatch_job_id])

        if time_received is not None:
            self._time_received = time_received

        self._lock = threading.RLock()

    _generation_cls: type[SingleGenerationTypeVar]

    @property
    def generation_cls(self) -> type[SingleGenerationTypeVar]:
        """The (python) type created by the job."""
        return self._generation_cls

    _generation: SingleGenerationTypeVar

    _generation_parameters_cls: type[ComposedParameterSetTypeVar]

    @property
    def generation_parameters_cls(self) -> type[ComposedParameterSetTypeVar]:
        """The (python) type of the generation parameters."""
        return self._generation_parameters_cls

    @property
    def generation(self) -> SingleGenerationTypeVar:
        """The individual generations in this job."""
        return self._generation

    @property
    def job_config(self) -> HordeWorkerJobConfig:
        """Return the configuration associated with this job."""
        return self._job_config

    @property
    def job_id(self) -> ID_TYPES:
        """Return the identifier assigned to this job."""
        return self._local_job_id

    @property
    def local_job_id(self) -> ID_TYPES:
        """Alias for :meth:`job_id` to emphasize local scope."""
        return self._local_job_id

    @property
    def dispatch_job_id(self) -> ID_TYPES | None:
        """Return the identifier provided by the dispatch source, if any."""
        with self._lock:
            return self._dispatch_job_id

    def set_dispatch_job_id(self, dispatch_job_id: ID_TYPES | None) -> None:
        """Bind the job to the identifier supplied by dispatch."""
        with self._lock:
            self._dispatch_job_id = dispatch_job_id

    @classmethod
    @abstractmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        """Type of worker that can process this job."""

    _time_received: float | None = None

    @property
    def time_received(self) -> float | None:
        """The time the job response was either received or constructed (in epoch time).

        **Note:** This generally will be the time the job was popped from the server. However, manually constructed
        api responses or jobs that are not popped from a queue may imbue this property with a different meaning.

        You can manually set this value with the `time_received` parameter in the constructor.
        """
        return self._time_received

    @property
    def time_since_received(self) -> float | None:
        """The time since the job was popped from the queue in seconds, or None if not yet received."""
        if self._time_received is None:
            return None
        return time.time() - self._time_received

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
        """Returns a string that identifies the job."""
        return f"{self.generation.generation_id}:{self.generation.result_ids}"

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

    def set_job_faulted(self, faulted_reason: WORKER_ERRORS, failure_exception: Exception | None = None) -> None:
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

            self.generation.on_abort(
                failed_message=faulted_reason,
                failure_exception=failure_exception,
            )

    @property
    def is_job_finalized(self) -> bool:
        """Return true if the generation in the job is finalized.

        Note: This means the generation has been submitted as either successful or failed, or has been
        abandoned. Accordingly, there is nothing more to do with the job.
        """
        with self._lock:
            return self.generation.get_generation_progress() in finalized_generation_states

    @property
    def job_completed_successfully(self) -> bool:
        """Return true if the generation in the job completed successfully."""
        with self._lock:
            return self.generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE
