from abc import ABC, abstractmethod
from typing import Any

from horde_sdk import KNOWN_DISPATCH_SOURCE
from horde_sdk.consts import WORKER_TYPE
from horde_sdk.generation_parameters.generic import CompositeParametersBase
from horde_sdk.worker.generations_base import HordeSingleGeneration
from horde_sdk.worker.job_base import HordeWorkerJob


class JobPopStrategyGeneric[SingleGenerationTypeVar, ComposedParameterSetTypeVar](ABC):
    """Abstract base class for job pop strategies."""

    _default_job_pop_time_spacing: float = 1.0
    """Default minimum time spacing between job pops in seconds."""

    def __init__(
        self,
        default_job_pop_time_spacing: float = _default_job_pop_time_spacing,
    ) -> None:
        """Initialize the job pop strategy."""
        self._default_job_pop_time_spacing = default_job_pop_time_spacing

    @abstractmethod
    def get_worker_type(self) -> WORKER_TYPE:
        """Get the worker type associated with this job pop strategy.

        Returns:
            WORKER_TYPE: The worker type.
        """

    @abstractmethod
    def get_dispatch_source(self) -> KNOWN_DISPATCH_SOURCE | str:
        """Get the dispatch source associated with this job pop strategy.

        Returns:
            KNOWN_DISPATCH_SOURCE | str: The dispatch source.
        """

    @abstractmethod
    def pop_job(self) -> HordeWorkerJob[HordeSingleGeneration[Any], CompositeParametersBase] | None:
        """Pop a job synchronously from the dispatch source.

        Use `async_pop_job` for asynchronous operations.

        Returns:
            HordeWorkerJob[HordeSingleGeneration[Any], CompositeParametersBase] | None: The popped job or `None` if
            no job is available.
        """

    @abstractmethod
    async def async_pop_job(self) -> HordeWorkerJob[HordeSingleGeneration[Any], CompositeParametersBase] | None:
        """Pop a job asynchronously from the dispatch source.

        Use `pop_job` if you prefer synchronous operations.

        Returns:
            HordeWorkerJob[HordeSingleGeneration[Any], CompositeParametersBase] | None: The popped job or `None` if
            no job is available.
        """
