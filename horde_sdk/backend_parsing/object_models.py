from abc import ABC
from typing import Generic

from strenum import StrEnum
from typing_extensions import TypeVar

from horde_sdk.consts import KNOWN_INFERENCE_BACKEND, WORKER_TYPE
from horde_sdk.generation_parameters.generic import CompositeParametersBase
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
)
from horde_sdk.generation_parameters.image.object_models import ImageGenerationParametersTemplate

SDKParameterSetTypeVar = TypeVar("SDKParameterSetTypeVar", bound=CompositeParametersBase)

BackendSamplersTypeVar = TypeVar("BackendSamplersTypeVar", bound=StrEnum)
BackendSchedulersTypeVar = TypeVar("BackendSchedulersTypeVar", bound=StrEnum)
BackendControlnetsTypeVar = TypeVar("BackendControlnetsTypeVar", bound=StrEnum)


MappingOutputTypeVar = TypeVar("MappingOutputTypeVar", bound=StrEnum)


class BackendValuesMapper(ABC, Generic[SDKParameterSetTypeVar]):
    """Base class for all backend values mappers.

    Value mappers provide a way to convert between the backend representations and the SDK representations of
    certain values. For example, a backend may use a different name for a sampler than the SDK, even though they are
    referring to the same thing.
    """

    _worker_type: WORKER_TYPE
    _inference_backend: KNOWN_INFERENCE_BACKEND

    def _map_value(
        self,
        value: str,
        mapping: dict[str, MappingOutputTypeVar],
        known_input_type: type[StrEnum],
        known_target_type: type[MappingOutputTypeVar],
    ) -> MappingOutputTypeVar:
        if len(mapping) == 0:
            return known_target_type(value)

        if isinstance(value, known_input_type):
            if value in mapping:
                return mapping[value]

            return known_target_type[value.name]

        if isinstance(value, str):
            if value in mapping:
                return mapping[value]
            if value in known_target_type.__members__:
                return known_target_type[value]
            if value in known_target_type.__members__.values():
                return known_target_type(value)

        raise TypeError(
            f"Invalid type for value: {type(value)}, {value}",
        )

    def _is_valid_value(
        self,
        value: str,
        known_type: type[StrEnum],
    ) -> bool:
        """Check if a value is valid for a given known type."""
        if isinstance(value, known_type):
            return True

        if isinstance(value, str):
            if value in known_type.__members__:
                return True
            if value in known_type.__members__.values():
                return True

        return False


class ImageBackendValuesMapper(
    BackendValuesMapper[ImageGenerationParametersTemplate],
    Generic[
        BackendSamplersTypeVar,
        BackendSchedulersTypeVar,
        BackendControlnetsTypeVar,
    ],
):
    """Base class for all image backend values mappers.

    Image backends often refer to samplers and schedulers in different ways in addition to the SDK having its own
    representation of these values.

    See :class:`BackendValuesMapper` for more information.
    """

    _backend_samplers_type: type[BackendSamplersTypeVar]
    _backend_schedulers_type: type[BackendSchedulersTypeVar]
    _backend_controlnets_type: type[BackendControlnetsTypeVar]

    _to_sdk_sampler_map: dict[BackendSamplersTypeVar | str, KNOWN_IMAGE_SAMPLERS]
    _to_sdk_scheduler_map: dict[BackendSchedulersTypeVar | str, KNOWN_IMAGE_SCHEDULERS]
    _to_sdk_controlnet_map: dict[BackendControlnetsTypeVar | str, KNOWN_IMAGE_CONTROLNETS]

    _to_backend_sampler_map: dict[KNOWN_IMAGE_SAMPLERS | str, BackendSamplersTypeVar]
    _to_backend_scheduler_map: dict[KNOWN_IMAGE_SCHEDULERS | str, BackendSchedulersTypeVar]
    _to_backend_controlnet_map: dict[KNOWN_IMAGE_CONTROLNETS | str, BackendControlnetsTypeVar]

    def __init__(
        self,
        *,
        backend_samplers_type: type[BackendSamplersTypeVar],
        backend_schedulers_type: type[BackendSchedulersTypeVar],
        backend_controlnets_type: type[BackendControlnetsTypeVar],
        sdk_samplers_map: dict[BackendSamplersTypeVar | str, KNOWN_IMAGE_SAMPLERS],
        sdk_schedulers_map: dict[BackendSchedulersTypeVar | str, KNOWN_IMAGE_SCHEDULERS],
        sdk_controlnets_map: dict[BackendControlnetsTypeVar | str, KNOWN_IMAGE_CONTROLNETS],
    ) -> None:
        """Initialize the image backend values mapper.

        Args:
            backend_samplers_type: The backend samplers type.
            backend_schedulers_type: The backend schedulers type.
            backend_controlnets_type: The backend controlnets type.
            sdk_samplers_map: The SDK samplers mapping.
            sdk_schedulers_map: The SDK schedulers mapping.
            sdk_controlnets_map: The SDK controlnets mapping.
        """
        self._backend_samplers_type = backend_samplers_type
        self._backend_schedulers_type = backend_schedulers_type
        self._backend_controlnets = backend_controlnets_type

        self._to_sdk_sampler_map = sdk_samplers_map
        self._to_sdk_scheduler_map = sdk_schedulers_map
        self._to_sdk_controlnet_map = sdk_controlnets_map

        self._to_backend_sampler_map = {v: backend_samplers_type(k) for k, v in sdk_samplers_map.items()}
        self._to_backend_scheduler_map = {v: backend_schedulers_type(k) for k, v in sdk_schedulers_map.items()}
        self._to_backend_controlnet_map = {v: backend_controlnets_type(k) for k, v in sdk_controlnets_map.items()}

    def map_to_sdk_sampler(
        self,
        backend_sampler: BackendSamplersTypeVar | str,
    ) -> KNOWN_IMAGE_SAMPLERS:
        """Map a backend sampler to a SDK sampler."""
        return self._map_value(
            value=backend_sampler,
            mapping=self._to_sdk_sampler_map,
            known_input_type=self._backend_samplers_type,
            known_target_type=KNOWN_IMAGE_SAMPLERS,
        )

    def map_to_backend_sampler(
        self,
        sdk_sampler: KNOWN_IMAGE_SAMPLERS | str,
    ) -> BackendSamplersTypeVar | str:
        """Map a SDK sampler to a backend sampler."""
        return self._map_value(
            value=sdk_sampler,
            mapping=self._to_backend_sampler_map,
            known_input_type=KNOWN_IMAGE_SAMPLERS,
            known_target_type=self._backend_samplers_type,
        )

    def is_valid_backend_sampler(
        self,
        backend_sampler: BackendSamplersTypeVar | str,
    ) -> bool:
        """Check if a backend sampler is valid."""
        return self._is_valid_value(
            value=backend_sampler,
            known_type=self._backend_samplers_type,
        )

    def map_to_sdk_scheduler(
        self,
        backend_scheduler: BackendSchedulersTypeVar | str,
    ) -> KNOWN_IMAGE_SCHEDULERS:
        """Map a backend scheduler to a SDK scheduler."""
        return self._map_value(
            value=backend_scheduler,
            mapping=self._to_sdk_scheduler_map,
            known_input_type=self._backend_schedulers_type,
            known_target_type=KNOWN_IMAGE_SCHEDULERS,
        )

    def map_to_backend_scheduler(
        self,
        sdk_scheduler: KNOWN_IMAGE_SCHEDULERS | str,
    ) -> BackendSchedulersTypeVar | str:
        """Map a SDK scheduler to a backend scheduler."""
        return self._map_value(
            value=sdk_scheduler,
            mapping=self._to_backend_scheduler_map,
            known_input_type=KNOWN_IMAGE_SCHEDULERS,
            known_target_type=self._backend_schedulers_type,
        )

    def is_valid_backend_scheduler(
        self,
        backend_scheduler: BackendSchedulersTypeVar | str,
    ) -> bool:
        """Check if a backend scheduler is valid."""
        return self._is_valid_value(
            value=backend_scheduler,
            known_type=self._backend_schedulers_type,
        )

    def map_to_sdk_controlnet(
        self,
        backend_controlnet: BackendControlnetsTypeVar | str,
    ) -> KNOWN_IMAGE_CONTROLNETS:
        """Map a backend controlnet to a SDK controlnet."""
        return self._map_value(
            value=backend_controlnet,
            mapping=self._to_sdk_controlnet_map,
            known_input_type=self._backend_controlnets,
            known_target_type=KNOWN_IMAGE_CONTROLNETS,
        )

    def map_to_backend_controlnet(
        self,
        sdk_controlnet: KNOWN_IMAGE_CONTROLNETS | str,
    ) -> BackendControlnetsTypeVar | str:
        """Map a SDK controlnet to a backend controlnet."""
        return self._map_value(
            value=sdk_controlnet,
            mapping=self._to_backend_controlnet_map,
            known_input_type=KNOWN_IMAGE_CONTROLNETS,
            known_target_type=self._backend_controlnets,
        )

    def is_valid_backend_controlnet(
        self,
        backend_controlnet: BackendControlnetsTypeVar | str,
    ) -> bool:
        """Check if a backend controlnet is valid."""
        return self._is_valid_value(
            value=backend_controlnet,
            known_type=self._backend_controlnets,
        )
