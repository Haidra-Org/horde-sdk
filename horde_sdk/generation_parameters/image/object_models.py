from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import ConfigDict, Field, field_validator, model_validator

from horde_sdk.consts import ID_TYPES, get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.alchemy import AlchemyParameters
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.generation_parameters.generic import (
    CompositeParametersBase,
    GenerationParameterBaseModel,
    GenerationWithModelParameters,
)
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.image.constraints import KNOWN_SAMPLER_SOLVER_TYPES, SAMPLER_SOLVER_KNOB
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
from horde_sdk.generation_parameters.utils import (
    ResultIdAllocator,
    finalize_template_for_parameters,
    resolve_result_ids_from_payload,
)

DEFAULT_BASELINE_RESOLUTION: int = 512
"""The default assumed (single side) trained resolution for image generation models if unspecified."""
HIRES_FIX_DENOISE_STRENGTH_DEFAULT: float = 0.65
"""The default second-pass denoise strength for hires-fix generations."""


class ControlnetFeatureFlags(GenerationParameterBaseModel):
    """Represents required or supported ControlNet render features."""

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
    """Represents portable image render features that are required or supported.

    A generation uses this model to describe requirements. A worker advertises the same fields as
    supported values inside `ImageWorkerFeatureFlags`. Compatibility is directional: every requested
    value must appear in the worker's advertised set, while a false, empty, or absent request field
    adds no requirement.
    """

    baselines: list[KNOWN_IMAGE_GENERATION_BASELINE | str] = Field(
        examples=[
            [KNOWN_IMAGE_GENERATION_BASELINE.infer],
            [KNOWN_IMAGE_GENERATION_BASELINE.infer, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1],
        ],
    )
    """The baselines required by a generation or supported by a worker.

    If `infer`, the worker will attempt to infer the model type from the model name.
    """

    clip_skip: bool = Field(default=False)
    """Whether clip skipping is required or supported."""

    hires_fix: bool = Field(default=False)
    """Whether hires fix is required or supported."""

    tiling: bool = Field(default=False)
    """Whether seamless tiling is required or supported."""

    schedulers: list[KNOWN_IMAGE_SCHEDULERS | str] = Field(
        examples=[
            [KNOWN_IMAGE_SCHEDULERS.normal],
            [KNOWN_IMAGE_SCHEDULERS.normal, KNOWN_IMAGE_SCHEDULERS.simple],
        ],
    )
    """The schedulers required or supported."""

    samplers: list[KNOWN_IMAGE_SAMPLERS | str] = Field(
        examples=[
            [KNOWN_IMAGE_SAMPLERS.k_euler],
            [KNOWN_IMAGE_SAMPLERS.k_lms, KNOWN_IMAGE_SAMPLERS.k_euler],
        ],
    )
    """The samplers required or supported."""

    sampler_solver_knobs: list[SAMPLER_SOLVER_KNOB | str] | None = Field(default=None)
    """The per-request sampler solver knobs required or supported."""

    flow_shift: bool = Field(default=False)
    """Whether a model-specific flow shift is required or supported."""

    transparent: bool = Field(default=False)
    """Whether transparent image generation is required or supported."""

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
    """The ControlNet features required or supported."""

    post_processing: list[KNOWN_ALCHEMY_TYPES | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus],
            [KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus, KNOWN_ALCHEMY_TYPES.GFPGAN],
        ],
    )
    """The exact post-processing operations required or supported."""

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
    """The source-processing methods required or supported."""

    workflows: list[KNOWN_IMAGE_WORKFLOWS | str] | None = Field(
        default=None,
        examples=[
            [KNOWN_IMAGE_WORKFLOWS.qr_code],
        ],
    )
    """The workflows required or supported."""

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


class BasicImageGenerationParametersTemplate(GenerationWithModelParameters):
    """Represents the common parameters for an image generation."""

    prompt: str | None = None
    """The prompt to use for the generation."""
    negative_prompt: str | None = None
    """The negative prompt to use for the generation, if any.

    Dispatch converters are responsible for splitting any combined prompt encoding
    (such as AI-Horde's ``###`` separator) before constructing these parameters.
    """
    seed: str | None = None
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

    sampler_eta: float | None = Field(
        default=None,
        ge=0,
        examples=[0.0, 1.0],
    )
    """The stochastic strength of the solver. Unset leaves the solver's own default in place.

    Which solvers accept this, and over what range, is stated in
    [`SAMPLER_CONSTRAINTS`][horde_sdk.generation_parameters.image.constraints.SAMPLER_CONSTRAINTS].
    """

    sampler_s_noise: float | None = Field(
        default=None,
        ge=0,
        examples=[1.0],
    )
    """The multiplier on the noise the solver adds per step. Unset leaves the solver's own default."""

    sampler_s_churn: float | None = Field(
        default=None,
        ge=0,
        examples=[0.0],
    )
    """The extra noise injected across the run, spread over the steps inside the churn window."""

    sampler_s_tmin: float | None = Field(
        default=None,
        ge=0,
        examples=[0.0],
    )
    """The lower sigma bound of the churn window. Only meaningful alongside `sampler_s_churn`."""

    sampler_s_tmax: float | None = Field(
        default=None,
        ge=0,
        examples=[999.0],
    )
    """The upper sigma bound of the churn window. Only meaningful alongside `sampler_s_churn`."""

    sampler_solver_type: KNOWN_SAMPLER_SOLVER_TYPES | str | None = Field(
        default=None,
        examples=[KNOWN_SAMPLER_SOLVER_TYPES.midpoint],
    )
    """Which correction the solver applies. The accepted vocabulary differs per sampler."""

    sampler_order: int | None = Field(
        default=None,
        ge=1,
        examples=[3, 4],
    )
    """The order of the solver. The accepted range is per-sampler and narrower than this bound."""

    flow_shift: float | None = Field(
        default=None,
        ge=0,
        examples=[3.0],
    )
    """The timestep shift applied to a flow-matching model. Unset leaves the model's own default."""

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

    tiling: bool | None = None
    """If true, the generation will be generated with seamless tiling."""

    transparent: bool | None = None
    """If true, the generation will be generated with a transparent background (layer diffusion)."""


class BasicImageGenerationParameters(BasicImageGenerationParametersTemplate):
    """Represents the common bare minimum parameters for an image generation."""

    model_config = ConfigDict(
        frozen=True,
        from_attributes=True,
    )

    model: str
    """The model to use for the generation."""

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
    model_baseline="infer",
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


class Image2ImageGenerationParameters(GenerationParameterBaseModel):
    """Represents the parameters for an image-to-image generation."""

    source_image: bytes | str | None
    """The source image to use for the generation."""
    source_mask: bytes | str | None
    """The source mask to use for the generation."""


class RemixImageEntry(GenerationParameterBaseModel):
    """Represents a special image entry for a generation."""

    image: bytes | str
    """The image data."""

    strength: float = 1.0
    """The weight to apply this image to the remix generation."""


class RemixGenerationParameters(GenerationParameterBaseModel):
    """Represents the parameters for a stable cascade remix generation."""

    source_image: bytes | str
    """The source image to use for the generation."""

    remix_images: list[RemixImageEntry]
    """The images to remix the source image with."""


class ControlnetGenerationParameters(GenerationParameterBaseModel):
    """Represents the parameters for a controlnet generation."""

    controlnet_type: KNOWN_IMAGE_CONTROLNETS | str
    """The type of controlnet to use for the generation."""

    source_image: bytes | str | None
    """The source image to use for the generation, if img2img."""
    control_map: bytes | str | None
    """The control map to use for the generation, if img2img."""

    return_control_map: bool = False
    """If true, return the control map created by the controlnet pre-processor."""


class HiresFixGenerationParameters(GenerationParameterBaseModel):
    """Represents the parameters for a high-resolution fix generation."""

    first_pass: BasicImageGenerationParameters
    second_pass: BasicImageGenerationParameters


class AuxModelEntry(GenerationParameterBaseModel):
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


class ExtraTextEntry(GenerationParameterBaseModel):
    """Represents a single extra text input consumed by a custom workflow."""

    text: str
    """The text content."""

    reference: str | None = None
    """A reference identifying how the workflow should use this text."""


class CustomWorkflowGenerationParameters(GenerationParameterBaseModel):
    """Represents the parameters for a custom workflow generation."""

    custom_workflow_name: KNOWN_IMAGE_WORKFLOWS | str
    """The name of the custom workflow to use for the generation."""
    custom_workflow_version: str | None = None
    """The version of the custom workflow to use for the generation. \
        If None, the latest version will be used. Defaults to None."""

    custom_parameters: dict[ID_TYPES, str] | None = None
    """The custom parameters to use for the generation. Defaults to None."""

    extra_texts: list[ExtraTextEntry] | None = None
    """Extra text inputs consumed by the workflow (for example, the text encoded by a QR code workflow)."""


class ImageGenerationComponentContainer(GenerationParameterBaseModel):
    """Container for optional image generation components.

    This container holds auxiliary components for image generation such as LoRa entries,
    Textual Inversion entries, ControlNet parameters, and more. It uses a simple list
    that naturally supports multiple instances of the same component type.
    """

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        from_attributes=True,
    )

    components: list[
        Image2ImageGenerationParameters
        | RemixGenerationParameters
        | ControlnetGenerationParameters
        | HiresFixGenerationParameters
        | LoRaEntry
        | TIEntry
        | CustomWorkflowGenerationParameters
    ] = Field(default_factory=list)
    """The list of generation components."""

    def add(
        self,
        component: (
            Image2ImageGenerationParameters
            | RemixGenerationParameters
            | ControlnetGenerationParameters
            | HiresFixGenerationParameters
            | LoRaEntry
            | TIEntry
            | CustomWorkflowGenerationParameters
        ),
    ) -> None:
        """Add a component to the container.

        Args:
            component: The component to add.
        """
        self.components.append(component)

    def add_all(
        self,
        components: list[
            Image2ImageGenerationParameters
            | RemixGenerationParameters
            | ControlnetGenerationParameters
            | HiresFixGenerationParameters
            | LoRaEntry
            | TIEntry
            | CustomWorkflowGenerationParameters
        ],
    ) -> None:
        """Add multiple components to the container.

        Args:
            components: The list of components to add.
        """
        self.components.extend(components)

    @property
    def image2image_params(self) -> Image2ImageGenerationParameters | None:
        """Get the image-to-image parameters if they exist."""
        for component in self.components:
            if isinstance(component, Image2ImageGenerationParameters):
                return component
        return None

    @property
    def remix_params(self) -> RemixGenerationParameters | None:
        """Get the remix parameters if they exist."""
        for component in self.components:
            if isinstance(component, RemixGenerationParameters):
                return component
        return None

    @property
    def controlnet_params(self) -> ControlnetGenerationParameters | None:
        """Get the controlnet parameters if they exist."""
        for component in self.components:
            if isinstance(component, ControlnetGenerationParameters):
                return component
        return None

    @property
    def hires_fix_params(self) -> HiresFixGenerationParameters | None:
        """Get the hires fix parameters if they exist."""
        for component in self.components:
            if isinstance(component, HiresFixGenerationParameters):
                return component
        return None

    @property
    def lora_entries(self) -> list[LoRaEntry]:
        """Get all LoRa entries."""
        return [c for c in self.components if isinstance(c, LoRaEntry)]

    @property
    def ti_entries(self) -> list[TIEntry]:
        """Get all Textual Inversion entries."""
        return [c for c in self.components if isinstance(c, TIEntry)]

    @property
    def custom_workflow_entries(self) -> list[CustomWorkflowGenerationParameters]:
        """Get all custom workflow entries."""
        return [c for c in self.components if isinstance(c, CustomWorkflowGenerationParameters)]

    @property
    def lora_params(self) -> list[LoRaEntry]:
        """Get all LoRa entries.

        Deprecated: Use lora_entries instead. This property returns a plain list instead of LoRaEntries wrapper.
        """
        return self.lora_entries

    @property
    def ti_params(self) -> list[TIEntry]:
        """Get all Textual Inversion entries.

        Deprecated: Use ti_entries instead. This property returns a plain list instead of TIEntries wrapper.
        """
        return self.ti_entries

    @property
    def custom_workflows_params(self) -> list[CustomWorkflowGenerationParameters]:
        """Get all custom workflow entries.

        Deprecated: Use custom_workflow_entries instead. This property returns a plain list instead of
        CustomWorkflows wrapper.
        """
        return self.custom_workflow_entries


class ImageGenerationParametersTemplate(CompositeParametersBase):
    """Represents the parameters for an image generation."""

    batch_size: int | None = Field(default=None, ge=1)
    """The number of images to generated batched (simultaneously). This is the `n_iter` parameter in ComfyUI"""

    source_processing: KNOWN_IMAGE_SOURCE_PROCESSING | str | None = None
    """txt2img, img2img, etc. See `KNOWN_IMAGE_SOURCE_PROCESSING` for more information."""

    base_params: BasicImageGenerationParametersTemplate | None = None
    """The base parameters for the generation."""

    additional_params: ImageGenerationComponentContainer | None = None
    """Additional parameters for the generation. This can include parameters for img2img, remix, controlnet, hires fix,
    and custom workflows."""

    alchemy_params: AlchemyParameters | None = None
    """If alchemy is also requested, the parameters specific to those operations."""

    @model_validator(mode="after")
    def verify_source_processing(self: ImageGenerationParametersTemplate) -> ImageGenerationParametersTemplate:
        """Ensure that the appropriate parameters are set based on the source processing type."""
        if self.source_processing in [
            KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
            KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
            KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
        ]:
            if self.additional_params is None:
                raise ValueError("additional_params must be provided for img2img or inpainting source processing.")

            if self.additional_params.image2image_params is None:
                raise ValueError("img2img_params must be provided for img2img source processing.")
        elif self.source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.remix:
            if self.additional_params is None:
                raise ValueError("additional_params must be provided for remix source processing.")

            if self.additional_params.remix_params is None:
                raise ValueError("remix_params must be provided for remix source processing.")

        return self

    @override
    def get_number_expected_results(self: ImageGenerationParametersTemplate) -> int:
        """Return the number of expected results for this parameter set.

        Returns:
            int: The number of expected results.
        """
        return self.batch_size if self.batch_size is not None else 1

    def to_parameters(
        self,
        *,
        base_param_updates: BasicImageGenerationParametersTemplate | None = None,
        additional_param_updates: ImageGenerationComponentContainer | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "image",
    ) -> ImageGenerationParameters:
        """Convert this template into concrete image generation parameters."""
        base_params = self.base_params
        if base_params is None:
            raise ValueError("Image generation templates must define base_params before conversion.")

        overrides: dict[str, object] | None = None
        if base_param_updates:
            overrides = {
                "base_params": base_params.model_copy(update=base_param_updates.model_dump(exclude_none=True)),
            }

        if additional_param_updates:
            if overrides is None:
                overrides = {}
            if not self.additional_params:
                raise ValueError("additional_params must be defined before applying updates.")
            overrides["additional_params"] = self.additional_params.model_copy(update=dict(additional_param_updates))

        finalization = finalize_template_for_parameters(
            self,
            overrides=overrides,
            exclude_none=False,
            fingerprint_exclude_fields=("result_ids",),
        )

        finalized_template = finalization.template
        resolved_base_params = finalized_template.base_params
        if resolved_base_params is None:
            raise ValueError("Image generation templates must define base_params before conversion.")

        batch_size = finalized_template.batch_size or 1

        resolved_result_ids = resolve_result_ids_from_payload(
            explicit_ids=result_ids,
            payload_value=finalization.payload.get("result_ids"),
            count=batch_size,
            allocator=allocator,
            seed=seed,
            fingerprint=finalization.fingerprint,
        )

        concrete_base_params = BasicImageGenerationParameters.model_validate(
            resolved_base_params,
            from_attributes=True,
        )

        resolved_additional_params = (
            finalized_template.additional_params
            if finalized_template.additional_params is not None
            else ImageGenerationComponentContainer()
        )

        parameter_payload = finalized_template.model_copy(
            update={
                "base_params": concrete_base_params,
                "result_ids": resolved_result_ids,
                "additional_params": resolved_additional_params,
                "batch_size": batch_size,
            },
        )

        return ImageGenerationParameters.model_validate(
            parameter_payload,
            from_attributes=True,
        )


class ImageGenerationParameters(ImageGenerationParametersTemplate):
    """Represents the common bare-minimum parameters for an image generation."""

    result_ids: list[ID_TYPES]
    """The IDs to assign to the resulting images."""

    base_params: BasicImageGenerationParameters
    """The base parameters for the generation."""

    additional_params: ImageGenerationComponentContainer = Field(default_factory=ImageGenerationComponentContainer)
    """Additional parameters for the generation. This can include parameters for img2img, remix, controlnet, hires fix,
    and custom workflows."""

    batch_size: int | None = Field(default=1, ge=1)
    """The number of images to generated batched (simultaneously, not concurrently).
    This is the `n_iter` parameter in ComfyUI"""

    @model_validator(mode="after")
    def verify_id_count(self: ImageGenerationParameters) -> ImageGenerationParameters:
        """Ensure that at least one generation ID is provided."""
        if not self.result_ids:
            raise ValueError("At least one generation ID must be provided.")

        if len(self.result_ids) != self.batch_size:
            raise ValueError("The number of generation IDs must match the batch size.")

        return self


def sampler_solver_knobs_from_values(
    *,
    sampler_eta: float | None,
    sampler_s_noise: float | None,
    sampler_s_churn: float | None,
    sampler_s_tmin: float | None,
    sampler_s_tmax: float | None,
    sampler_solver_type: KNOWN_SAMPLER_SOLVER_TYPES | str | None,
    sampler_order: int | None,
) -> list[SAMPLER_SOLVER_KNOB]:
    """Return the solver-knob capabilities required by concrete parameter values.

    Args:
        sampler_eta: Requested stochastic strength.
        sampler_s_noise: Requested noise multiplier.
        sampler_s_churn: Requested churn strength.
        sampler_s_tmin: Requested lower churn bound.
        sampler_s_tmax: Requested upper churn bound.
        sampler_solver_type: Requested second-order correction.
        sampler_order: Requested solver order.

    Returns:
        The canonical knob identifiers for every explicitly supplied value.
    """
    requested_knobs: list[SAMPLER_SOLVER_KNOB] = []
    if sampler_eta is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.eta)
    if sampler_s_noise is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.s_noise)
    if sampler_s_churn is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.s_churn)
    if sampler_s_tmin is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.s_tmin)
    if sampler_s_tmax is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.s_tmax)
    if sampler_solver_type is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.solver_type)
    if sampler_order is not None:
        requested_knobs.append(SAMPLER_SOLVER_KNOB.order)
    return requested_knobs


def image_parameters_to_feature_flags(
    parameters: ImageGenerationParametersTemplate,
) -> ImageGenerationFeatureFlags:
    """Create the canonical feature requirements used by image parameters.

    Args:
        parameters: Backend-agnostic image parameters to inspect.

    Returns:
        The exact portable render features required to execute the parameters.
    """
    all_alchemy_operations = None
    if parameters.alchemy_params is not None and parameters.alchemy_params._all_alchemy_operations is not None:
        all_alchemy_operations = [
            operation.operation_name for operation in parameters.alchemy_params._all_alchemy_operations
        ]

    baselines: list[KNOWN_IMAGE_GENERATION_BASELINE | str]
    if parameters.base_params and parameters.base_params.model_baseline is not None:
        baselines = [parameters.base_params.model_baseline]
    else:
        baselines = [KNOWN_IMAGE_GENERATION_BASELINE.infer]

    schedulers = []
    samplers = []
    sampler_solver_knobs: list[SAMPLER_SOLVER_KNOB] = []

    if parameters.base_params is not None:
        if parameters.base_params.scheduler is not None:
            schedulers.append(parameters.base_params.scheduler)
        if parameters.base_params.sampler_name is not None:
            samplers.append(parameters.base_params.sampler_name)
        sampler_solver_knobs = sampler_solver_knobs_from_values(
            sampler_eta=parameters.base_params.sampler_eta,
            sampler_s_noise=parameters.base_params.sampler_s_noise,
            sampler_s_churn=parameters.base_params.sampler_s_churn,
            sampler_s_tmin=parameters.base_params.sampler_s_tmin,
            sampler_s_tmax=parameters.base_params.sampler_s_tmax,
            sampler_solver_type=parameters.base_params.sampler_solver_type,
            sampler_order=parameters.base_params.sampler_order,
        )

    source_processing = [parameters.source_processing] if parameters.source_processing is not None else []

    post_processing = all_alchemy_operations

    tiling = bool(parameters.base_params and parameters.base_params.tiling)
    flow_shift = bool(parameters.base_params and parameters.base_params.flow_shift is not None)
    transparent = bool(parameters.base_params and parameters.base_params.transparent)
    clip_skip = bool(
        parameters.base_params
        and parameters.base_params.clip_skip is not None
        and abs(parameters.base_params.clip_skip) > 1
    )

    hires_fix = False
    controlnets_feature_flags = None
    workflows: list[KNOWN_IMAGE_WORKFLOWS | str] | None = None
    tis: list[KNOWN_AUX_MODEL_SOURCE | str] | None = None
    loras: list[KNOWN_AUX_MODEL_SOURCE | str] | None = None
    extra_texts = False
    extra_source_images = False

    if parameters.additional_params:
        hires_fix = parameters.additional_params.hires_fix_params is not None

        controlnets_feature_flags = (
            ControlnetFeatureFlags(
                controlnets=[parameters.additional_params.controlnet_params.controlnet_type],
                image_is_control=parameters.additional_params.controlnet_params.control_map is not None,
                return_control_map=parameters.additional_params.controlnet_params.return_control_map,
            )
            if parameters.additional_params.controlnet_params is not None
            else None
        )

        if parameters.additional_params.custom_workflow_entries:
            workflow_names = [
                workflow.custom_workflow_name for workflow in parameters.additional_params.custom_workflow_entries
            ]
            workflows = workflow_names or None
            extra_texts = any(
                workflow.extra_texts for workflow in parameters.additional_params.custom_workflow_entries
            )

        if parameters.additional_params.ti_entries:
            ti_sources = list(dict.fromkeys(ti.source for ti in parameters.additional_params.ti_entries))
            tis = ti_sources or None

        if parameters.additional_params.lora_entries:
            lora_sources = list(dict.fromkeys(lora.source for lora in parameters.additional_params.lora_entries))
            loras = lora_sources or None

        remix_parameters = parameters.additional_params.remix_params
        extra_source_images = bool(remix_parameters and remix_parameters.remix_images)

    return ImageGenerationFeatureFlags(
        extra_texts=extra_texts,
        extra_source_images=extra_source_images,
        baselines=baselines,
        clip_skip=clip_skip,
        hires_fix=hires_fix,
        tiling=tiling,
        schedulers=schedulers,
        samplers=samplers,
        sampler_solver_knobs=sampler_solver_knobs or None,
        flow_shift=flow_shift,
        transparent=transparent,
        controlnets_feature_flags=controlnets_feature_flags,
        post_processing=post_processing,
        source_processing=source_processing,
        workflows=workflows,
        tis=tis,
        loras=loras,
    )


def _ordered_feature_union[FeatureValue](
    feature_collections: Sequence[Sequence[FeatureValue] | None],
) -> list[FeatureValue]:
    """Return all feature values once, preserving their first advertised order."""
    union: list[FeatureValue] = []
    for feature_collection in feature_collections:
        for feature_value in feature_collection or []:
            if feature_value not in union:
                union.append(feature_value)
    return union


def _ordered_feature_intersection[FeatureValue](
    feature_collections: Sequence[Sequence[FeatureValue] | None],
) -> list[FeatureValue]:
    """Return common feature values in the first collection's order."""
    if not feature_collections or not feature_collections[0]:
        return []
    return [
        feature_value
        for feature_value in feature_collections[0]
        if all(
            feature_collection is not None and feature_value in feature_collection
            for feature_collection in feature_collections[1:]
        )
    ]


def _union_controlnet_feature_flags(
    feature_sets: Sequence[ImageGenerationFeatureFlags],
) -> ControlnetFeatureFlags | None:
    """Return the union of advertised ControlNet features."""
    controlnet_features = [
        feature_set.controlnets_feature_flags
        for feature_set in feature_sets
        if feature_set.controlnets_feature_flags is not None
    ]
    if not controlnet_features:
        return None
    return ControlnetFeatureFlags(
        controlnets=_ordered_feature_union([features.controlnets for features in controlnet_features]),
        image_is_control=any(features.image_is_control for features in controlnet_features),
        return_control_map=any(features.return_control_map for features in controlnet_features),
    )


def _intersect_controlnet_feature_flags(
    feature_sets: Sequence[ImageGenerationFeatureFlags],
) -> ControlnetFeatureFlags | None:
    """Return the intersection of advertised ControlNet features."""
    controlnet_features = [feature_set.controlnets_feature_flags for feature_set in feature_sets]
    if any(features is None for features in controlnet_features):
        return None

    concrete_features = [features for features in controlnet_features if features is not None]
    common_controlnets = _ordered_feature_intersection([features.controlnets for features in concrete_features])
    if not common_controlnets:
        return None
    return ControlnetFeatureFlags(
        controlnets=common_controlnets,
        image_is_control=all(features.image_is_control for features in concrete_features),
        return_control_map=all(features.return_control_map for features in concrete_features),
    )


def union_image_generation_feature_flags(
    feature_sets: Sequence[ImageGenerationFeatureFlags],
) -> ImageGenerationFeatureFlags:
    """Return the axis-wise union of canonical image feature sets.

    This operation combines each field independently. It does not preserve correlations between fields;
    callers must not treat a heterogeneous union as proof that one worker can execute every combination.
    Resource limits, model residency, queue state, and operator policy also remain separate constraints.

    Args:
        feature_sets: Canonical feature sets to combine.

    Returns:
        One canonical feature set containing every advertised feature.

    Raises:
        ValueError: If no feature sets are supplied.
    """
    if not feature_sets:
        raise ValueError("At least one image generation feature set is required.")

    return ImageGenerationFeatureFlags(
        extra_texts=any(feature_set.extra_texts for feature_set in feature_sets),
        extra_source_images=any(feature_set.extra_source_images for feature_set in feature_sets),
        baselines=_ordered_feature_union([feature_set.baselines for feature_set in feature_sets]),
        clip_skip=any(feature_set.clip_skip for feature_set in feature_sets),
        hires_fix=any(feature_set.hires_fix for feature_set in feature_sets),
        tiling=any(feature_set.tiling for feature_set in feature_sets),
        schedulers=_ordered_feature_union([feature_set.schedulers for feature_set in feature_sets]),
        samplers=_ordered_feature_union([feature_set.samplers for feature_set in feature_sets]),
        sampler_solver_knobs=(
            _ordered_feature_union([feature_set.sampler_solver_knobs for feature_set in feature_sets]) or None
        ),
        flow_shift=any(feature_set.flow_shift for feature_set in feature_sets),
        transparent=any(feature_set.transparent for feature_set in feature_sets),
        controlnets_feature_flags=_union_controlnet_feature_flags(feature_sets),
        post_processing=(
            _ordered_feature_union([feature_set.post_processing for feature_set in feature_sets]) or None
        ),
        source_processing=_ordered_feature_union([feature_set.source_processing for feature_set in feature_sets]),
        workflows=_ordered_feature_union([feature_set.workflows for feature_set in feature_sets]) or None,
        tis=_ordered_feature_union([feature_set.tis for feature_set in feature_sets]) or None,
        loras=_ordered_feature_union([feature_set.loras for feature_set in feature_sets]) or None,
    )


def intersect_image_generation_feature_flags(
    feature_sets: Sequence[ImageGenerationFeatureFlags],
) -> ImageGenerationFeatureFlags:
    """Return the intersection of canonical image feature sets.

    Args:
        feature_sets: Canonical feature sets to intersect.

    Returns:
        One canonical feature set containing only features every input advertises.

    Raises:
        ValueError: If no feature sets are supplied or they share no generation baseline.
    """
    if not feature_sets:
        raise ValueError("At least one image generation feature set is required.")

    common_baselines = _ordered_feature_intersection([feature_set.baselines for feature_set in feature_sets])
    if not common_baselines:
        raise ValueError("Image generation feature sets must share at least one baseline.")

    return ImageGenerationFeatureFlags(
        extra_texts=all(feature_set.extra_texts for feature_set in feature_sets),
        extra_source_images=all(feature_set.extra_source_images for feature_set in feature_sets),
        baselines=common_baselines,
        clip_skip=all(feature_set.clip_skip for feature_set in feature_sets),
        hires_fix=all(feature_set.hires_fix for feature_set in feature_sets),
        tiling=all(feature_set.tiling for feature_set in feature_sets),
        schedulers=_ordered_feature_intersection([feature_set.schedulers for feature_set in feature_sets]),
        samplers=_ordered_feature_intersection([feature_set.samplers for feature_set in feature_sets]),
        sampler_solver_knobs=(
            _ordered_feature_intersection([feature_set.sampler_solver_knobs for feature_set in feature_sets]) or None
        ),
        flow_shift=all(feature_set.flow_shift for feature_set in feature_sets),
        transparent=all(feature_set.transparent for feature_set in feature_sets),
        controlnets_feature_flags=_intersect_controlnet_feature_flags(feature_sets),
        post_processing=(
            _ordered_feature_intersection([feature_set.post_processing for feature_set in feature_sets]) or None
        ),
        source_processing=_ordered_feature_intersection(
            [feature_set.source_processing for feature_set in feature_sets],
        ),
        workflows=_ordered_feature_intersection([feature_set.workflows for feature_set in feature_sets]) or None,
        tis=_ordered_feature_intersection([feature_set.tis for feature_set in feature_sets]) or None,
        loras=_ordered_feature_intersection([feature_set.loras for feature_set in feature_sets]) or None,
    )
