"""Object models which represent the parameters for an image generation."""

from horde_sdk.generation_parameters.image.object_models import (
    DEFAULT_BASELINE_RESOLUTION,
    HIRES_FIX_DENOISE_STRENGTH_DEFAULT,
    AuxModelEntry,
    BasicImageGenerationParameters,
    ControlnetGenerationParameters,
    CustomWorkflowGenerationParameters,
    HiresFixGenerationParameters,
    Image2ImageGenerationParameters,
    ImageGenerationParameters,
    LoRaEntry,
    RemixGenerationParameters,
    RemixImageEntry,
    TIEntry,
    default_basic_image_generation_parameters,
)

__all__ = [
    "DEFAULT_BASELINE_RESOLUTION",
    "HIRES_FIX_DENOISE_STRENGTH_DEFAULT",
    "AuxModelEntry",
    "BasicImageGenerationParameters",
    "ControlnetGenerationParameters",
    "CustomWorkflowGenerationParameters",
    "HiresFixGenerationParameters",
    "Image2ImageGenerationParameters",
    "ImageGenerationParameters",
    "LoRaEntry",
    "RemixGenerationParameters",
    "RemixImageEntry",
    "TIEntry",
    "default_basic_image_generation_parameters",
]
