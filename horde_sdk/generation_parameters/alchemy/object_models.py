import PIL.Image
from pydantic import BaseModel, ConfigDict

from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    KNOWN_CAPTION_MODELS,
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_NSFW_DETECTOR,
    KNOWN_UPSCALERS,
)


class BasicAlchemyParameters(BaseModel):
    """Represents the common bare minimum parameters for any alchemy generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    form: KNOWN_ALCHEMY_FORMS | str
    """The form to use for the generation."""

    source_image: PIL.Image.Image
    """The source image to u`se for the generation."""


class UpscaleAlchemyParameters(BasicAlchemyParameters):
    """Represents the parameters for an upscale alchemy generation."""

    upscaler: KNOWN_UPSCALERS | str


class FacefixAlchemyParameters(BasicAlchemyParameters):
    """Represents the parameters for a facefix alchemy generation."""

    facefixer: KNOWN_FACEFIXERS | str


class InterrogateAlchemyParameters(BasicAlchemyParameters):
    """Represents the parameters for an interrogation alchemy generation."""

    interrogator: KNOWN_INTERROGATORS | str


class CaptionAlchemyParameters(BasicAlchemyParameters):
    """Represents the parameters for a caption alchemy generation."""

    caption_model: KNOWN_CAPTION_MODELS | str


class NSFWAlchemyParameters(BasicAlchemyParameters):
    """Represents the parameters for a NSFW alchemy generation."""

    nsfw_detector: KNOWN_NSFW_DETECTOR | str


class AlchemyParameters(BaseModel):
    """Represents the parameters for an alchemy generation."""

    upscalers: list[UpscaleAlchemyParameters] | None = None
    """The upscale operations requested."""
    facefixers: list[FacefixAlchemyParameters] | None = None
    """The facefix operations requested."""
    interrogators: list[InterrogateAlchemyParameters] | None = None
    """The interrogation operations requested."""
    captions: list[CaptionAlchemyParameters] | None = None
    """The caption operations requested."""
    nsfw_detectors: list[NSFWAlchemyParameters] | None = None
    """The NSFW detection operations requested."""
