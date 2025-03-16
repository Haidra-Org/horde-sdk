from pydantic import BaseModel, Field

from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    KNOWN_ALCHEMY_TYPES,
    KNOWN_CAPTION_MODELS,
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_NSFW_DETECTOR,
    KNOWN_UPSCALERS,
)
from horde_sdk.generation_parameters.generic import ComposedParameterSetBase


class AlchemyFeatureFlags(BaseModel):
    """Feature flags for an alchemy worker."""

    alchemy_types: list[KNOWN_ALCHEMY_TYPES] = Field(default_factory=list)
    """The alchemy types supported by the worker."""


class SingleAlchemyParameters(BaseModel):
    """Represents the common bare minimum parameters for any alchemy generation."""

    generation_id: str
    """The generation ID to use for the generation."""

    form: KNOWN_ALCHEMY_FORMS | str
    """The form to use for the generation."""

    source_image: bytes | str | None
    """The source image to use for the generation."""


class UpscaleAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for an upscale alchemy generation."""

    upscaler: KNOWN_UPSCALERS | str


class FacefixAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a facefix alchemy generation."""

    facefixer: KNOWN_FACEFIXERS | str


class InterrogateAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for an interrogation alchemy generation."""

    interrogator: KNOWN_INTERROGATORS | str


class CaptionAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a caption alchemy generation."""

    caption_model: KNOWN_CAPTION_MODELS | str


class NSFWAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a NSFW alchemy generation."""

    nsfw_detector: KNOWN_NSFW_DETECTOR | str


class AlchemyParameters(ComposedParameterSetBase):
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

    misc_post_processors: list[SingleAlchemyParameters] | None = None
    """Any other post-processing operations requested."""

    _all_alchemy_operations: list[SingleAlchemyParameters] | None = None
    """The list of all alchemy operations requested."""

    @property
    def all_alchemy_operations(self) -> list[SingleAlchemyParameters]:
        """Get all operations."""
        if self._all_alchemy_operations is not None:
            return self._all_alchemy_operations

        all_operations: list[SingleAlchemyParameters] = []
        if self.upscalers:
            all_operations.extend(self.upscalers)
        if self.facefixers:
            all_operations.extend(self.facefixers)
        if self.interrogators:
            all_operations.extend(self.interrogators)
        if self.captions:
            all_operations.extend(self.captions)
        if self.nsfw_detectors:
            all_operations.extend(self.nsfw_detectors)
        if self.misc_post_processors:
            all_operations.extend(self.misc_post_processors)

        self._all_alchemy_operations = all_operations

        return all_operations
