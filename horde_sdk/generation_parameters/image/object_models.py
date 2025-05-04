from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import ConfigDict, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.consts import GENERATION_ID_TYPES, get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.alchemy import AlchemyParameters
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.generation_parameters.generic import (
    BasicModelGenerationParameters,
    ComposedParameterSetBase,
    GenerationParameterComponentBase,
)
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.image.consts import (
    CLIP_SKIP_REPRESENTATION,
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    KNOWN_IMAGE_WORKFLOWS,
    LORA_TRIGGER_INJECT_CHOICE,
    TI_TRIGGER_INJECT_CHOICE,
)

DEFAULT_BASELINE_RESOLUTION: int = 512
"""The default assumed (single side) trained resolution for image generation models if unspecified."""
HIRES_FIX_DENOISE_STRENGTH_DEFAULT: float = 0.65
"""The default second-pass denoise strength for hires-fix generations."""


class ControlnetFeatureFlags(GenerationParameterComponentBase):
    """Feature flags for controlnet."""

    model_config = get_default_frozen_model_config_dict()

    controlnets: list[KNOWN_IMAGE_CONTROLNETS | str] = Field(
        examples=[
            [KNOWN_IMAGE_CONTROLNETS.canny],
            [KNOWN_IMAGE_CONTROLNETS.canny, KNOWN_IMAGE_CONTROLNETS.depth],
        ],
    )
    """The controlnets supported by the worker."""

    image_is_control: bool = Field(default=False)
    """Whether there is support for passing a pre-parsed control image."""

    return_control_map: bool = Field(default=False)
    """Whether there is support returning the control map."""


class ImageGenerationFeatureFlags(GenerationFeatureFlags):
    """Feature flags for an image worker."""

    baselines: list[KNOWN_IMAGE_GENERATION_BASELINE | str] = Field(
        examples=[
            [KNOWN_IMAGE_GENERATION_BASELINE.infer],
            [KNOWN_IMAGE_GENERATION_BASELINE.infer, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1],
        ],
    )
    """The baselines supported for standard image generation.

    If `infer`, the worker will attempt to infer the model type from the model name.
    """

    clip_skip: bool = Field(default=False)
    """Whether there is support for clip skipping."""

    hires_fix: bool = Field(default=False)
    """Whether there is support for hires fix."""

    tiling: bool = Field(default=False)
    """Whether there is support for seamless tiling."""

    schedulers: list[KNOWN_IMAGE_SCHEDULERS | str] = Field(
        examples=[
            [KNOWN_IMAGE_SCHEDULERS.normal],
            [KNOWN_IMAGE_SCHEDULERS.normal, KNOWN_IMAGE_SCHEDULERS.simple],
        ],
    )
    """The schedulers supported."""

    samplers: list[KNOWN_IMAGE_SAMPLERS | str] = Field(
        examples=[
            [KNOWN_IMAGE_SAMPLERS.k_euler],
            [KNOWN_IMAGE_SAMPLERS.k_lms, KNOWN_IMAGE_SAMPLERS.k_euler],
        ],
    )
    """The samplers supported."""

    controlnets_feature_flags: ControlnetFeatureFlags | None = Field(
        default=None,
        examples=[
            ControlnetFeatureFlags(
                controlnets=[KNOWN_IMAGE_CONTROLNETS.canny],
                image_is_control=False,
                return_control_map=False,
            ),
            ControlnetFeatureFlags(
                controlnets=[KNOWN_IMAGE_CONTROLNETS.canny, KNOWN_IMAGE_CONTROLNETS.depth],
                image_is_control=True,
                return_control_map=True,
            ),
        ],
    )
    """The controlnet feature flags for the worker."""

    post_processing: list[KNOWN_ALCHEMY_TYPES | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus],
            [KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus, KNOWN_ALCHEMY_TYPES.GFPGAN],
        ],
    )
    """The post processing methods."""

    source_processing: list[KNOWN_IMAGE_SOURCE_PROCESSING | str] = Field(
        examples=[
            [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img],
            [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img, KNOWN_IMAGE_SOURCE_PROCESSING.img2img],
            [
                KNOWN_IMAGE_SOURCE_PROCESSING.txt2img,
                KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
                KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
            ],
        ],
    )
    """The source processing methods."""

    workflows: list[KNOWN_IMAGE_WORKFLOWS | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_IMAGE_WORKFLOWS.qr_code],
        ],
    )
    """The workflows supported."""

    tis: list[KNOWN_AUX_MODEL_SOURCE | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_AUX_MODEL_SOURCE.HORDELING],
            [KNOWN_AUX_MODEL_SOURCE.LOCAL],
        ],
    )
    """If textual inversions are supported, the sources of the textual inversions supported."""

    loras: list[KNOWN_AUX_MODEL_SOURCE | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_AUX_MODEL_SOURCE.CIVITAI],
            [KNOWN_AUX_MODEL_SOURCE.LOCAL],
        ],
    )

    """If loras are supported, the sources of the loras supported."""

    @field_validator("baselines")
    @classmethod
    def ensure_baseline_non_empty(
        cls,
        v: list[KNOWN_IMAGE_GENERATION_BASELINE | str],
    ) -> list[KNOWN_IMAGE_GENERATION_BASELINE | str]:
        """Ensure that the baselines are not empty."""
        if not v:
            raise ValueError("Baselines cannot be empty.")
        return v


class BasicImageGenerationParametersTemplate(BasicModelGenerationParameters):
    """Represents the common parameters for an image generation."""

    prompt: str | None
    """The prompt to use for the generation."""
    seed: str | None
    """The seed to use for the generation."""

    height: int | None = Field(
        default=None,
        multiple_of=64,
        ge=64,
        examples=[512, 768],
    )
    """The height to use for the generation."""
    width: int | None = Field(
        default=None,
        multiple_of=64,
        ge=64,
        examples=[512, 768],
    )
    """The width to use for the generation."""

    steps: int | None = Field(
        default=None,
        ge=1,
        examples=[4, 20, 50],
    )
    """The number of steps to use for the generation."""

    cfg_scale: float | None = Field(
        default=None,
        ge=0,
        examples=[0.0, 1.0, 7.0],
    )
    """The scale to use for the generation."""

    sampler_name: KNOWN_IMAGE_SAMPLERS | str | None = Field(
        default=None,
        examples=[KNOWN_IMAGE_SAMPLERS.k_lms],
    )
    """The sampler to use for the generation."""

    scheduler: KNOWN_IMAGE_SCHEDULERS | str | None = Field(
        default=None,
        examples=[KNOWN_IMAGE_SCHEDULERS.normal],
    )
    """The scheduler to use for the generation."""

    clip_skip: int | None = Field(
        default=None,
        examples=[-3, -2, -1, 1, 2, 3],
    )
    """The offset of layer numbers to skip. Be sure to check `clip_skip_representation` for the representation."""

    clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = Field(
        default=None,
    )
    """The representation of the clip skip. See `CLIP_SKIP_REPRESENTATION` for more information.

    Typically front-ends use positive values, while comfyui used the same value but negative.
    """

    denoising_strength: float | None = Field(
        default=None,
        ge=0,
        le=1,
        examples=[0.0, 0.5, 1.0],
    )
    """The denoising strength to use for the generation."""


class BasicImageGenerationParameters(BasicImageGenerationParametersTemplate):
    """Represents the common bare minimum parameters for an image generation."""

    model_config = ConfigDict(
        frozen=True,
    )

    prompt: str
    """The prompt to use for the generation."""

    height: int | None = Field(
        default=DEFAULT_BASELINE_RESOLUTION,
        multiple_of=64,
        ge=64,
        examples=[512, 768],
    )
    """The height to use for the generation."""
    width: int | None = Field(
        default=DEFAULT_BASELINE_RESOLUTION,
        multiple_of=64,
        ge=64,
        examples=[512, 768],
    )
    """The width to use for the generation."""

    clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = Field(
        default=CLIP_SKIP_REPRESENTATION.NEGATIVE_OFFSET,
    )
    """The representation of the clip skip. See `CLIP_SKIP_REPRESENTATION` for more information.

    Typically front-ends use positive values, while comfyui used the same value but negative.
    """


default_basic_image_generation_parameters = BasicImageGenerationParameters(
    prompt="EXAMPLE_PROMPT",
    model="EXAMPLE_MODEL",
    seed="1",
    height=DEFAULT_BASELINE_RESOLUTION,
    width=DEFAULT_BASELINE_RESOLUTION,
    steps=20,
    cfg_scale=7.0,
    sampler_name=KNOWN_IMAGE_SAMPLERS.k_lms,
    scheduler=KNOWN_IMAGE_SCHEDULERS.normal,
    clip_skip=1,
    denoising_strength=0.75,
)


class Image2ImageGenerationParameters(GenerationParameterComponentBase):
    """Represents the parameters for an image-to-image generation."""

    source_image: bytes | str | None
    """The source image to use for the generation."""
    source_mask: bytes | str | None
    """The source mask to use for the generation."""


class RemixImageEntry(GenerationParameterComponentBase):
    """Represents a special image entry for a generation."""

    image: bytes | str
    """The image data."""

    strength: float = 1.0
    """The weight to apply this image to the remix generation."""


class RemixGenerationParameters(GenerationParameterComponentBase):
    """Represents the parameters for a stable cascade remix generation."""

    source_image: bytes | str
    """The source image to use for the generation."""

    remix_images: list[RemixImageEntry]
    """The images to remix the source image with."""


class ControlnetGenerationParameters(GenerationParameterComponentBase):
    """Represents the parameters for a controlnet generation."""

    controlnet_type: KNOWN_IMAGE_CONTROLNETS | str
    """The type of controlnet to use for the generation."""

    source_image: bytes | str | None
    """The source image to use for the generation, if img2img."""
    control_map: bytes | str | None
    """The control map to use for the generation, if img2img."""

    return_control_map: bool = False
    """If true, return the control map created by the controlnet pre-processor."""


class HiresFixGenerationParameters(GenerationParameterComponentBase):
    """Represents the parameters for a high-resolution fix generation."""

    first_pass: BasicImageGenerationParameters
    second_pass: BasicImageGenerationParameters


class AuxModelEntry(GenerationParameterComponentBase):
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


class CustomWorkflowGenerationParameters(GenerationParameterComponentBase):
    """Represents the parameters for a custom workflow generation."""

    custom_workflow_name: KNOWN_IMAGE_WORKFLOWS | str
    """The name of the custom workflow to use for the generation."""
    custom_workflow_version: str | None = None
    """The version of the custom workflow to use for the generation. \
        If None, the latest version will be used. Defaults to None."""

    custom_parameters: dict[GENERATION_ID_TYPES, str] | None = None
    """The custom parameters to use for the generation. Defaults to None."""


GenerationParameterComponentBaseTypeVar = TypeVar(
    "GenerationParameterComponentBaseTypeVar",
    bound=GenerationParameterComponentBase,
)


class ImageGenerationParametersTemplate(ComposedParameterSetBase):
    """Represents the parameters for an image generation."""

    batch_size: int | None = Field(default=None, ge=1)
    """The number of images to generated batched (simultaneously). This is the `n_iter` parameter in ComfyUI"""

    tiling: bool | None = None
    """If true, the generation will be generated with seamless tiling."""

    source_processing: KNOWN_IMAGE_SOURCE_PROCESSING | str | None = None
    """txt2img, img2img, etc. See `KNOWN_IMAGE_SOURCE_PROCESSING` for more information."""

    base_params: BasicImageGenerationParameters | None = None
    """The base parameters for the generation."""

    _additional_params: dict[type[GenerationParameterComponentBase], GenerationParameterComponentBase] | None = None
    """Additional parameters for the generation.This can include parameters for img2img, remix, controlnet, hires fix,
    and custom workflows."""

    additional_params: list[GenerationParameterComponentBase] | None = None
    """Additional parameters for the generation. This can include parameters for img2img, remix, controlnet, hires fix,
    and custom workflows. The types of the parameters must be unique - you cannot have two
    Image2ImageGenerationParameters for example."""

    @model_validator(mode="after")
    def verify_additional_params(self: ImageGenerationParametersTemplate) -> ImageGenerationParametersTemplate:
        """Ensure that additional parameters are valid and set up the internal dictionary."""
        if not self.additional_params:
            self.additional_params = None
            self._additional_params = None
            return self

        if not isinstance(self.additional_params, list):
            raise TypeError("additional_params must be a list of GenerationParameterComponentBase instances.")

        self._additional_params = {}

        for param in self.additional_params:
            param_type = type(param)

            if param_type in self._additional_params:
                raise ValueError(f"Duplicate parameter type found: {param_type.__name__}.")

            self._additional_params[param_type] = param

        return self

    def _get_additional_param(
        self,
        param_type: type[GenerationParameterComponentBaseTypeVar],
    ) -> GenerationParameterComponentBaseTypeVar | None:
        """Get an additional parameter of the specified type."""
        if self._additional_params and param_type in self._additional_params:
            param = self._additional_params[param_type]
            if not isinstance(param, param_type):
                raise TypeError(f"{param_type.__name__} must be of type {param_type.__name__}.")
            return param
        return None

    @property
    def img2img_params(self) -> Image2ImageGenerationParameters | None:
        """If this is an img2img generation, the parameters specific to img2img."""
        return self._get_additional_param(Image2ImageGenerationParameters)

    @property
    def remix_params(self) -> RemixGenerationParameters | None:
        """If this is a remix generation, the parameters specific to remix."""
        return self._get_additional_param(RemixGenerationParameters)

    @property
    def controlnet_params(self) -> ControlnetGenerationParameters | None:
        """If this is a controlnet generation, the parameters specific to controlnet."""
        return self._get_additional_param(ControlnetGenerationParameters)

    @property
    def hires_fix_params(self) -> HiresFixGenerationParameters | None:
        """If this is a high-resolution fix generation, the parameters specific to high-resolution fix."""
        return self._get_additional_param(HiresFixGenerationParameters)

    @property
    def custom_workflow_params(self) -> CustomWorkflowGenerationParameters | None:
        """If this is a custom workflow generation, the parameters specific to custom workflow."""
        return self._get_additional_param(CustomWorkflowGenerationParameters)

    alchemy_params: AlchemyParameters | None = None
    """If alchemy is also requested, the parameters specific to those operations."""

    loras: list[LoRaEntry] | None = None
    """The LoRas to use for the generation."""
    tis: list[TIEntry] | None = None
    """The TIs to use for the generation."""

    @model_validator(mode="after")
    def verify_source_processing(self: ImageGenerationParametersTemplate) -> ImageGenerationParametersTemplate:
        """Ensure that the appropriate parameters are set based on the source processing type."""
        if self.source_processing in [
            KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
            KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
            KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
        ]:
            if self.img2img_params is None:
                raise ValueError("img2img_params must be provided for img2img source processing.")
        elif self.source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.remix and self.remix_params is None:
            raise ValueError("remix_params must be provided for remix source processing.")

        return self

    @override
    def get_number_expected_results(self: ImageGenerationParametersTemplate) -> int:
        """Return the number of expected results for this parameter set.

        Returns:
            int: The number of expected results.
        """
        return self.batch_size if self.batch_size is not None else 1


class ImageGenerationParameters(ImageGenerationParametersTemplate):
    """Represents the common bare-minimum parameters for an image generation."""

    generation_ids: list[GENERATION_ID_TYPES]
    """The generation IDs to assign to the resulting images."""

    base_params: BasicImageGenerationParameters
    """The base parameters for the generation."""

    batch_size: int | None = Field(default=1, ge=1)
    """The number of images to generated batched (simultaneously, not concurrently).
    This is the `n_iter` parameter in ComfyUI"""

    @model_validator(mode="after")
    def verify_id_count(self: ImageGenerationParameters) -> ImageGenerationParameters:
        """Ensure that at least one generation ID is provided."""
        if not self.generation_ids:
            raise ValueError("At least one generation ID must be provided.")

        if len(self.generation_ids) != self.batch_size:
            raise ValueError("The number of generation IDs must match the batch size.")

        return self


def image_parameters_to_feature_flags(
    parameters: ImageGenerationParametersTemplate,
) -> ImageGenerationFeatureFlags:
    """Create a feature flag object representing the features used in the parameters."""
    all_alchemy_forms = None
    if parameters.alchemy_params is not None and parameters.alchemy_params._all_alchemy_operations is not None:
        all_alchemy_forms = [x.form for x in parameters.alchemy_params._all_alchemy_operations if x.form is not None]

    baselines = (
        [parameters.base_params.model_baseline]
        if parameters.base_params and parameters.base_params.model_baseline
        else [KNOWN_IMAGE_GENERATION_BASELINE.infer]
    )

    hires_fix = parameters.hires_fix_params is not None

    tiling = bool(parameters.tiling)

    schedulers = []
    samplers = []

    if parameters.base_params is not None:
        if parameters.base_params.scheduler is not None:
            schedulers.append(parameters.base_params.scheduler)
        if parameters.base_params.sampler_name is not None:
            samplers.append(parameters.base_params.sampler_name)

    controlnets_feature_flags = (
        ControlnetFeatureFlags(
            controlnets=[parameters.controlnet_params.controlnet_type],
            image_is_control=parameters.controlnet_params.source_image is not None,
            return_control_map=parameters.controlnet_params.return_control_map,
        )
        if parameters.controlnet_params is not None
        else None
    )

    post_processing = all_alchemy_forms

    source_processing = [parameters.source_processing]

    workflows = (
        [parameters.custom_workflow_params.custom_workflow_name]
        if parameters.custom_workflow_params is not None
        else None
    )

    tis = [ti.source for ti in parameters.tis] if parameters.tis is not None else None
    loras = [lora.source for lora in parameters.loras] if parameters.loras is not None else None

    return ImageGenerationFeatureFlags(
        baselines=baselines,
        hires_fix=hires_fix,
        tiling=tiling,
        schedulers=schedulers,
        samplers=samplers,
        controlnets_feature_flags=controlnets_feature_flags,
        post_processing=post_processing,
        source_processing=source_processing,
        workflows=workflows,
        tis=tis,
        loras=loras,
    )
