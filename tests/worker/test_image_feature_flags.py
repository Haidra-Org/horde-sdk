"""Verify directional image feature compatibility."""

from collections.abc import Callable

import pytest
from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE

from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.image.constraints import SAMPLER_SOLVER_KNOB
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    KNOWN_IMAGE_WORKFLOWS,
)
from horde_sdk.generation_parameters.image.object_models import (
    ControlnetFeatureFlags,
    ImageGenerationFeatureFlags,
    intersect_image_generation_feature_flags,
    union_image_generation_feature_flags,
)
from horde_sdk.generation_parameters.image.sampler_work import SamplerExecutionContractVersion
from horde_sdk.worker.feature_flags import (
    ImageWorkerFeatureFlags,
    PerBaselineFeatureFlags,
    union_image_worker_feature_flags,
)


def _feature_flags(**updates: object) -> ImageGenerationFeatureFlags:
    """Create a narrow feature set with stable defaults."""
    feature_flags = ImageGenerationFeatureFlags(
        baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1],
        schedulers=[],
        samplers=[],
        source_processing=[],
    )
    return feature_flags.model_copy(update=updates)


def _worker(
    supported_features: ImageGenerationFeatureFlags,
    *,
    per_baseline_features: PerBaselineFeatureFlags | None = None,
) -> ImageWorkerFeatureFlags:
    """Create a worker advertising exactly the supplied render features."""
    return ImageWorkerFeatureFlags(
        image_generation_feature_flags=supported_features,
        per_baseline_feature_flags=per_baseline_features,
    )


def test_union_only_retains_an_execution_contract_shared_by_every_backend_path() -> None:
    conforming = _worker(_feature_flags()).model_copy(
        update={"sampler_execution_contract_version": SamplerExecutionContractVersion.V1},
    )
    legacy = _worker(_feature_flags())

    assert union_image_worker_feature_flags([conforming, legacy]).sampler_execution_contract_version is None
    assert (
        union_image_worker_feature_flags([conforming, conforming]).sampler_execution_contract_version
        is SamplerExecutionContractVersion.V1
    )


INCOMPATIBLE_FEATURE_CASES: list[tuple[str, ImageGenerationFeatureFlags, str]] = [
    ("extra_texts", _feature_flags(extra_texts=True), "extra_texts"),
    ("extra_source_images", _feature_flags(extra_source_images=True), "extra_source_images"),
    (
        "baselines",
        _feature_flags(baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl]),
        "unsupported_baseline",
    ),
    ("clip_skip", _feature_flags(clip_skip=True), "clip_skip"),
    ("hires_fix", _feature_flags(hires_fix=True), "hires_fix"),
    ("tiling", _feature_flags(tiling=True), "tiling"),
    ("schedulers", _feature_flags(schedulers=[KNOWN_IMAGE_SCHEDULERS.karras]), "schedulers"),
    ("samplers", _feature_flags(samplers=[KNOWN_IMAGE_SAMPLERS.k_euler]), "samplers"),
    (
        "sampler_solver_knobs",
        _feature_flags(sampler_solver_knobs=[SAMPLER_SOLVER_KNOB.eta]),
        "sampler_solver_knobs",
    ),
    ("flow_shift", _feature_flags(flow_shift=True), "flow_shift"),
    ("transparent", _feature_flags(transparent=True), "transparent"),
    (
        "controlnets_feature_flags",
        _feature_flags(
            controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.canny]),
        ),
        "controlnets",
    ),
    ("post_processing", _feature_flags(post_processing=["RealESRGAN_x4plus"]), "post_processing"),
    (
        "source_processing",
        _feature_flags(source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.img2img]),
        "source_processing",
    ),
    ("workflows", _feature_flags(workflows=[KNOWN_IMAGE_WORKFLOWS.qr_code]), "workflows"),
    ("tis", _feature_flags(tis=[KNOWN_AUX_MODEL_SOURCE.HORDELING]), "tis"),
    ("loras", _feature_flags(loras=[KNOWN_AUX_MODEL_SOURCE.CIVITAI]), "loras"),
]


@pytest.mark.parametrize(("field_name", "requested_features", "expected_reason"), INCOMPATIBLE_FEATURE_CASES)
def test_each_image_feature_field_is_compared_directionally(
    field_name: str,
    requested_features: ImageGenerationFeatureFlags,
    expected_reason: str,
) -> None:
    """Reject each required feature when the worker does not advertise it."""
    worker = _worker(_feature_flags())

    reasons = worker.reasons_not_capable_of_features(requested_features)

    assert reasons is not None, field_name
    assert expected_reason in {reason.value for reason in reasons}


@pytest.mark.parametrize(("field_name", "requested_features", "_expected_reason"), INCOMPATIBLE_FEATURE_CASES)
def test_each_image_feature_field_accepts_an_exactly_matching_worker(
    field_name: str,
    requested_features: ImageGenerationFeatureFlags,
    _expected_reason: str,
) -> None:
    """Accept every required feature when the worker advertises the same value."""
    assert _worker(requested_features).is_capable_of_features(requested_features), field_name


def test_image_feature_compatibility_registry_covers_the_canonical_model() -> None:
    """Require an explicit comparison policy for every canonical feature field."""
    requested_features = _feature_flags()
    compatibility_checks = _worker(requested_features)._get_image_feature_compatibility_checks(requested_features)

    assert set(compatibility_checks) == set(ImageGenerationFeatureFlags.model_fields)


def test_wrong_generation_feature_type_is_not_reported_capable() -> None:
    """Reject a feature model from a different generation domain."""
    worker = _worker(_feature_flags())

    reasons = worker.reasons_not_capable_of_features(GenerationFeatureFlags())

    assert reasons is not None
    assert {reason.value for reason in reasons} == {"unsupported_generation_type"}
    assert not worker.is_capable_of_features(GenerationFeatureFlags())


@pytest.mark.parametrize(
    ("requested_features", "map_factory", "expected_reason"),
    [
        (
            _feature_flags(samplers=[KNOWN_IMAGE_SAMPLERS.k_euler]),
            lambda baseline: PerBaselineFeatureFlags(samplers_map={baseline: [KNOWN_IMAGE_SAMPLERS.k_euler]}),
            "samplers",
        ),
        (
            _feature_flags(schedulers=[KNOWN_IMAGE_SCHEDULERS.karras]),
            lambda baseline: PerBaselineFeatureFlags(schedulers_map={baseline: [KNOWN_IMAGE_SCHEDULERS.karras]}),
            "schedulers",
        ),
        (
            _feature_flags(tiling=True),
            lambda baseline: PerBaselineFeatureFlags(tiling_map={baseline: True}),
            "tiling",
        ),
        (
            _feature_flags(hires_fix=True),
            lambda baseline: PerBaselineFeatureFlags(hires_fix_map={baseline: True}),
            "hires_fix",
        ),
        (
            _feature_flags(transparent=True),
            lambda baseline: PerBaselineFeatureFlags(transparent_map={baseline: True}),
            "transparent",
        ),
        (
            _feature_flags(
                controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.canny]),
            ),
            lambda baseline: PerBaselineFeatureFlags(controlnet_map={baseline: True}),
            "controlnets",
        ),
        (
            _feature_flags(tis=[KNOWN_AUX_MODEL_SOURCE.HORDELING]),
            lambda baseline: PerBaselineFeatureFlags(tis_map={baseline: True}),
            "tis",
        ),
        (
            _feature_flags(loras=[KNOWN_AUX_MODEL_SOURCE.CIVITAI]),
            lambda baseline: PerBaselineFeatureFlags(loras_map={baseline: True}),
            "loras",
        ),
    ],
)
def test_populated_per_baseline_maps_are_exhaustive(
    requested_features: ImageGenerationFeatureFlags,
    map_factory: Callable[[KNOWN_IMAGE_GENERATION_BASELINE], PerBaselineFeatureFlags],
    expected_reason: str,
) -> None:
    """Treat a requested baseline omitted from a populated map as unsupported."""
    worker = _worker(
        requested_features,
        per_baseline_features=map_factory(KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl),
    )

    reasons = worker.reasons_not_capable_of_features(requested_features)

    assert reasons is not None
    assert expected_reason in {reason.value for reason in reasons}


@pytest.mark.parametrize(
    ("requested_features", "per_baseline_features", "expected_reason"),
    [
        (
            _feature_flags(samplers=[KNOWN_IMAGE_SAMPLERS.k_euler]),
            PerBaselineFeatureFlags(
                samplers_map={
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [KNOWN_IMAGE_SAMPLERS.k_euler],
                },
            ),
            "samplers",
        ),
        (
            _feature_flags(schedulers=[KNOWN_IMAGE_SCHEDULERS.karras]),
            PerBaselineFeatureFlags(
                schedulers_map={
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [KNOWN_IMAGE_SCHEDULERS.karras],
                },
            ),
            "schedulers",
        ),
        (
            _feature_flags(tiling=True),
            PerBaselineFeatureFlags(
                tiling_map={KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True},
            ),
            "tiling",
        ),
        (
            _feature_flags(hires_fix=True),
            PerBaselineFeatureFlags(
                hires_fix_map={KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True},
            ),
            "hires_fix",
        ),
        (
            _feature_flags(transparent=True),
            PerBaselineFeatureFlags(
                transparent_map={KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True},
            ),
            "transparent",
        ),
    ],
)
def test_per_baseline_maps_cannot_widen_the_flat_advertisement(
    requested_features: ImageGenerationFeatureFlags,
    per_baseline_features: PerBaselineFeatureFlags,
    expected_reason: str,
) -> None:
    """Use per-baseline maps only to narrow the canonical flat feature set."""
    worker = _worker(_feature_flags(), per_baseline_features=per_baseline_features)

    reasons = worker.reasons_not_capable_of_features(requested_features)

    assert reasons is not None
    assert expected_reason in {reason.value for reason in reasons}


@pytest.mark.parametrize(
    "requested_features",
    [
        _feature_flags(
            controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.canny]),
        ),
        _feature_flags(
            controlnets_feature_flags=ControlnetFeatureFlags(
                controlnets=[KNOWN_IMAGE_CONTROLNETS.canny],
                image_is_control=True,
            ),
        ),
        _feature_flags(
            controlnets_feature_flags=ControlnetFeatureFlags(
                controlnets=[KNOWN_IMAGE_CONTROLNETS.canny],
                return_control_map=True,
            ),
        ),
    ],
)
def test_controlnet_type_and_modes_are_independent_requirements(
    requested_features: ImageGenerationFeatureFlags,
) -> None:
    """Require exact ControlNet types and each optional ControlNet mode."""
    unsupported = _feature_flags(
        controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.depth]),
    )

    reasons = _worker(unsupported).reasons_not_capable_of_features(requested_features)

    assert reasons is not None
    assert "controlnets" in {reason.value for reason in reasons}
    assert _worker(requested_features).is_capable_of_features(requested_features)


@pytest.mark.parametrize("source_processing", list(KNOWN_IMAGE_SOURCE_PROCESSING))
def test_every_source_processing_value_uses_exact_subset_semantics(
    source_processing: KNOWN_IMAGE_SOURCE_PROCESSING,
) -> None:
    """Compare every known source-processing value exactly."""
    requested_features = _feature_flags(source_processing=[source_processing])

    assert _worker(requested_features).is_capable_of_features(requested_features)
    assert not _worker(_feature_flags()).is_capable_of_features(requested_features)


@pytest.mark.parametrize("workflow", list(KNOWN_IMAGE_WORKFLOWS))
def test_every_workflow_value_uses_exact_subset_semantics(workflow: KNOWN_IMAGE_WORKFLOWS) -> None:
    """Compare every known workflow value exactly."""
    requested_features = _feature_flags(workflows=[workflow])

    assert _worker(requested_features).is_capable_of_features(requested_features)
    assert not _worker(_feature_flags()).is_capable_of_features(requested_features)


@pytest.mark.parametrize("sampler_solver_knob", list(SAMPLER_SOLVER_KNOB))
def test_every_sampler_solver_knob_uses_exact_subset_semantics(
    sampler_solver_knob: SAMPLER_SOLVER_KNOB,
) -> None:
    """Compare every known sampler solver knob exactly."""
    requested_features = _feature_flags(sampler_solver_knobs=[sampler_solver_knob])

    assert _worker(requested_features).is_capable_of_features(requested_features)
    assert not _worker(_feature_flags()).is_capable_of_features(requested_features)


@pytest.mark.parametrize("controlnet_type", list(KNOWN_IMAGE_CONTROLNETS))
@pytest.mark.parametrize(
    ("image_is_control", "return_control_map"), [(False, False), (True, False), (False, True), (True, True)]
)
def test_every_controlnet_value_and_mode_combination_is_compared(
    controlnet_type: KNOWN_IMAGE_CONTROLNETS,
    image_is_control: bool,
    return_control_map: bool,
) -> None:
    """Compare each known ControlNet type across its independent mode flags."""
    requested_features = _feature_flags(
        controlnets_feature_flags=ControlnetFeatureFlags(
            controlnets=[controlnet_type],
            image_is_control=image_is_control,
            return_control_map=return_control_map,
        ),
    )

    assert _worker(requested_features).is_capable_of_features(requested_features)
    assert not _worker(_feature_flags()).is_capable_of_features(requested_features)


@pytest.mark.parametrize(
    ("field_name", "custom_value"),
    [
        ("samplers", "future-sampler"),
        ("schedulers", "future-scheduler"),
        ("source_processing", "future-source-processing"),
        ("workflows", "future-workflow"),
        ("post_processing", "future-post-processor"),
        ("tis", "future-ti-source"),
        ("loras", "future-lora-source"),
    ],
)
def test_unknown_string_features_require_exact_advertisement(field_name: str, custom_value: str) -> None:
    """Fail closed for forward-added string values until a worker advertises them."""
    requested_features = _feature_flags(**{field_name: [custom_value]})

    assert _worker(requested_features).is_capable_of_features(requested_features)
    assert not _worker(_feature_flags()).is_capable_of_features(requested_features)


@pytest.mark.parametrize("field_name", ["tis", "loras"])
def test_auxiliary_model_sources_use_subset_semantics(field_name: str) -> None:
    """Require workers to advertise every requested auxiliary-model source."""
    requested_features = _feature_flags(**{field_name: [KNOWN_AUX_MODEL_SOURCE.CIVITAI, "future-source"]})
    worker_features = _feature_flags(**{field_name: [KNOWN_AUX_MODEL_SOURCE.CIVITAI]})

    reasons = _worker(worker_features).reasons_not_capable_of_features(requested_features)

    assert reasons is not None
    assert field_name in {reason.value for reason in reasons}


def test_image_feature_union_is_monotone_for_worker_support() -> None:
    """Support each input requirement with the union of their advertised feature sets."""
    first_features = _feature_flags(
        samplers=[KNOWN_IMAGE_SAMPLERS.k_euler],
        source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.txt2img],
        loras=[KNOWN_AUX_MODEL_SOURCE.CIVITAI],
        sampler_solver_knobs=[SAMPLER_SOLVER_KNOB.eta],
        transparent=True,
    )
    second_features = _feature_flags(
        baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl],
        schedulers=[KNOWN_IMAGE_SCHEDULERS.karras],
        source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.img2img],
        workflows=[KNOWN_IMAGE_WORKFLOWS.qr_code],
        flow_shift=True,
    )

    combined_features = union_image_generation_feature_flags([first_features, second_features])
    worker = _worker(combined_features)

    assert worker.is_capable_of_features(first_features)
    assert worker.is_capable_of_features(second_features)
    assert union_image_generation_feature_flags([first_features]) == first_features


def test_worker_profile_union_preserves_per_baseline_restrictions() -> None:
    """Union each baseline independently when every input supplies an exhaustive restriction map."""
    sd1 = KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1
    sdxl = KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl
    first = _worker(
        _feature_flags(
            baselines=[sd1, sdxl],
            samplers=[KNOWN_IMAGE_SAMPLERS.k_euler],
            controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.canny]),
        ),
        per_baseline_features=PerBaselineFeatureFlags(
            samplers_map={sd1: [KNOWN_IMAGE_SAMPLERS.k_euler]},
            controlnet_map={sd1: True, sdxl: False},
        ),
    )
    second = _worker(
        _feature_flags(
            baselines=[sd1, sdxl],
            samplers=[KNOWN_IMAGE_SAMPLERS.k_lms],
            controlnets_feature_flags=ControlnetFeatureFlags(controlnets=[KNOWN_IMAGE_CONTROLNETS.canny]),
        ),
        per_baseline_features=PerBaselineFeatureFlags(
            samplers_map={sdxl: [KNOWN_IMAGE_SAMPLERS.k_lms]},
            controlnet_map={sd1: False, sdxl: True},
        ),
    )

    combined = union_image_worker_feature_flags([first, second])

    assert combined.per_baseline_feature_flags is not None
    assert combined.per_baseline_feature_flags.samplers_map == {
        sd1: [KNOWN_IMAGE_SAMPLERS.k_euler],
        sdxl: [KNOWN_IMAGE_SAMPLERS.k_lms],
    }
    assert combined.per_baseline_feature_flags.controlnet_map == {sd1: True, sdxl: True}


def test_worker_profile_union_expands_an_unrestricted_member_only_on_its_baselines() -> None:
    """A flat member contributes its values without widening another member's baseline support."""
    restricted = _worker(
        _feature_flags(samplers=[KNOWN_IMAGE_SAMPLERS.k_euler]),
        per_baseline_features=PerBaselineFeatureFlags(
            samplers_map={
                KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [KNOWN_IMAGE_SAMPLERS.k_euler],
            },
        ),
    )
    unrestricted = _worker(_feature_flags(samplers=[KNOWN_IMAGE_SAMPLERS.k_lms]))

    combined = union_image_worker_feature_flags([restricted, unrestricted])

    assert combined.per_baseline_feature_flags is not None
    assert combined.per_baseline_feature_flags.samplers_map == {
        KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: [
            KNOWN_IMAGE_SAMPLERS.k_euler,
            KNOWN_IMAGE_SAMPLERS.k_lms,
        ],
    }


def test_worker_profile_union_rejects_empty_input() -> None:
    """An empty pool cannot produce a valid profile because image baselines are required."""
    with pytest.raises(ValueError, match="At least one image worker"):
        union_image_worker_feature_flags([])


def test_image_feature_intersection_retains_only_common_support() -> None:
    """Retain only values and boolean capabilities advertised by every feature set."""
    first_features = _feature_flags(
        samplers=[KNOWN_IMAGE_SAMPLERS.k_euler, KNOWN_IMAGE_SAMPLERS.k_lms],
        source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.txt2img, KNOWN_IMAGE_SOURCE_PROCESSING.img2img],
        clip_skip=True,
        tiling=True,
        sampler_solver_knobs=[SAMPLER_SOLVER_KNOB.eta, SAMPLER_SOLVER_KNOB.order],
        flow_shift=True,
        transparent=True,
    )
    second_features = _feature_flags(
        samplers=[KNOWN_IMAGE_SAMPLERS.k_euler],
        source_processing=[KNOWN_IMAGE_SOURCE_PROCESSING.txt2img],
        clip_skip=True,
        tiling=False,
        sampler_solver_knobs=[SAMPLER_SOLVER_KNOB.eta],
        flow_shift=True,
        transparent=False,
    )

    common_features = intersect_image_generation_feature_flags([first_features, second_features])

    assert common_features.samplers == [KNOWN_IMAGE_SAMPLERS.k_euler]
    assert common_features.source_processing == [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img]
    assert common_features.clip_skip is True
    assert common_features.tiling is False
    assert common_features.sampler_solver_knobs == [SAMPLER_SOLVER_KNOB.eta]
    assert common_features.flow_shift is True
    assert common_features.transparent is False
    assert _worker(first_features).is_capable_of_features(common_features)
    assert _worker(second_features).is_capable_of_features(common_features)


def test_image_feature_intersection_rejects_disjoint_baselines() -> None:
    """Reject an intersection that cannot describe any executable image baseline."""
    with pytest.raises(ValueError, match="share at least one baseline"):
        intersect_image_generation_feature_flags(
            [
                _feature_flags(baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1]),
                _feature_flags(baselines=[KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl]),
            ],
        )
