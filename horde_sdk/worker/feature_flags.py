from abc import ABC, abstractmethod
from enum import auto
from typing import TypeVar, override

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from loguru import logger
from pydantic import BaseModel, Field
from strenum import StrEnum

from horde_sdk import get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.alchemy.consts import (
    is_caption_form,
    is_facefixer_form,
    is_interrogator_form,
    is_nsfw_detector_form,
    is_upscaler_form,
)
from horde_sdk.generation_parameters.alchemy.object_models import AlchemyFeatureFlags
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.image.consts import (
    CLIP_SKIP_REPRESENTATION,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
)
from horde_sdk.generation_parameters.image.object_models import ImageGenerationFeatureFlags

ReasonTypeVar = TypeVar("ReasonTypeVar", bound=str)


class RESULT_RETURN_METHOD(StrEnum):
    """The method of returning results from a worker."""

    base64_post_back = auto()
    """Base64 post back in the 'job completed' message."""

    base64_post_back_with_url = auto()
    """Base64 post back to a given URL without results in the 'job completed' message."""

    byte_stream = auto()
    """Byte stream to a given URL without results in the 'job completed' message."""

    local_write_to_file = auto()
    """Can write to the local filesystem for jobs originating locally or within a closed environment."""


class WorkerFeatureFlags[ReasonTypeVar: str](ABC, BaseModel):
    """Feature flags for a worker."""

    model_config = get_default_frozen_model_config_dict()

    supported_result_return_methods: list[RESULT_RETURN_METHOD] = Field(default_factory=list)
    """The methods of returning results supported by the worker."""

    supports_threads: bool = Field(default=False)
    """Whether the worker supports threading."""

    def is_capable_of_features(self, features: GenerationFeatureFlags) -> bool:
        """Check if the worker is capable of handling the requested features.

        Args:
            features (GenerationFeatureFlags): The features to check.

        Returns:
            bool: True if the worker is capable of handling the requested features, False otherwise.
        """
        return not self.reasons_not_capable_of_features(features)

    @abstractmethod
    def get_not_capable_reason_type(self) -> type[ReasonTypeVar]:
        """Return the type of the reason for not being capable of handling the requested features.

        Returns:
            type[ReasonTypeVar]: The (python) type of the reason for not being capable of handling the requested
            features.
        """

    @abstractmethod
    def reasons_not_capable_of_features(
        self,
        features: GenerationFeatureFlags,
    ) -> list[ReasonTypeVar] | None:
        """Return a list of reasons why the worker is not capable of handling the requested features.

        Args:
            features (GenerationFeatureFlags): The features to check.

        Returns:
            list[str] | None: A list of reasons why the worker is not capable of handling the requested features,
            or None if the worker is capable.
        """


class PerBaselineFeatureFlags(BaseModel):
    """Feature flags for a worker per baseline."""

    model_config = get_default_frozen_model_config_dict()

    schedulers_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, list[KNOWN_IMAGE_SCHEDULERS | str]] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [
                    KNOWN_IMAGE_SCHEDULERS.simple,
                    KNOWN_IMAGE_SCHEDULERS.normal,
                    KNOWN_IMAGE_SCHEDULERS.exponential,
                ],
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: [
                    KNOWN_IMAGE_SCHEDULERS.simple,
                ],
            },
        ],
    )
    """If set, the supported schedulers for each baseline. If unset, it is assumed that all baselines
    support all schedulers."""

    samplers_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, list[KNOWN_IMAGE_SAMPLERS | str]] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [
                    KNOWN_IMAGE_SAMPLERS.k_lms,
                    KNOWN_IMAGE_SAMPLERS.k_dpm_2,
                    KNOWN_IMAGE_SAMPLERS.k_euler,
                ],
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: [
                    KNOWN_IMAGE_SAMPLERS.k_lms,
                ],
            },
        ],
    )
    """If set, the supported samplers for each baseline. If unset, it is assumed that all baselines
    support all samplers."""

    tiling_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: False,
            },
        ],
    )
    """If set, the supported tiling for each baseline. If unset, it is assumed that all baselines
    support tiling."""

    hires_fix_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: True,
                KNOWN_IMAGE_GENERATION_BASELINE.flux_1: False,
            },
        ],
    )
    """If set, the supported hires fix for each baseline. If unset, it is assumed that all baselines
    support hires fix."""

    controlnet_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: False,
            },
        ],
    )
    """If set, support for controlnet for each baseline. If unset, it is assumed that all baselines
    support controlnets."""

    tis_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: False,
            },
        ],
    )
    """If set, support for TIs for each baseline. If unset, it is assumed that all baselines support
    TIs."""

    loras_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: False,
            },
        ],
    )
    """If set, support for Loras for each baseline. If unset, it is assumed that all baselines
    support Loras."""


class IMAGE_WORKER_NOT_CAPABLE_REASON(StrEnum):
    """Reasons why a worker is not capable of handling a request."""

    clip_skip = auto()
    """The worker does not support clip skip."""

    samplers = auto()
    """The worker does not support the requested samplers."""

    schedulers = auto()
    """The worker does not support the requested schedulers."""

    tiling = auto()
    """The worker does not support tiling."""

    hires_fix = auto()
    """The worker does not support hires fix."""

    controlnets = auto()
    """The worker does not support controlnets."""

    tis = auto()
    """The worker does not support TIs."""

    loras = auto()
    """The worker does not support Loras."""

    extra_texts = auto()
    """The worker does not support extra texts."""

    extra_source_images = auto()
    """The worker does not support extra source images."""

    unsupported_baseline = auto()
    """The worker does not support the requested baseline."""


class ImageWorkerFeatureFlags(WorkerFeatureFlags[IMAGE_WORKER_NOT_CAPABLE_REASON]):
    """Feature flags for an image worker."""

    image_generation_feature_flags: ImageGenerationFeatureFlags
    """The image generation feature flags for the worker."""

    per_baseline_feature_flags: PerBaselineFeatureFlags | None = None
    """The per baseline feature flags for the worker. This includes the supported schedulers and
    samplers for each baseline."""

    backend_clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = None
    """The clip skip representation supported."""

    @override
    def get_not_capable_reason_type(self) -> type[IMAGE_WORKER_NOT_CAPABLE_REASON]:
        return IMAGE_WORKER_NOT_CAPABLE_REASON

    @override
    def reasons_not_capable_of_features(
        self,
        request: GenerationFeatureFlags,
    ) -> list[IMAGE_WORKER_NOT_CAPABLE_REASON] | None:
        """Return a list of reasons why a worker is not capable of handling a request."""
        if not isinstance(request, ImageGenerationFeatureFlags):
            logger.debug(f"Request is not an ImageGenerationFeatureFlags instance. Request type: {type(request)}")
            return None

        reasons = []

        if request.clip_skip and not self.image_generation_feature_flags.clip_skip:
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.clip_skip)

        if not self.worker_supports_requested_samplers(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.samplers)

        if not self.worker_supports_requested_schedulers(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.schedulers)

        if not self.worker_supports_requested_tiling(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.tiling)

        if not self.worker_supports_requested_hires_fix(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.hires_fix)

        if not self.worker_supports_requested_controlnets(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.controlnets)

        if not self.worker_supports_requested_tis(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.tis)

        if not self.worker_supports_requested_loras(request):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.loras)

        if request.extra_texts and not self.image_generation_feature_flags.extra_texts:
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.extra_texts)

        if request.extra_source_images and not self.image_generation_feature_flags.extra_source_images:
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.extra_source_images)

        if (
            request.baselines
            and self.image_generation_feature_flags.baselines
            and (not any(baseline in self.image_generation_feature_flags.baselines for baseline in request.baselines))
        ):
            reasons.append(IMAGE_WORKER_NOT_CAPABLE_REASON.unsupported_baseline)

        return reasons if reasons else None

    def worker_supports_requested_samplers(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports the samplers requested."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.samplers_map:
            for baseline in request.baselines or []:
                if any(
                    sampler not in self.per_baseline_feature_flags.samplers_map.get(baseline, [])
                    for sampler in request.samplers
                ):
                    return False
        else:
            if any(sampler not in self.image_generation_feature_flags.samplers for sampler in request.samplers):
                return False
        return True

    def worker_supports_requested_schedulers(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports the schedulers requested."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.schedulers_map:
            for baseline in request.baselines or []:
                if any(
                    scheduler not in self.per_baseline_feature_flags.schedulers_map.get(baseline, [])
                    for scheduler in request.schedulers
                ):
                    return False
        else:
            if any(
                scheduler not in self.image_generation_feature_flags.schedulers for scheduler in request.schedulers
            ):
                return False
        return True

    def worker_supports_requested_tiling(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports tiling."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.tiling_map:
            for baseline in request.baselines or []:
                if not self.per_baseline_feature_flags.tiling_map.get(baseline, True):
                    return False
        else:
            if request.tiling and not self.image_generation_feature_flags.tiling:
                return False
        return True

    def worker_supports_requested_hires_fix(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports hires fix."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.hires_fix_map:
            for baseline in request.baselines or []:
                if not self.per_baseline_feature_flags.hires_fix_map.get(baseline, True):
                    return False
        else:
            if request.hires_fix and not self.image_generation_feature_flags.hires_fix:
                return False
        return True

    def worker_supports_requested_controlnets(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports controlnets."""
        if not request.controlnets_feature_flags:
            return True

        if not self.image_generation_feature_flags.controlnets_feature_flags:
            return False

        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.controlnet_map:
            for baseline in request.baselines or []:
                if not self.per_baseline_feature_flags.controlnet_map.get(baseline, True):
                    return False

        if (
            request.controlnets_feature_flags.image_is_control
            and not self.image_generation_feature_flags.controlnets_feature_flags.image_is_control
        ):
            return False

        if (  # noqa SIM103: For readability, we return this False directly
            request.controlnets_feature_flags.return_control_map
            and not self.image_generation_feature_flags.controlnets_feature_flags.return_control_map
        ):
            return False

        return True

    def worker_supports_requested_tis(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports TIs."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.tis_map:
            for baseline in request.baselines or []:
                if not self.per_baseline_feature_flags.tis_map.get(baseline, True):
                    return False
        else:
            if request.tis and not self.image_generation_feature_flags.tis:
                return False
        return True

    def worker_supports_requested_loras(
        self,
        request: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return True if the worker supports Loras."""
        if self.per_baseline_feature_flags and self.per_baseline_feature_flags.loras_map:
            for baseline in request.baselines or []:
                if not self.per_baseline_feature_flags.loras_map.get(baseline, True):
                    return False
        else:
            if request.loras and not self.image_generation_feature_flags.loras:
                return False
        return True


# class TextWorkerFeatureFlags(WorkerFeatureFlags[TEXT_WORKER_NOT_CAPABLE_REASON]):
#     """Feature flags for a text worker."""


class ALCHEMY_WORKER_NOT_CAPABLE_REASON(StrEnum):
    """Reasons why a worker is not capable of handling an alchemy request."""

    unsupported_upscaler = auto()
    """The worker does not support a requested upscaler."""

    unsupported_facefixer = auto()
    """The worker does not support a requested facefixer."""

    unsupported_interrogator = auto()
    """The worker does not support a requested interrogator."""

    unsupported_caption_model = auto()
    """The worker does not support a requested caption model."""

    unsupported_nsfw_detector = auto()
    """The worker does not support a requested NSFW detector."""

    unsupported_misc = auto()
    """The worker does not support a requested miscellaneous feature."""


class AlchemyWorkerFeatureFlags(WorkerFeatureFlags[ALCHEMY_WORKER_NOT_CAPABLE_REASON]):
    """Feature flags for an alchemy worker."""

    alchemy_feature_flags: AlchemyFeatureFlags

    @override
    def get_not_capable_reason_type(self) -> type[ALCHEMY_WORKER_NOT_CAPABLE_REASON]:
        return ALCHEMY_WORKER_NOT_CAPABLE_REASON

    @override
    def reasons_not_capable_of_features(
        self,
        request: GenerationFeatureFlags,
    ) -> list[ALCHEMY_WORKER_NOT_CAPABLE_REASON] | None:
        """Return a list of reasons why a worker is not capable of handling an alchemy request."""
        if not isinstance(request, AlchemyFeatureFlags):
            logger.debug(f"Request is not an AlchemyFeatureFlags instance. Request type: {type(request)}")
            return None

        if not self.alchemy_feature_flags:
            logger.debug("Worker does not have alchemy feature flags.")
            return None

        if not request.alchemy_types:
            logger.debug("Request does not have alchemy types.")
            return None

        reasons = []

        for alchemy_type in request.alchemy_types:
            if alchemy_type not in self.alchemy_feature_flags.alchemy_types:
                if is_upscaler_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_upscaler)
                elif is_facefixer_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_facefixer)
                elif is_interrogator_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_interrogator)
                elif is_caption_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_caption_model)
                elif is_nsfw_detector_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_nsfw_detector)
                else:
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_misc)
        return reasons if reasons else None


# class AudioWorkerFeatureFlags(WorkerFeatureFlags[AUDIO_WORKER_NOT_CAPABLE_REASON]):
#     """Feature flags for an audio worker."""


# class VideoWorkerFeatureFlags(WorkerFeatureFlags[VIDEO_WORKER_NOT_CAPABLE_REASON]):
#     """Feature flags for a video worker."""
