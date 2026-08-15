"""Verify canonical feature extraction from image generation parameters."""

from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image.constraints import KNOWN_SAMPLER_SOLVER_TYPES, SAMPLER_SOLVER_KNOB
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    KNOWN_IMAGE_WORKFLOWS,
)
from horde_sdk.generation_parameters.image.object_models import (
    ControlnetGenerationParameters,
    CustomWorkflowGenerationParameters,
    ExtraTextEntry,
    ImageGenerationComponentContainer,
    ImageGenerationParameters,
    LoRaEntry,
    RemixGenerationParameters,
    RemixImageEntry,
    TIEntry,
    image_parameters_to_feature_flags,
)


def test_image_parameter_extraction_preserves_all_component_feature_dimensions(
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    """Preserve auxiliary sources, custom inputs, and remix inputs in the canonical feature set."""
    parameters = simple_image_generation_parameters.model_copy(
        update={
            "source_processing": KNOWN_IMAGE_SOURCE_PROCESSING.remix,
            "base_params": simple_image_generation_parameters.base_params.model_copy(
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
                },
            ),
            "additional_params": ImageGenerationComponentContainer(
                components=[
                    RemixGenerationParameters(
                        source_image=b"source",
                        remix_images=[RemixImageEntry(image=b"additional")],
                    ),
                    LoRaEntry(
                        name="lora",
                        remote_version_id=None,
                        source=KNOWN_AUX_MODEL_SOURCE.CIVITAI,
                    ),
                    TIEntry(
                        name="embedding",
                        remote_version_id=None,
                        source=KNOWN_AUX_MODEL_SOURCE.HORDELING,
                    ),
                    CustomWorkflowGenerationParameters(
                        custom_workflow_name=KNOWN_IMAGE_WORKFLOWS.qr_code,
                        extra_texts=[ExtraTextEntry(text="encoded text")],
                    ),
                ],
            ),
        },
    )

    features = image_parameters_to_feature_flags(parameters)

    assert features.clip_skip is True
    assert features.sampler_solver_knobs == list(SAMPLER_SOLVER_KNOB)
    assert features.flow_shift is True
    assert features.transparent is True
    assert features.extra_source_images is True
    assert features.extra_texts is True
    assert features.loras == [KNOWN_AUX_MODEL_SOURCE.CIVITAI]
    assert features.tis == [KNOWN_AUX_MODEL_SOURCE.HORDELING]
    assert features.workflows == [KNOWN_IMAGE_WORKFLOWS.qr_code]


def test_clip_skip_default_does_not_require_clip_skip_support(
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    """Treat the first CLIP layer as the no-skip representation in either sign convention."""
    for clip_skip in (-1, 1, None):
        parameters = simple_image_generation_parameters.model_copy(
            update={
                "base_params": simple_image_generation_parameters.base_params.model_copy(
                    update={"clip_skip": clip_skip},
                ),
            },
        )
        assert image_parameters_to_feature_flags(parameters).clip_skip is False


def test_control_map_distinguishes_precomputed_control_from_source_image(
    simple_image_generation_parameters: ImageGenerationParameters,
) -> None:
    """Describe a precomputed control map independently from an image requiring annotation."""
    source_parameters = simple_image_generation_parameters.model_copy(
        update={
            "additional_params": ImageGenerationComponentContainer(
                components=[
                    ControlnetGenerationParameters(
                        controlnet_type=KNOWN_IMAGE_CONTROLNETS.canny,
                        source_image=b"source",
                        control_map=None,
                    ),
                ],
            ),
        },
    )
    control_map_parameters = source_parameters.model_copy(
        update={
            "additional_params": ImageGenerationComponentContainer(
                components=[
                    ControlnetGenerationParameters(
                        controlnet_type=KNOWN_IMAGE_CONTROLNETS.canny,
                        source_image=None,
                        control_map=b"control map",
                    ),
                ],
            ),
        },
    )

    source_features = image_parameters_to_feature_flags(source_parameters).controlnets_feature_flags
    control_map_features = image_parameters_to_feature_flags(control_map_parameters).controlnets_feature_flags

    assert source_features is not None
    assert source_features.image_is_control is False
    assert control_map_features is not None
    assert control_map_features.image_is_control is True
