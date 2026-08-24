"""Verify image feature extraction at the AI-Horde dispatch boundary."""

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import ImageGenerateJobPopRequest, ImageGenerateJobPopResponse
from horde_sdk.ai_horde_api.apimodels.base import ExtraTextEntry
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image.constraints import KNOWN_SAMPLER_SOLVER_TYPES
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    KNOWN_IMAGE_WORKFLOWS,
)
from horde_sdk.generation_parameters.image.object_models import (
    ControlnetFeatureFlags,
    ImageGenerationFeatureFlags,
    image_parameters_to_feature_flags,
)
from horde_sdk.generation_parameters.image.sampler_work import SamplerExecutionContractVersion
from horde_sdk.worker.dispatch.ai_horde.bridge_data import ImageWorkerBridgeData
from horde_sdk.worker.dispatch.ai_horde.image.convert import (
    AI_HORDE_EXTENDED_IMAGE_CONTROL_TYPES,
    apply_image_worker_feature_flags_to_pop_request,
    convert_image_job_pop_response_to_parameters,
    image_job_pop_response_to_feature_flags,
    image_worker_bridge_data_to_feature_flags,
)
from horde_sdk.worker.feature_flags import ImageWorkerFeatureFlags, PerBaselineFeatureFlags


def _implementation_profile(
    *,
    control_types: list[KNOWN_IMAGE_CONTROLNETS | str] | None = None,
) -> ImageWorkerFeatureFlags:
    """Build exact implementation support for AI Horde projection tests."""
    baselines = [
        KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
        KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl,
    ]
    return ImageWorkerFeatureFlags(
        image_generation_feature_flags=ImageGenerationFeatureFlags(
            extra_source_images=True,
            baselines=baselines,
            schedulers=[],
            samplers=[],
            controlnets_feature_flags=(
                ControlnetFeatureFlags(
                    controlnets=control_types,
                    image_is_control=True,
                    return_control_map=True,
                )
                if control_types is not None
                else None
            ),
            post_processing=["RealESRGAN_x4plus"],
            source_processing=list(KNOWN_IMAGE_SOURCE_PROCESSING),
            workflows=[KNOWN_IMAGE_WORKFLOWS.qr_code],
            tis=[KNOWN_AUX_MODEL_SOURCE.HORDELING],
            loras=[KNOWN_AUX_MODEL_SOURCE.CIVITAI],
        ),
        per_baseline_feature_flags=PerBaselineFeatureFlags(
            controlnet_map=dict.fromkeys(baselines, True),
        ),
        sampler_execution_contract_version=SamplerExecutionContractVersion.V1,
    )


def _pop_request() -> ImageGenerateJobPopRequest:
    """Build a request whose non-feature values must survive feature projection."""
    return ImageGenerateJobPopRequest(
        name="feature-worker",
        bridge_agent="feature-worker:1:test",
        max_pixels=262144,
        models=["model-a"],
        threads=3,
        nsfw=False,
    )


def test_wire_and_converted_feature_extraction_agree_without_degradation(
    simple_image_gen_job_pop_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Produce the same canonical features before and after lossless conversion."""
    wire_features = image_job_pop_response_to_feature_flags(
        simple_image_gen_job_pop_response,
        resolved_baseline=KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
    )
    conversion_result = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response,
        model_reference_manager=model_reference_manager,
    )

    assert wire_features == image_parameters_to_feature_flags(conversion_result.generation_parameters)


def test_wire_and_converted_feature_extraction_agree_across_feature_families(
    simple_image_gen_job_pop_response_post_processing: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response_controlnet_openpose: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response_hires_fix: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response_loras: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response_tis: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response_remix: ImageGenerateJobPopResponse,
    simple_image_gen_job_pop_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Keep both adapters equivalent for every portable wire feature family."""
    workflow_response = simple_image_gen_job_pop_response.model_copy(
        update={
            "payload": simple_image_gen_job_pop_response.payload.model_copy(
                update={
                    "clip_skip": 2,
                    "sampler_eta": 0.5,
                    "sampler_s_noise": 0.9,
                    "sampler_s_churn": 1.0,
                    "sampler_s_tmin": 0.1,
                    "sampler_s_tmax": 1.0,
                    "sampler_solver_type": KNOWN_SAMPLER_SOLVER_TYPES.midpoint,
                    "sampler_order": 2,
                    "flow_shift": 3.0,
                    "transparent": True,
                    "workflow": KNOWN_IMAGE_WORKFLOWS.qr_code,
                    "extra_texts": [ExtraTextEntry(text="encoded text", reference="qr_text")],
                },
            ),
        },
    )
    response_corpus = [
        (simple_image_gen_job_pop_response_post_processing, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
        (simple_image_gen_job_pop_response_controlnet_openpose, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
        (simple_image_gen_job_pop_response_hires_fix, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
        (simple_image_gen_job_pop_response_loras, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
        (simple_image_gen_job_pop_response_tis, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
        (simple_image_gen_job_pop_response_remix, KNOWN_IMAGE_GENERATION_BASELINE.stable_cascade),
        (workflow_response, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1),
    ]

    for api_response, resolved_baseline in response_corpus:
        wire_features = image_job_pop_response_to_feature_flags(
            api_response,
            resolved_baseline=resolved_baseline,
        )
        conversion_result = convert_image_job_pop_response_to_parameters(
            api_response=api_response,
            model_reference_manager=model_reference_manager,
        )
        assert wire_features == image_parameters_to_feature_flags(conversion_result.generation_parameters)


def test_wire_features_remain_distinct_from_fault_tolerant_source_fallback(
    simple_image_gen_job_pop_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Keep accepted wire requirements distinct from the workload selected after fallback."""
    response_without_source = simple_image_gen_job_pop_response.model_copy(
        update={
            "source_processing": KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
            "source_image": None,
        },
    )

    wire_features = image_job_pop_response_to_feature_flags(
        response_without_source,
        resolved_baseline=KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
    )
    conversion_result = convert_image_job_pop_response_to_parameters(
        api_response=response_without_source,
        model_reference_manager=model_reference_manager,
    )
    execution_features = image_parameters_to_feature_flags(conversion_result.generation_parameters)

    assert wire_features.source_processing == [KNOWN_IMAGE_SOURCE_PROCESSING.img2img]
    assert execution_features.source_processing == [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img]


def test_bridge_choices_only_narrow_exact_implementation_support() -> None:
    """Operator choices remove gated features without inventing or broadening exact values."""
    implementation = _implementation_profile(control_types=list(KNOWN_IMAGE_CONTROLNETS))
    bridge_data = ImageWorkerBridgeData(
        models_to_load=["model-a"],
        allow_img2img=False,
        allow_inpainting=True,
        allow_controlnet=True,
        allow_sdxl_controlnet=True,
        allow_post_processing=False,
        allow_lora=False,
    )

    effective = image_worker_bridge_data_to_feature_flags(bridge_data, implementation)
    features = effective.image_generation_feature_flags

    assert features.source_processing == [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img]
    assert features.extra_source_images is False
    assert features.controlnets_feature_flags is None
    assert features.workflows is None
    assert features.post_processing is None
    assert features.loras is None
    assert features.tis == [KNOWN_AUX_MODEL_SOURCE.HORDELING]
    assert effective.per_baseline_feature_flags is not None
    assert effective.per_baseline_feature_flags.controlnet_map is not None
    assert not any(effective.per_baseline_feature_flags.controlnet_map.values())


def test_pop_projection_requires_complete_extended_controlnet_coverage() -> None:
    """Do not turn a subset of extended support into the AI Horde's all-extended boolean offer."""
    partial_profile = _implementation_profile(
        control_types=[KNOWN_IMAGE_CONTROLNETS.canny, KNOWN_IMAGE_CONTROLNETS.mlsd]
    )
    full_profile = _implementation_profile(control_types=list(KNOWN_IMAGE_CONTROLNETS))

    partial_request = apply_image_worker_feature_flags_to_pop_request(_pop_request(), partial_profile)
    full_request = apply_image_worker_feature_flags_to_pop_request(_pop_request(), full_profile)

    assert partial_request.allow_controlnet is True
    assert partial_request.allow_extended_controlnet is False
    assert full_request.allow_extended_controlnet is True
    assert {control_type.value for control_type in AI_HORDE_EXTENDED_IMAGE_CONTROL_TYPES}


def test_pop_projection_carries_sampler_execution_contract_version() -> None:
    projected = apply_image_worker_feature_flags_to_pop_request(_pop_request(), _implementation_profile())

    assert projected.sampler_execution_contract_version is SamplerExecutionContractVersion.V1


def test_pop_projection_preserves_non_feature_fields_and_baseline_restrictions() -> None:
    """Project canonical booleans while retaining identity, policy, limits and exact SDXL restrictions."""
    profile = _implementation_profile(control_types=list(KNOWN_IMAGE_CONTROLNETS))
    per_baseline = profile.per_baseline_feature_flags
    assert per_baseline is not None
    restricted_profile = profile.model_copy(
        update={
            "per_baseline_feature_flags": per_baseline.model_copy(
                update={
                    "controlnet_map": {
                        KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1: True,
                        KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl: False,
                    },
                },
            ),
        },
    )

    projected = apply_image_worker_feature_flags_to_pop_request(_pop_request(), restricted_profile)

    assert projected.models == ["model-a"]
    assert projected.max_pixels == 262144
    assert projected.threads == 3
    assert projected.nsfw is False
    assert projected.allow_img2img is True
    assert projected.allow_painting is True
    assert projected.allow_post_processing is True
    assert projected.allow_controlnet is True
    assert projected.allow_sdxl_controlnet is False
    assert projected.allow_lora is True


def test_pop_projection_includes_implicit_source_and_control_requirements() -> None:
    """Coarse source and ControlNet bits cover workflows that need them without naming a control type."""
    profile = _implementation_profile()
    features = profile.image_generation_feature_flags.model_copy(
        update={
            "extra_source_images": False,
            "source_processing": [KNOWN_IMAGE_SOURCE_PROCESSING.txt2img],
            "controlnets_feature_flags": None,
            "workflows": [KNOWN_IMAGE_WORKFLOWS.qr_code],
        },
    )
    workflow_profile = profile.model_copy(update={"image_generation_feature_flags": features})

    projected = apply_image_worker_feature_flags_to_pop_request(_pop_request(), workflow_profile)

    assert projected.allow_img2img is True
    assert projected.allow_controlnet is True


def test_pop_projection_does_not_advertise_sdxl_control_without_sdxl_support() -> None:
    """Flat ControlNet support cannot imply support for a baseline absent from the profile."""
    profile = _implementation_profile(control_types=list(KNOWN_IMAGE_CONTROLNETS))
    features = profile.image_generation_feature_flags.model_copy(
        update={"baselines": [KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1]},
    )
    sd1_profile = profile.model_copy(update={"image_generation_feature_flags": features})

    projected = apply_image_worker_feature_flags_to_pop_request(_pop_request(), sd1_profile)

    assert projected.allow_controlnet is True
    assert projected.allow_sdxl_controlnet is False
