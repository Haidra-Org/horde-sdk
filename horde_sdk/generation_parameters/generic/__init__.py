"""Contains base class definitions and handling for object models of generation parameters.

See :class:`horde_sdk.generation_parameters.generic.object_models.BasicModelGenerationParameters` for the main
base model for generation parameters.
"""

from abc import ABC, abstractmethod

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import BaseModel, ConfigDict


class ComposedParameterSetBase(ABC, BaseModel):
    """Base class for all combined (composed) parameter sets.

    The top level classes which contain BasicModelGenerationParameters instance and/or other specific parameters
    should inherit from this class. These classes should always represent complete parameter sets that can be used
    for generation.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
    )

    @abstractmethod
    def get_number_expected_results(self) -> int:
        """Return the number of expected results for this parameter set.

        Returns:
            int: The number of expected results.
        """


class GenerationParameterComponentBase(BaseModel):
    """Base class for all generation parameters components.

    These classes represent components of generation parameters that can be combined to form a complete
    parameter set. This includes the use of specific auxiliary features such as controlnets, LoRAs, etc.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
    )


class BasicModelGenerationParameters(GenerationParameterComponentBase):
    """Represents the common bare minimum parameters for any model-based generative inference or similar."""

    model: str | None = None
    """The model to use for the generation."""

    model_baseline: str | KNOWN_IMAGE_GENERATION_BASELINE | None = None
    """The baseline of the model. If not specified, it is generally up to the bridge or backend to infer it."""
    model_filename: str | None = None
    """The filename of the model to use for the generation"""
    model_hash: str | None = None
    """The hash of the model to use for the generation"""
