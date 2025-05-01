from enum import auto

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import BaseModel, Field
from strenum import StrEnum

from horde_sdk import get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.alchemy.object_models import AlchemyFeatureFlags
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.image.consts import (
    CLIP_SKIP_REPRESENTATION,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
)
from horde_sdk.generation_parameters.image.object_models import ImageGenerationFeatureFlags


class RESULT_RETURN_METHOD(StrEnum):
    """The method of returning results from a worker."""

    base64_post_back = auto()
    """Base64 post back in the 'job completed' message."""

    base64_post_back_with_url = auto()
    """Base64 post back to a given URL without results in the 'job completed' message."""

    byte_stream = auto()
    """Byte stream to a given URL without results in the 'job completed' message."""


class WorkerFeatureFlags(BaseModel):
    """Feature flags for a worker."""

    model_config = get_default_frozen_model_config_dict()

    supported_result_return_methods: list[RESULT_RETURN_METHOD] = Field(default_factory=list)
    """The methods of returning results supported by the worker."""

    supports_threads: bool = Field(default=False)
    """Whether the worker supports threading."""


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


class ImageWorkerFeatureFlags(WorkerFeatureFlags):
    """Feature flags for an image worker."""

    image_generation_feature_flags: ImageGenerationFeatureFlags
    """The image generation feature flags for the worker."""

    per_baseline_feature_flags: PerBaselineFeatureFlags | None = None
    """The per baseline feature flags for the worker. This includes the supported schedulers and
    samplers for each baseline."""

    backend_clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = None
    """The clip skip representation supported."""


class TextWorkerFeatureFlags(WorkerFeatureFlags):
    """Feature flags for a text worker."""


class AlchemyWorkerFeatureFlags(WorkerFeatureFlags):
    """Feature flags for an alchemy worker."""

    alchemy_feature_flags: AlchemyFeatureFlags


class AudioWorkerFeatureFlags(WorkerFeatureFlags):
    """Feature flags for an audio worker."""


class VideoWorkerFeatureFlags(WorkerFeatureFlags):
    """Feature flags for a video worker."""


class WORKER_NOT_CAPABLE_REASON(StrEnum):
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


def reasons_worker_not_capable(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> list[WORKER_NOT_CAPABLE_REASON] | None:
    """Return a list of reasons why a worker is not capable of handling a request."""
    reasons = []

    if request.clip_skip and not worker.image_generation_feature_flags.clip_skip:
        reasons.append(WORKER_NOT_CAPABLE_REASON.clip_skip)

    if not worker_supports_requested_samplers(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.samplers)

    if not worker_supports_requested_schedulers(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.schedulers)

    if not worker_supports_requested_tiling(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.tiling)

    if not worker_supports_requested_hires_fix(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.hires_fix)

    if not worker_supports_requested_controlnets(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.controlnets)

    if not worker_supports_requested_tis(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.tis)

    if not worker_supports_requested_loras(request, worker):
        reasons.append(WORKER_NOT_CAPABLE_REASON.loras)

    if request.extra_texts and not worker.image_generation_feature_flags.extra_texts:
        reasons.append(WORKER_NOT_CAPABLE_REASON.extra_texts)

    if request.extra_source_images and not worker.image_generation_feature_flags.extra_source_images:
        reasons.append(WORKER_NOT_CAPABLE_REASON.extra_source_images)

    if (
        request.baselines
        and worker.image_generation_feature_flags.baselines
        and (not any(baseline in worker.image_generation_feature_flags.baselines for baseline in request.baselines))
    ):
        reasons.append(WORKER_NOT_CAPABLE_REASON.unsupported_baseline)

    return reasons if reasons else None


def is_image_worker_capable(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Check if a request is compatible with an image worker.

    Args:
        request: The request to check.
        worker: The image worker to check against.

    Returns:
        True if the request is compatible with the image worker, False otherwise.
    """
    reasons = reasons_worker_not_capable(request, worker)

    return reasons is None


def worker_supports_requested_samplers(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports the samplers requested."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.samplers_map:
        for baseline in request.baselines or []:
            if any(
                sampler not in worker.per_baseline_feature_flags.samplers_map.get(baseline, [])
                for sampler in request.samplers
            ):
                return False
    else:
        if any(sampler not in worker.image_generation_feature_flags.samplers for sampler in request.samplers):
            return False
    return True


def worker_supports_requested_schedulers(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports the schedulers requested."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.schedulers_map:
        for baseline in request.baselines or []:
            if any(
                scheduler not in worker.per_baseline_feature_flags.schedulers_map.get(baseline, [])
                for scheduler in request.schedulers
            ):
                return False
    else:
        if any(scheduler not in worker.image_generation_feature_flags.schedulers for scheduler in request.schedulers):
            return False
    return True


def worker_supports_requested_tiling(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports tiling."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.tiling_map:
        for baseline in request.baselines or []:
            if not worker.per_baseline_feature_flags.tiling_map.get(baseline, True):
                return False
    else:
        if request.tiling and not worker.image_generation_feature_flags.tiling:
            return False
    return True


def worker_supports_requested_hires_fix(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports hires fix."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.hires_fix_map:
        for baseline in request.baselines or []:
            if not worker.per_baseline_feature_flags.hires_fix_map.get(baseline, True):
                return False
    else:
        if request.hires_fix and not worker.image_generation_feature_flags.hires_fix:
            return False
    return True


def worker_supports_requested_controlnets(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports controlnets."""
    if not request.controlnets_feature_flags:
        return True

    if not worker.image_generation_feature_flags.controlnets_feature_flags:
        return False

    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.controlnet_map:
        for baseline in request.baselines or []:
            if not worker.per_baseline_feature_flags.controlnet_map.get(baseline, True):
                return False

    if (
        request.controlnets_feature_flags.image_is_control
        and not worker.image_generation_feature_flags.controlnets_feature_flags.image_is_control
    ):
        return False

    if (  # noqa: SIM103: while the bool is needless, it is more readable
        request.controlnets_feature_flags.return_control_map
        and not worker.image_generation_feature_flags.controlnets_feature_flags.return_control_map
    ):
        return False

    return True


def worker_supports_requested_tis(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports TIs."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.tis_map:
        for baseline in request.baselines or []:
            if not worker.per_baseline_feature_flags.tis_map.get(baseline, True):
                return False
    else:
        if request.tis and not worker.image_generation_feature_flags.tis:
            return False
    return True


def worker_supports_requested_loras(
    request: ImageGenerationFeatureFlags,
    worker: ImageWorkerFeatureFlags,
) -> bool:
    """Return True if the worker supports Loras."""
    if worker.per_baseline_feature_flags and worker.per_baseline_feature_flags.loras_map:
        for baseline in request.baselines or []:
            if not worker.per_baseline_feature_flags.loras_map.get(baseline, True):
                return False
    else:
        if request.loras and not worker.image_generation_feature_flags.loras:
            return False
    return True


def is_worker_capable(
    request: GenerationFeatureFlags,
    worker: WorkerFeatureFlags,
) -> bool:
    """Check if a request is compatible with a worker.

    Args:
        request: The request to check.
        worker: The worker to check against.

    Returns:
        True if the request is compatible with the worker, False otherwise.
    """
    if isinstance(worker, ImageWorkerFeatureFlags) and isinstance(request, ImageGenerationFeatureFlags):
        return is_image_worker_capable(request, worker)

    if isinstance(worker, AlchemyWorkerFeatureFlags) and isinstance(request, AlchemyFeatureFlags):
        raise NotImplementedError("Alchemy worker capability check not implemented yet")
        # return is_alchemy_worker_capable(request, worker)

    if isinstance(worker, TextWorkerFeatureFlags) and isinstance(request, GenerationFeatureFlags):
        raise NotImplementedError("Text worker capability check not implemented yet")
        # return is_text_worker_capable(request, worker)

    raise NotImplementedError(f"Worker capability check not implemented for this worker type ({type(worker)})")
