from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import auto
from typing import TypeVar, override

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from loguru import logger
from pydantic import BaseModel, Field
from strenum import StrEnum

from horde_sdk import get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.alchemy.consts import (
    is_annotation_form,
    is_caption_form,
    is_facefixer_form,
    is_image_vectorizer_form,
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
from horde_sdk.generation_parameters.image.object_models import (
    ImageGenerationFeatureFlags,
    union_image_generation_feature_flags,
)
from horde_sdk.generation_parameters.image.sampler_work import (
    SamplerExecutionContractVersion,
    minimum_common_sampler_execution_contract_version,
)

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
    """Represents exhaustive baseline-specific restrictions on a worker feature profile.

    `None` leaves the corresponding flat feature advertisement in effect. Once a map is supplied,
    a missing baseline advertises no support for that feature on the omitted baseline.
    """

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
    support all schedulers.

    A populated map is exhaustive: a baseline absent from it advertises support for no schedulers at
    all, not for the flat `schedulers` list. A worker setting this map must therefore cover every
    baseline it serves."""

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
    support all samplers.

    A populated map is exhaustive: a baseline absent from it advertises support for no samplers at
    all, not for the flat `samplers` list. A worker setting this map must therefore cover every
    baseline it serves."""

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
    follow the flat tiling flag. A populated map is exhaustive."""

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
    follow the flat hires-fix flag. A populated map is exhaustive."""

    transparent_map: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None = Field(
        default=None,
        examples=[
            {
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: True,
                KNOWN_IMAGE_GENERATION_BASELINE.stable_cascade: False,
            },
        ],
    )
    """If set, support for transparent generation for each baseline. If unset, all advertised
    baselines follow the flat transparent flag. A populated map is exhaustive."""

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
    follow the flat ControlNet feature flags. A populated map is exhaustive."""

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
    the advertised TI sources. A populated map is exhaustive."""

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
    support the advertised LoRA sources. A populated map is exhaustive."""


class IMAGE_WORKER_NOT_CAPABLE_REASON(StrEnum):
    """Reasons why a worker is not capable of handling a request."""

    clip_skip = auto()
    """The worker does not support clip skip."""

    samplers = auto()
    """The worker does not support the requested samplers."""

    sampler_solver_knobs = auto()
    """The worker does not support one or more requested sampler solver knobs."""

    flow_shift = auto()
    """The worker does not support model-specific flow shifting."""

    transparent = auto()
    """The worker does not support transparent image generation."""

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

    post_processing = auto()
    """The worker does not support one or more requested post-processors."""

    source_processing = auto()
    """The worker does not support the requested source-processing mode."""

    workflows = auto()
    """The worker does not support the requested workflow."""

    unsupported_baseline = auto()
    """The worker does not support the requested baseline."""

    unsupported_generation_type = auto()
    """The supplied requirements describe a different generation domain."""


@dataclass(frozen=True, slots=True)
class _ImageFeatureCompatibilityCheck:
    """Couple a feature support verdict to its durable reason."""

    is_supported: bool
    reason: IMAGE_WORKER_NOT_CAPABLE_REASON


class ImageWorkerFeatureFlags(WorkerFeatureFlags[IMAGE_WORKER_NOT_CAPABLE_REASON]):
    """Represents portable render features advertised by an image worker.

    This profile does not describe model residency, resource fit, queue state, worker readiness, or
    service policy. Consumers compose those constraints with `is_capable_of_features`.
    """

    image_generation_feature_flags: ImageGenerationFeatureFlags
    """The image generation feature flags for the worker."""

    per_baseline_feature_flags: PerBaselineFeatureFlags | None = None
    """The per baseline feature flags for the worker. This includes the supported schedulers and
    samplers for each baseline."""

    backend_clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = None
    """The clip skip representation supported."""

    sampler_execution_contract_version: SamplerExecutionContractVersion | None = None
    """Cumulative SDK execution contract guaranteed by every backend path in this profile."""

    @override
    def get_not_capable_reason_type(self) -> type[IMAGE_WORKER_NOT_CAPABLE_REASON]:
        return IMAGE_WORKER_NOT_CAPABLE_REASON

    @override
    def reasons_not_capable_of_features(
        self,
        requested_features: GenerationFeatureFlags,
    ) -> list[IMAGE_WORKER_NOT_CAPABLE_REASON] | None:
        """Return reasons the advertised worker features do not cover a request.

        Args:
            requested_features: Features required by one image generation.

        Returns:
            The stable incompatibility reasons, or `None` when every requirement is supported.

        """
        if not isinstance(requested_features, ImageGenerationFeatureFlags):
            return [IMAGE_WORKER_NOT_CAPABLE_REASON.unsupported_generation_type]

        compatibility_checks = self._get_image_feature_compatibility_checks(requested_features)
        reasons = [check.reason for check in compatibility_checks.values() if not check.is_supported]
        return reasons or None

    def _get_image_feature_compatibility_checks(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> dict[str, _ImageFeatureCompatibilityCheck]:
        """Return the exhaustive compatibility registry for an image request."""
        supported_features = self.image_generation_feature_flags
        return {
            "extra_texts": _ImageFeatureCompatibilityCheck(
                not requested_features.extra_texts or supported_features.extra_texts,
                IMAGE_WORKER_NOT_CAPABLE_REASON.extra_texts,
            ),
            "extra_source_images": _ImageFeatureCompatibilityCheck(
                not requested_features.extra_source_images or supported_features.extra_source_images,
                IMAGE_WORKER_NOT_CAPABLE_REASON.extra_source_images,
            ),
            "baselines": _ImageFeatureCompatibilityCheck(
                self._worker_supports_requested_values(
                    requested_features.baselines,
                    supported_features.baselines,
                ),
                IMAGE_WORKER_NOT_CAPABLE_REASON.unsupported_baseline,
            ),
            "clip_skip": _ImageFeatureCompatibilityCheck(
                not requested_features.clip_skip or supported_features.clip_skip,
                IMAGE_WORKER_NOT_CAPABLE_REASON.clip_skip,
            ),
            "hires_fix": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_hires_fix(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.hires_fix,
            ),
            "tiling": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_tiling(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.tiling,
            ),
            "schedulers": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_schedulers(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.schedulers,
            ),
            "samplers": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_samplers(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.samplers,
            ),
            "sampler_solver_knobs": _ImageFeatureCompatibilityCheck(
                self._worker_supports_requested_values(
                    requested_features.sampler_solver_knobs,
                    supported_features.sampler_solver_knobs,
                ),
                IMAGE_WORKER_NOT_CAPABLE_REASON.sampler_solver_knobs,
            ),
            "flow_shift": _ImageFeatureCompatibilityCheck(
                not requested_features.flow_shift or supported_features.flow_shift,
                IMAGE_WORKER_NOT_CAPABLE_REASON.flow_shift,
            ),
            "transparent": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_transparent(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.transparent,
            ),
            "controlnets_feature_flags": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_controlnets(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.controlnets,
            ),
            "post_processing": _ImageFeatureCompatibilityCheck(
                self._worker_supports_requested_values(
                    requested_features.post_processing,
                    supported_features.post_processing,
                ),
                IMAGE_WORKER_NOT_CAPABLE_REASON.post_processing,
            ),
            "source_processing": _ImageFeatureCompatibilityCheck(
                self._worker_supports_requested_values(
                    requested_features.source_processing,
                    supported_features.source_processing,
                ),
                IMAGE_WORKER_NOT_CAPABLE_REASON.source_processing,
            ),
            "workflows": _ImageFeatureCompatibilityCheck(
                self._worker_supports_requested_values(
                    requested_features.workflows,
                    supported_features.workflows,
                ),
                IMAGE_WORKER_NOT_CAPABLE_REASON.workflows,
            ),
            "tis": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_tis(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.tis,
            ),
            "loras": _ImageFeatureCompatibilityCheck(
                self.worker_supports_requested_loras(requested_features),
                IMAGE_WORKER_NOT_CAPABLE_REASON.loras,
            ),
        }

    @staticmethod
    def _worker_supports_requested_values(
        requested_values: Sequence[object] | None,
        supported_values: Sequence[object] | None,
    ) -> bool:
        """Return whether all requested values appear in the advertised values."""
        if not requested_values:
            return True
        if not supported_values:
            return False
        return all(requested_value in supported_values for requested_value in requested_values)

    def _per_baseline_boolean_supports_request(
        self,
        requested_features: ImageGenerationFeatureFlags,
        per_baseline_support: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None,
    ) -> bool:
        """Return whether an exhaustive per-baseline boolean map covers the request."""
        if per_baseline_support is None:
            return True
        return all(per_baseline_support.get(baseline, False) for baseline in requested_features.baselines)

    def worker_supports_requested_samplers(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports every requested sampler."""
        if not self._worker_supports_requested_values(
            requested_features.samplers,
            self.image_generation_feature_flags.samplers,
        ):
            return False
        sampler_map = self.per_baseline_feature_flags.samplers_map if self.per_baseline_feature_flags else None
        if sampler_map is None:
            return True
        return all(
            self._worker_supports_requested_values(requested_features.samplers, sampler_map.get(baseline))
            for baseline in requested_features.baselines
        )

    def worker_supports_requested_schedulers(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports every requested scheduler."""
        if not self._worker_supports_requested_values(
            requested_features.schedulers,
            self.image_generation_feature_flags.schedulers,
        ):
            return False
        scheduler_map = self.per_baseline_feature_flags.schedulers_map if self.per_baseline_feature_flags else None
        if scheduler_map is None:
            return True
        return all(
            self._worker_supports_requested_values(requested_features.schedulers, scheduler_map.get(baseline))
            for baseline in requested_features.baselines
        )

    def worker_supports_requested_tiling(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports tiling for every requested baseline."""
        if not requested_features.tiling:
            return True
        if not self.image_generation_feature_flags.tiling:
            return False
        tiling_map = self.per_baseline_feature_flags.tiling_map if self.per_baseline_feature_flags else None
        if tiling_map is not None:
            return self._per_baseline_boolean_supports_request(requested_features, tiling_map)
        return True

    def worker_supports_requested_hires_fix(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports hires fix for every requested baseline."""
        if not requested_features.hires_fix:
            return True
        if not self.image_generation_feature_flags.hires_fix:
            return False
        hires_fix_map = self.per_baseline_feature_flags.hires_fix_map if self.per_baseline_feature_flags else None
        if hires_fix_map is not None:
            return self._per_baseline_boolean_supports_request(requested_features, hires_fix_map)
        return True

    def worker_supports_requested_transparent(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports transparency for every requested baseline."""
        if not requested_features.transparent:
            return True
        if not self.image_generation_feature_flags.transparent:
            return False
        transparent_map = self.per_baseline_feature_flags.transparent_map if self.per_baseline_feature_flags else None
        if transparent_map is not None:
            return self._per_baseline_boolean_supports_request(requested_features, transparent_map)
        return True

    def worker_supports_requested_controlnets(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports the requested ControlNet configuration."""
        requested_controlnets = requested_features.controlnets_feature_flags
        if requested_controlnets is None:
            return True

        supported_controlnets = self.image_generation_feature_flags.controlnets_feature_flags
        if supported_controlnets is None:
            return False

        controlnet_map = self.per_baseline_feature_flags.controlnet_map if self.per_baseline_feature_flags else None
        if controlnet_map is not None and not self._per_baseline_boolean_supports_request(
            requested_features,
            controlnet_map,
        ):
            return False

        if not self._worker_supports_requested_values(
            requested_controlnets.controlnets, supported_controlnets.controlnets
        ):
            return False

        supports_control_image = not requested_controlnets.image_is_control or supported_controlnets.image_is_control
        supports_returned_map = (
            not requested_controlnets.return_control_map or supported_controlnets.return_control_map
        )
        return supports_control_image and supports_returned_map

    def worker_supports_requested_tis(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports every requested textual-inversion source."""
        if not self._worker_supports_requested_values(requested_features.tis, self.image_generation_feature_flags.tis):
            return False
        if not requested_features.tis:
            return True
        tis_map = self.per_baseline_feature_flags.tis_map if self.per_baseline_feature_flags else None
        return self._per_baseline_boolean_supports_request(requested_features, tis_map)

    def worker_supports_requested_loras(
        self,
        requested_features: ImageGenerationFeatureFlags,
    ) -> bool:
        """Return whether the worker supports every requested LoRA source."""
        if not self._worker_supports_requested_values(
            requested_features.loras,
            self.image_generation_feature_flags.loras,
        ):
            return False
        if not requested_features.loras:
            return True
        loras_map = self.per_baseline_feature_flags.loras_map if self.per_baseline_feature_flags else None
        return self._per_baseline_boolean_supports_request(requested_features, loras_map)


def _profile_union_baselines(
    profiles: Sequence[ImageWorkerFeatureFlags],
) -> list[KNOWN_IMAGE_GENERATION_BASELINE | str]:
    """Return advertised baselines once in profile order."""
    baselines: list[KNOWN_IMAGE_GENERATION_BASELINE | str] = []
    for profile in profiles:
        for baseline in profile.image_generation_feature_flags.baselines:
            if baseline not in baselines:
                baselines.append(baseline)
    return baselines


def _union_sequence_axis[FeatureValue](
    profiles: Sequence[ImageWorkerFeatureFlags],
    *,
    map_getter: Callable[
        [PerBaselineFeatureFlags],
        dict[KNOWN_IMAGE_GENERATION_BASELINE | str, list[FeatureValue]] | None,
    ],
    flat_getter: Callable[[ImageGenerationFeatureFlags], Sequence[FeatureValue] | None],
) -> dict[KNOWN_IMAGE_GENERATION_BASELINE | str, list[FeatureValue]] | None:
    """Union one sequence axis while retaining which profile supports each baseline."""
    maps = [
        map_getter(profile.per_baseline_feature_flags) if profile.per_baseline_feature_flags else None
        for profile in profiles
    ]
    if all(feature_map is None for feature_map in maps):
        return None

    union: dict[KNOWN_IMAGE_GENERATION_BASELINE | str, list[FeatureValue]] = {}
    for baseline in _profile_union_baselines(profiles):
        baseline_values: list[FeatureValue] = []
        for profile, feature_map in zip(profiles, maps, strict=True):
            flat_features = profile.image_generation_feature_flags
            if baseline not in flat_features.baselines:
                continue
            flat_values = flat_getter(flat_features) or []
            candidates = flat_values if feature_map is None else feature_map.get(baseline, [])
            for value in candidates:
                if value in flat_values and value not in baseline_values:
                    baseline_values.append(value)
        union[baseline] = baseline_values
    return union


def _union_boolean_axis(
    profiles: Sequence[ImageWorkerFeatureFlags],
    *,
    map_getter: Callable[
        [PerBaselineFeatureFlags],
        dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None,
    ],
    flat_getter: Callable[[ImageGenerationFeatureFlags], bool],
) -> dict[KNOWN_IMAGE_GENERATION_BASELINE | str, bool] | None:
    """Union one boolean axis while retaining which profile supports each baseline."""
    maps = [
        map_getter(profile.per_baseline_feature_flags) if profile.per_baseline_feature_flags else None
        for profile in profiles
    ]
    if all(feature_map is None for feature_map in maps):
        return None

    return {
        baseline: any(
            baseline in profile.image_generation_feature_flags.baselines
            and flat_getter(profile.image_generation_feature_flags)
            and (feature_map is None or feature_map.get(baseline, False))
            for profile, feature_map in zip(profiles, maps, strict=True)
        )
        for baseline in _profile_union_baselines(profiles)
    }


def _union_per_baseline_feature_flags(
    profiles: Sequence[ImageWorkerFeatureFlags],
) -> PerBaselineFeatureFlags | None:
    """Return the union of baseline restrictions, or no restrictions when every axis is flat."""
    per_baseline_profiles = [profile.per_baseline_feature_flags for profile in profiles]
    if all(per_baseline_profile is None for per_baseline_profile in per_baseline_profiles):
        return None

    return PerBaselineFeatureFlags(
        schedulers_map=_union_sequence_axis(
            profiles,
            map_getter=lambda profile: profile.schedulers_map,
            flat_getter=lambda features: features.schedulers,
        ),
        samplers_map=_union_sequence_axis(
            profiles,
            map_getter=lambda profile: profile.samplers_map,
            flat_getter=lambda features: features.samplers,
        ),
        tiling_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.tiling_map,
            flat_getter=lambda features: features.tiling,
        ),
        hires_fix_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.hires_fix_map,
            flat_getter=lambda features: features.hires_fix,
        ),
        transparent_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.transparent_map,
            flat_getter=lambda features: features.transparent,
        ),
        controlnet_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.controlnet_map,
            flat_getter=lambda features: features.controlnets_feature_flags is not None,
        ),
        tis_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.tis_map,
            flat_getter=lambda features: bool(features.tis),
        ),
        loras_map=_union_boolean_axis(
            profiles,
            map_getter=lambda profile: profile.loras_map,
            flat_getter=lambda features: bool(features.loras),
        ),
    )


def union_image_worker_feature_flags(
    profiles: Sequence[ImageWorkerFeatureFlags],
) -> ImageWorkerFeatureFlags:
    """Return the axis-wise union of image worker profiles.

    The operation preserves the meaning of exhaustive per-baseline maps. When any input restricts an axis,
    the union computes that axis independently for every advertised baseline. A flat input contributes its
    flat values only on its own baselines, and a missing baseline contributes no support. Correlations between
    separate axes are not representable by this model, so a heterogeneous union is not itself a routeability
    proof; callers must retain member identity or otherwise prove that emitted combinations are supported.

    Args:
        profiles: Canonical image worker profiles to combine.

    Returns:
        One profile containing every independently advertised feature value.

    Raises:
        ValueError: If no profiles are supplied.
    """
    if not profiles:
        raise ValueError("At least one image worker feature profile is required.")

    clip_skip_representations = {
        profile.backend_clip_skip_representation
        for profile in profiles
        if profile.backend_clip_skip_representation is not None
    }
    clip_skip_representation = next(iter(clip_skip_representations)) if len(clip_skip_representations) == 1 else None

    result_methods: list[RESULT_RETURN_METHOD] = []
    for profile in profiles:
        for result_method in profile.supported_result_return_methods:
            if result_method not in result_methods:
                result_methods.append(result_method)

    return ImageWorkerFeatureFlags(
        supported_result_return_methods=result_methods,
        supports_threads=any(profile.supports_threads for profile in profiles),
        image_generation_feature_flags=union_image_generation_feature_flags(
            [profile.image_generation_feature_flags for profile in profiles],
        ),
        per_baseline_feature_flags=_union_per_baseline_feature_flags(profiles),
        backend_clip_skip_representation=clip_skip_representation,
        sampler_execution_contract_version=minimum_common_sampler_execution_contract_version(
            [profile.sampler_execution_contract_version for profile in profiles],
        ),
    )


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

    unsupported_vectorizer = auto()
    """The worker does not support image vectorization."""

    unsupported_annotation = auto()
    """The worker does not support controlnet annotation."""

    unsupported_misc = auto()
    """The worker does not support a requested miscellaneous feature."""

    unsupported_generation_type = auto()
    """The supplied requirements describe a different generation domain."""


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
            return [ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_generation_type]

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
                elif is_image_vectorizer_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_vectorizer)
                elif is_annotation_form(alchemy_type):
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_annotation)
                else:
                    reasons.append(ALCHEMY_WORKER_NOT_CAPABLE_REASON.unsupported_misc)
        return reasons if reasons else None


# class AudioWorkerFeatureFlags(WorkerFeatureFlags[AUDIO_WORKER_NOT_CAPABLE_REASON]):
#     """Feature flags for an audio worker."""


# class VideoWorkerFeatureFlags(WorkerFeatureFlags[VIDEO_WORKER_NOT_CAPABLE_REASON]):
#     """Feature flags for a video worker."""
