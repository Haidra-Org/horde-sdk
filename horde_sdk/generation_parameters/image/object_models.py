from __future__ import annotations

from pathlib import Path

import PIL.Image
from pydantic import BaseModel, ConfigDict, Field, model_validator

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters.alchemy import AlchemyParameters
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

DEFAULT_BASELINE_RESOLUTION: int = 512
"""The default assumed (single side) trained resolution for image generation models if unspecified."""
HIRES_FIX_DENOISE_STRENGTH_DEFAULT: float = 0.65
"""The default second-pass denoise strength for hires-fix generations."""


class BasicImageGenerationParameters(BasicModelGenerationParameters):
    """Represents the common bare minimum parameters for an image generation."""

    prompt: str
    """The prompt to use for the generation."""
    seed: str
    """The seed to use for the generation."""

    height: int
    """The height to use for the generation."""
    width: int
    """The width to use for the generation."""
    steps: int
    """The number of steps to use for the generation."""

    cfg_scale: float
    """The scale to use for the generation."""
    sampler_name: KNOWN_SAMPLERS | str
    """The sampler to use for the generation."""
    scheduler: KNOWN_SCHEDULERS | str
    """The scheduler to use for the generation."""
    clip_skip: int
    """The offset of layer numbers to skip. 1 means no layers are skipped."""

    denoising_strength: float
    """The denoising strength to use for the generation."""


class Image2ImageGenerationParameters(BaseModel):
    """Represents the parameters for an image-to-image generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_image: PIL.Image.Image
    """The source image to use for the generation."""
    source_mask: PIL.Image.Image | None
    """The source mask to use for the generation."""


class RemixImageEntry(BaseModel):
    """Represents a special image entry for a generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: PIL.Image.Image
    """The image data."""

    strength: float = 1.0
    """The weight to apply this image to the remix generation."""


class RemixGenerationParameters(BaseModel):
    """Represents the parameters for a stable cascade remix generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    source_image: PIL.Image.Image
    """The source image to use for the generation."""

    remix_images: list[RemixImageEntry]
    """The images to remix the source image with."""


class ControlnetGenerationParameters(BaseModel):
    """Represents the parameters for a controlnet generation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    controlnet_type: KNOWN_CONTROLNETS | str
    """The type of controlnet to use for the generation."""

    source_image: PIL.Image.Image | None
    """The source image to use for the generation, if img2img."""
    control_map: PIL.Image.Image | None
    """The control map to use for the generation, if img2img."""

    return_control_map: bool = False
    """If true, return the control map created by the controlnet pre-processor."""


class HiresFixGenerationParameters(BaseModel):
    """Represents the parameters for a high-resolution fix generation."""

    first_pass: BasicImageGenerationParameters
    second_pass: BasicImageGenerationParameters


class AuxModelEntry(BaseModel):
    """Represents a single entry of an aux model, (LoRas, TIs, etc)."""

    name: str | None
    """The name of the aux model. If this is a hosted aux model, the name to search for. See `remote_version_id` if
    targeting a specific version of a hosted aux model."""
    release_version: str | None = None
    """The version of the aux model. This is v1, v2, etc. If this is a hosted aux model, you should instead use
    `remote_version_id` and reference the platform-specific file identifier."""
    remote_version_id: str | None
    """If this aux model is sourced from a website/API, the version ID specific to that website/API
    to identify the specific version of the aux model. This is *not* v1, v2, but a numeric ID that the
    service assigns and is typically in the URL of the download link."""

    source: KNOWN_AUX_MODEL_SOURCE | str
    """The source of the aux model. This can be a known source or a custom source."""

    remote_url: str | None = None
    """The remote URL to download the aux model from."""
    local_filename: Path | None = None
    """The local filename to load the aux model from."""
    file_hash: str | None = None
    """The hash of the aux model file."""

    model_strength: float = 1
    """The strength of the aux model on the generation model. 1 is the default strength."""

    @model_validator(mode="after")
    def verify_identifier_set(self: AuxModelEntry) -> AuxModelEntry:
        """Ensure that at least one of name, version, or remote_version_id is provided."""
        if self.name is None and self.release_version is None and self.remote_version_id is None:
            raise ValueError("At least one of name, version, or remote_version_id must be provided.")

        return self


class LoRaEntry(AuxModelEntry):
    """Represents a single entry of a LoRa."""

    clip_strength: float = 1
    """The strength of the LoRa on the clip model. 1 is the default strength."""

    lora_triggers: list[str] | None = None
    """The triggers to use for the LoRa. Specify the behavior with `lora_inject_trigger_choice`."""

    lora_inject_trigger_choice: LORA_TRIGGER_INJECT_CHOICE = LORA_TRIGGER_INJECT_CHOICE.NO_INJECT
    """If true and if supported by the backend, inject a trigger term into the prompt."""


class TIEntry(AuxModelEntry):
    """Represents a single entry of a Textual Inversion."""

    ti_inject_trigger_choice: TI_TRIGGER_INJECT_CHOICE = TI_TRIGGER_INJECT_CHOICE.NO_INJECT
    """If true and if supported by the backend, inject a trigger term into the prompt."""


class CustomWorkflowGenerationParameters(BaseModel):
    """Represents the parameters for a custom workflow generation."""

    custom_workflow_name: KNOWN_WORKFLOWS | str
    """The name of the custom workflow to use for the generation."""
    custom_workflow_version: str | None = None
    """The version of the custom workflow to use for the generation. \
        If None, the latest version will be used. Defaults to None."""

    custom_parameters: dict[GENERATION_ID_TYPES, str] | None = None
    """The custom parameters to use for the generation. Defaults to None."""


class ImageGenerationParameters(ComposedParameterSetBase):
    """Represents the parameters for an image generation."""

    generation_ids: list[GENERATION_ID_TYPES]

    batch_size: int = Field(default=1, ge=1)
    """The number of images to generated batched (simultaneously). This is the `n_iter` parameter in ComfyUI"""

    tiling: bool = False
    """If true, the generation will be generated with seamless tiling."""

    source_processing: KNOWN_SOURCE_PROCESSING | str
    """txt2img, img2img, etc. See `KNOWN_SOURCE_PROCESSING` for more information."""

    base_params: BasicImageGenerationParameters
    """The base parameters for the generation."""

    img2img_params: Image2ImageGenerationParameters | None = None
    """If this is an img2img generation, the parameters specific to img2img."""
    remix_params: RemixGenerationParameters | None = None
    """If this is a remix generation, the parameters specific to remix."""
    controlnet_params: ControlnetGenerationParameters | None = None
    """If this is a controlnet generation, the parameters specific to controlnet."""
    hires_fix_params: HiresFixGenerationParameters | None = None
    """If this is a high-resolution fix generation, the parameters specific to high-resolution fix."""
    custom_workflow_params: CustomWorkflowGenerationParameters | None = None
    """If this is a custom workflow generation, the parameters specific to custom workflow."""

    alchemy_params: AlchemyParameters | None = None
    """If alchemy is also requested, the parameters specific to those operations."""

    loras: list[LoRaEntry] | None = None
    """The LoRas to use for the generation."""
    tis: list[TIEntry] | None = None
    """The TIs to use for the generation."""

    @model_validator(mode="after")
    def verify_source_processing(self: ImageGenerationParameters) -> ImageGenerationParameters:
        """Ensure that the appropriate parameters are set based on the source processing type."""
        if self.source_processing in [
            KNOWN_SOURCE_PROCESSING.img2img,
            KNOWN_SOURCE_PROCESSING.inpainting,
            KNOWN_SOURCE_PROCESSING.outpainting,
        ]:
            if self.img2img_params is None:
                raise ValueError("img2img_params must be provided for img2img source processing.")
        elif self.source_processing == KNOWN_SOURCE_PROCESSING.remix and self.remix_params is None:
            raise ValueError("remix_params must be provided for remix source processing.")

        return self

    @model_validator(mode="after")
    def verify_id_count(self: ImageGenerationParameters) -> ImageGenerationParameters:
        """Ensure that at least one generation ID is provided."""
        if not self.generation_ids:
            raise ValueError("At least one generation ID must be provided.")

        if len(self.generation_ids) != self.batch_size:
            raise ValueError("The number of generation IDs must match the batch size.")

        return self
