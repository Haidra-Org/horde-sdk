"""Contains class definitions and handling for object models of generation parameters.

For example, the parameters for text generation (inference) are defined in
:class:`horde_sdk.generation_parameters.text.object_models.TextGenerationParameters`
which contains fields such as `prompt`, `max_length`, `temperature`, etc.

"""

from horde_sdk.generation_parameters.alchemy import AlchemyParameters
from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    KNOWN_ALCHEMY_TYPES,
    KNOWN_CAPTION_MODELS,
    KNOWN_CLIP_BLIP_TYPES,
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_MISC_POST_PROCESSORS,
    KNOWN_NSFW_DETECTOR,
    KNOWN_UPSCALERS,
    is_caption_form,
    is_facefixer_form,
    is_interrogator_form,
    is_nsfw_detector_form,
    is_strip_background_form,
    is_upscaler_form,
)
from horde_sdk.generation_parameters.generic import BasicModelGenerationParameters, ComposedParameterSetBase
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_CONTROLNETS,
    KNOWN_SAMPLERS,
    KNOWN_SCHEDULERS,
    KNOWN_SOURCE_PROCESSING,
    KNOWN_WORKFLOWS,
    LORA_TRIGGER_INJECT_CHOICE,
    TI_TRIGGER_INJECT_CHOICE,
)
from horde_sdk.generation_parameters.image.object_models import ImageGenerationParameters
from horde_sdk.generation_parameters.text.object_models import TextGenerationParameters

__all__ = [
    "AlchemyParameters",
    "KNOWN_ALCHEMY_FORMS",
    "KNOWN_ALCHEMY_TYPES",
    "KNOWN_CAPTION_MODELS",
    "KNOWN_CLIP_BLIP_TYPES",
    "KNOWN_FACEFIXERS",
    "KNOWN_INTERROGATORS",
    "KNOWN_MISC_POST_PROCESSORS",
    "KNOWN_NSFW_DETECTOR",
    "KNOWN_UPSCALERS",
    "is_caption_form",
    "is_facefixer_form",
    "is_interrogator_form",
    "is_nsfw_detector_form",
    "is_strip_background_form",
    "is_upscaler_form",
    "BasicModelGenerationParameters",
    "ComposedParameterSetBase",
    "KNOWN_AUX_MODEL_SOURCE",
    "KNOWN_CONTROLNETS",
    "KNOWN_SAMPLERS",
    "KNOWN_SCHEDULERS",
    "KNOWN_SOURCE_PROCESSING",
    "KNOWN_WORKFLOWS",
    "LORA_TRIGGER_INJECT_CHOICE",
    "TI_TRIGGER_INJECT_CHOICE",
    "ImageGenerationParameters",
    "TextGenerationParameters",
]
