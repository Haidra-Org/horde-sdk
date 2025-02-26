"""Contains class definitions and handling for object models of generation parameters.

For example, the parameters for text generation (inference) are defined in
:class:`horde_sdk.generation_parameters.text.object_models.TextGenerationParameters`
which contains fields such as `prompt`, `max_length`, `temperature`, etc.

"""

from horde_sdk.generation_parameters.alchemy import AlchemyParameters
from horde_sdk.generation_parameters.generic import BasicModelGenerationParameters, ComposedParameterSetBase
from horde_sdk.generation_parameters.image.object_models import ImageGenerationParameters
from horde_sdk.generation_parameters.text.object_models import TextGenerationParameters

__all__ = [
    "AlchemyParameters",
    "BasicModelGenerationParameters",
    "ComposedParameterSetBase",
    "ImageGenerationParameters",
    "TextGenerationParameters",
]
