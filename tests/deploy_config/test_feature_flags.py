import pytest
from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE

from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image.consts import (
    CLIP_SKIP_REPRESENTATION,
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    KNOWN_IMAGE_WORKFLOWS,
)
from horde_sdk.generation_parameters.image.object_models import (
    ControlnetFeatureFlags,
    ImageGenerationFeatureFlags,
    ImageGenerationParameters,
    image_parameters_to_feature_flags,
)
from horde_sdk.worker.feature_flags import (
    IMAGE_WORKER_NOT_CAPABLE_REASON,
    RESULT_RETURN_METHOD,
    ImageWorkerFeatureFlags,
)


@pytest.fixture(scope="function")
def reference_image_worker_feature_flags() -> ImageWorkerFeatureFlags:
    """Fixture for a 'reference' worker capable of all features."""
    return ImageWorkerFeatureFlags(
        supported_result_return_methods=list(RESULT_RETURN_METHOD.__members__.values()),
        supports_threads=True,
        image_generation_feature_flags=ImageGenerationFeatureFlags(
            baselines=list(KNOWN_IMAGE_GENERATION_BASELINE.__members__.values()),
            clip_skip_representation=CLIP_SKIP_REPRESENTATION.NEGATIVE_OFFSET,
            hires_fix=True,
            schedulers=list(KNOWN_IMAGE_SCHEDULERS.__members__.values()),
            samplers=list(KNOWN_IMAGE_SAMPLERS.__members__.values()),
            tiling=True,
            controlnets_feature_flags=ControlnetFeatureFlags(
                controlnets=list(KNOWN_IMAGE_CONTROLNETS.__members__.values()),
                image_is_control=True,
                return_control_map=True,
            ),
            post_processing=list(KNOWN_ALCHEMY_TYPES.__members__.values()),
            source_processing=list(KNOWN_IMAGE_SOURCE_PROCESSING.__members__.values()),
            workflows=list(KNOWN_IMAGE_WORKFLOWS.__members__.values()),
            tis=list(KNOWN_AUX_MODEL_SOURCE.__members__.values()),
            loras=list(KNOWN_AUX_MODEL_SOURCE.__members__.values()),
        ),
    )


@pytest.fixture(scope="function")
def minimal_image_worker_feature_flags() -> ImageWorkerFeatureFlags:
    """Fixture for a 'minimal' worker capable of only the most basic features."""
    return ImageWorkerFeatureFlags(
        supported_result_return_methods=[RESULT_RETURN_METHOD.base64_post_back],
        supports_threads=False,
        image_generation_feature_flags=ImageGenerationFeatureFlags(
            baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1],
            clip_skip_representation=CLIP_SKIP_REPRESENTATION.NEGATIVE_OFFSET,
            hires_fix=False,
            schedulers=[KNOWN_IMAGE_SCHEDULERS.simple],
            samplers=[KNOWN_IMAGE_SAMPLERS.k_lms],
            tiling=False,
            controlnets_feature_flags=None,
            post_processing=None,
            source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.txt2img],
            workflows=None,
            tis=None,
            loras=None,
        ),
    )


def test_image_parameters_to_feature_flags(
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    feature_flags = image_parameters_to_feature_flags(simple_image_generation_parameters)
    assert isinstance(feature_flags, ImageGenerationFeatureFlags)

    assert len(feature_flags.baselines) == 1
    assert feature_flags.baselines
    assert KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1 in feature_flags.baselines

    assert feature_flags.workflows is None
    assert feature_flags.loras is None
    assert feature_flags.tis is None

    assert len(feature_flags.samplers) == 1
    assert len(feature_flags.schedulers) == 1
    assert not feature_flags.extra_source_images
    assert not feature_flags.extra_texts
    assert not feature_flags.tiling
    assert not feature_flags.hires_fix

    assert simple_image_generation_parameters.base_params.model_baseline in feature_flags.baselines
    assert simple_image_generation_parameters.base_params.sampler_name in feature_flags.samplers
    assert simple_image_generation_parameters.base_params.scheduler in feature_flags.schedulers


def test_is_image_worker_capable(
    reference_image_worker_feature_flags: ImageWorkerFeatureFlags,
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    assert reference_image_worker_feature_flags.is_capable_of_features(
        image_parameters_to_feature_flags(simple_image_generation_parameters),
    )


def test_minimal_worker_not_capable(
    minimal_image_worker_feature_flags: ImageWorkerFeatureFlags,
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    assert not minimal_image_worker_feature_flags.is_capable_of_features(
        image_parameters_to_feature_flags(simple_image_generation_parameters),
    )


def test_reasons_minimal_worker_not_capable(
    minimal_image_worker_feature_flags: ImageWorkerFeatureFlags,
    simple_image_generation_parameters: ImageGenerationParameters,
    simple_image_generation_parameters_hires_fix: ImageGenerationParameters,
) -> None:
    reasons_simple = minimal_image_worker_feature_flags.reasons_not_capable_of_features(
        image_parameters_to_feature_flags(simple_image_generation_parameters),
    )
    assert reasons_simple is not None
    assert len(reasons_simple) == 2
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.schedulers in reasons_simple
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.samplers in reasons_simple

    reasons_tiling = minimal_image_worker_feature_flags.reasons_not_capable_of_features(
        image_parameters_to_feature_flags(simple_image_generation_parameters.model_copy(update={"tiling": True})),
    )
    assert reasons_tiling is not None
    assert len(reasons_tiling) == 3
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.schedulers in reasons_simple
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.samplers in reasons_simple
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.tiling in reasons_tiling

    reasons_hires = minimal_image_worker_feature_flags.reasons_not_capable_of_features(
        image_parameters_to_feature_flags(simple_image_generation_parameters_hires_fix),
    )

    assert reasons_hires is not None
    assert len(reasons_hires) == 3
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.schedulers in reasons_simple
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.samplers in reasons_simple
    assert IMAGE_WORKER_NOT_CAPABLE_REASON.hires_fix in reasons_hires
