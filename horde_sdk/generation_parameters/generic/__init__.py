"""Contains base class definitions and handling for object models of generation parameters.

See :class:`horde_sdk.generation_parameters.generic.object_models.BasicModelGenerationParameters` for the main
base model for generation parameters.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from horde_sdk.consts import ServiceInfo
from horde_sdk.generation_parameters.generic.consts import UNDERLYING_GENERATION_SCHEME


class AbstractGenerationParameter:
    """Base class for all generation parameters components.

    These classes represent components of generation parameters that can be combined to form a complete
    parameter set. This includes the use of specific auxiliary features such as controlnets, LoRAs, etc.

    You should never instantiate or subclass this class directly. Always use a (pydantic) derived class, such as
    `GenerationParameterBaseModel` or `GenerationParameterList`.
    """


class SchemaVersionedBaseModel(BaseModel):
    """Base model that stamps serialized payloads with a schema version."""

    SCHEMA_VERSION: ClassVar[str] = "1.0"
    """Most recent schema version for this payload."""

    LEGACY_SCHEMA_VERSION: ClassVar[str] = "1.0"
    """Oldest schema version supported for deserialization when unspecified."""

    schema_version: str = Field(
        default="",
        description="Schema version recorded when the payload was serialized.",
    )

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        from_attributes=True,
    )

    @model_validator(mode="before")
    @classmethod
    def _assign_schema_version(cls, data: Any) -> Any:  # noqa: ANN401
        """Populate ``schema_version`` when omitted by callers."""
        if data is None:
            return {"schema_version": cls.SCHEMA_VERSION}

        if isinstance(data, dict):
            if "schema_version" not in data or not data["schema_version"]:
                updated = dict(data)
                updated["schema_version"] = cls.SCHEMA_VERSION
                return updated
            return data

        return data

    @classmethod
    def current_schema_version(cls) -> str:
        """Return the canonical schema version for newly created instances."""
        return cls.SCHEMA_VERSION

    @classmethod
    def legacy_schema_version(cls) -> str:
        """Return the version assumed for pre-metadata payloads."""
        return getattr(cls, "LEGACY_SCHEMA_VERSION", cls.SCHEMA_VERSION)


class GenerationParameterBaseModel(SchemaVersionedBaseModel, AbstractGenerationParameter):
    """Base class for all generation parameters models.

    Contrast this class with `GenerationParameterList`, which is a *collection* of components.
    RootModel should be used when a list of the same component type is allowed. For example, use
    `GenerationParameterBaseModel` for a single LoRa entry and `GenerationParameterList`
    for a list of those LoRa entries.
    """

    underlying_generation_scheme: UNDERLYING_GENERATION_SCHEME | None = None
    """The underlying method the generation uses to produce results.

    - If associated with a auxiliary process that is model based, such as a LoRa, this should be set to `MODEL`.
    - If instead a service is used to produce results, this should be set to `MODEL_FROM_SERVICE`.
    - If there is no generative model involved, and instead a "traditional" algorithm is used, this should be set to
    `NON_MODEL_ALGORITHM`.

    Otherwise, if this component is simply a set of parameters that, in itself, does not produce results, this
    should be set to `None`.
    """


T = TypeVar("T", bound=GenerationParameterBaseModel)
Y = TypeVar("Y", bound=GenerationParameterBaseModel)


class GenerationParameterList(RootModel[list[T]], AbstractGenerationParameter):
    """Base class for all generation parameters models that represent a collection of components.

    This should be a homogeneous collection of the same type of component. For example, if this is a LoRa
    list, all entries should be a `LoRaEntry` instance. Note that this do not prohibit further subclassing
    of the contained components, but you should not mix different component types in the same list. A bad
    example would be having both `LoRaEntry` and `TIEntry` instances in the same list.

    Contrast this class with `GenerationParameterBaseModel`, which is a single component.
    For example, use `GenerationParameterBaseModel` for a single LoRa entry and
    `GenerationParameterList` for a list of those LoRa entries.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        from_attributes=True,
    )

    root: list[T] = Field(default_factory=list)

    def __iter__(self) -> Iterator[T]:  # type: ignore
        return iter(self.root)

    def __len__(self) -> int:
        """Return the length of the root model's data."""
        return len(self.root)

    def __getitem__(self, index: int) -> T:
        """Get an item from the root model's data by index."""
        return self.root[index]

    def get_component_by_type(self, desired_type: type[Y]) -> Y | None:
        """Get all components of a specific type.

        Args:
            desired_type (type[T]): The type of the component to get.

        Returns:
            list[T]: A list of components of the specified type.
        """
        if not issubclass(desired_type, GenerationParameterBaseModel):
            raise TypeError(f"Expected a subclass of GenerationParameterBaseModel, got {desired_type}")

        components = [component for component in self.root if isinstance(component, desired_type)]
        return components[0] if components else None

    def add_component(self, component: T) -> None:
        """Add a component to the container.

        Args:
            component (T): The component to add.
        """
        self.root.append(component)


class GenerationWithModelParameters(GenerationParameterBaseModel):
    """Represents the common bare minimum parameters for any model-based generative inference or similar."""

    underlying_generation_scheme: UNDERLYING_GENERATION_SCHEME = UNDERLYING_GENERATION_SCHEME.MODEL
    """See :attr:`ComposedParameterSetBase.underlying_generation_scheme` for more information."""

    model: str | None = None
    model_baseline: str | None = None


class GenerationByServiceParameters(GenerationParameterBaseModel):
    """A base class for service-based generation parameters.

    This class is intended to be used as a base for all service-based generation parameters, which may include
    additional fields or methods specific to the service being used.
    """

    underlying_generation_scheme: UNDERLYING_GENERATION_SCHEME = UNDERLYING_GENERATION_SCHEME.MODEL_FROM_SERVICE
    """See :attr:`ComposedParameterSetBase.underlying_generation_scheme` for more information."""

    service: ServiceInfo
    """The service to use for the generation, if applicable."""

    @property
    def model_name(self) -> str | None:
        """Get the name of the generation model."""
        raise NotImplementedError()  # FIXME


class CompositeParametersBase(ABC, SchemaVersionedBaseModel):
    """Base class for all combined (composed) parameter sets.

    The top level classes which contain BasicModelGenerationParameters instance and/or other specific parameters
    should inherit from this class. These classes should always represent complete parameter sets that can be used
    for generation.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        from_attributes=True,
        arbitrary_types_allowed=True,  # FIXME
    )

    @abstractmethod
    def get_number_expected_results(self) -> int:
        """Return the number of expected results for this parameter set.

        Returns:
            int: The number of expected results.
        """

    underlying_generation_scheme: UNDERLYING_GENERATION_SCHEME | None = None
    """The underlying method the generation uses to produce results.

    Note that this refers only to the top-level generation itself. Component parameters may contain their own
    underlying generation schemes. For example, for stable diffusion image generation, this would always be
    `MODEL` even if some of the contained components use another scheme such as `MODEL_FROM_SERVICE` or
    `NON_MODEL_ALGORITHM`.

    - If the top-level generation is model-based, this should be set to `MODEL`.
    - If the top-level generation uses an outside service to produce results, this should be set
    to `MODEL_FROM_SERVICE`.
    - If the top-level generation does not use a generative model and instead uses a "traditional" algorithm, this
    should be set to `NON_MODEL_ALGORITHM`.
    """
