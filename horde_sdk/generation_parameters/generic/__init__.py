"""Contains base class definitions and handling for object models of generation parameters.

See :class:`horde_sdk.generation_parameters.generic.object_models.BasicModelGenerationParameters` for the main
base model for generation parameters.
"""

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import BaseModel


class ComposedParameterSetBase(BaseModel):
    """Base class for all combined (composed) parameter sets.

    The top level classes which contain BasicModelGenerationParameters instance and/or other specific parameters
    should inherit from this class.
    """


class BasicModelGenerationParameters(BaseModel):
    """Represents the common bare minimum parameters for any model-based generative inference or similar."""

    model: str
    """The model to use for the generation."""

    model_baseline: str | KNOWN_IMAGE_GENERATION_BASELINE | None = None
    """The baseline of the model. If not specified, it is generally up to the bridge or backend to infer it."""
    model_filename: str | None = None
    """The filename of the model to use for the generation"""
    model_hash: str | None = None
    """The hash of the model to use for the generation"""
