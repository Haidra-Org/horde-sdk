from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
)
from horde_sdk.generation_parameters.image import (
    BasicImageGenerationParameters,
    ControlnetGenerationParameters,
    HiresFixGenerationParameters,
    Image2ImageGenerationParameters,
    ImageGenerationParameters,
    LoRaEntry,
    RemixGenerationParameters,
    TIEntry,
)
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_SOURCE_PROCESSING,
    LORA_TRIGGER_INJECT_CHOICE,
    TI_TRIGGER_INJECT_CHOICE,
)
from horde_sdk.worker.consts import REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE
from horde_sdk.worker.dispatch.ai_horde.image.convert import convert_image_job_pop_response_to_parameters
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeR2DispatchParameters


def assert_features_selected(
    generation_parameters: ImageGenerationParameters,
    *,
    control_net: bool = False,
    custom_workflow: bool = False,
    hires_fix: bool = False,
    img2img: bool = False,
    remix: bool = False,
    loras: bool = False,
    tis: bool = False,
) -> None:
    """Confirm that the selected features are present if intended, and not present if deselected."""
    additional_params = generation_parameters.additional_params

    if additional_params is None:
        assert not (control_net or custom_workflow or hires_fix or img2img or remix or loras or tis)
        return

    assert (additional_params.controlnet_params is not None) == control_net
    assert bool(additional_params.custom_workflows_params) == custom_workflow
    assert (additional_params.hires_fix_params is not None) == hires_fix
    assert (additional_params.image2image_params is not None) == img2img
    assert (additional_params.remix_params is not None) == remix
    assert bool(additional_params.lora_params) == loras
    assert bool(additional_params.ti_params) == tis


def assert_base_image_generation_parameters(
    base_params: BasicImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm all common image generation parameters are correctly mapped."""
    assert isinstance(base_params, BasicImageGenerationParameters)
    assert base_params.model == api_response.model
    assert base_params.prompt == api_response.payload.prompt
    assert base_params.seed == api_response.payload.seed

    if not api_response.payload.hires_fix:
        assert base_params.steps == api_response.payload.ddim_steps


def assert_image_generation_parameters(
    generation_parameters: ImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
    source_processing: str,
) -> None:
    """Confirm all common image generation parameters are correctly mapped."""
    assert isinstance(generation_parameters, ImageGenerationParameters)

    assert isinstance(generation_parameters.base_params, BasicImageGenerationParameters)
    assert_base_image_generation_parameters(generation_parameters.base_params, api_response)

    assert generation_parameters.batch_size == api_response.payload.n_iter
    assert generation_parameters.source_processing == source_processing


def assert_image_dispatch_parameters(
    dispatch_parameters: AIHordeR2DispatchParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm all common image dispatch parameters are correctly mapped."""
    assert isinstance(dispatch_parameters, AIHordeR2DispatchParameters)
    assert dispatch_parameters.generation_ids == api_response.ids
    assert (
        dispatch_parameters.no_valid_request_found_reasons
        == api_response.skipped
        == ImageGenerateJobPopSkippedStatus()
    )
    assert dispatch_parameters.source_image_fallback_choice == REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.TXT2IMG_FALLBACK


def assert_common_image_parameters(
    image_generation_parameters: ImageGenerationParameters,
    dispatch_parameters: AIHordeR2DispatchParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm all common image generation and dispatch parameters are correctly mapped."""
    source_processing = api_response.source_processing
    assert_image_generation_parameters(image_generation_parameters, api_response, source_processing)
    assert_image_dispatch_parameters(dispatch_parameters, api_response)


def test_convert_image_job_pop_response_to_parameters(
    simple_image_gen_job_pop_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response,
        model_reference_manager=model_reference_manager,
    )
    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response,
    )
    assert_features_selected(generation_parameters)


def test_convert_image_job_pop_response_to_parameters_img2img(
    simple_image_gen_job_pop_response_img2img: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for img2img."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_img2img,
        model_reference_manager=model_reference_manager,
    )
    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_img2img,
    )
    assert_features_selected(generation_parameters, img2img=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.image2image_params, Image2ImageGenerationParameters)
    assert isinstance(additional_params.image2image_params.source_image, bytes)
    assert additional_params.image2image_params.source_mask is None


def test_convert_image_job_pop_response_to_parameters_img2img_masked(
    simple_image_gen_job_pop_response_img2img_masked: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for img2img inpainting."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_img2img_masked,
        model_reference_manager=model_reference_manager,
    )
    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_img2img_masked,
    )

    assert_features_selected(generation_parameters, img2img=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.image2image_params, Image2ImageGenerationParameters)
    assert isinstance(additional_params.image2image_params.source_image, bytes)
    assert isinstance(additional_params.image2image_params.source_mask, bytes)


def test_convert_image_job_pop_response_to_parameters_inpainting(
    simple_image_gen_job_pop_response_inpainting: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for inpainting."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_inpainting,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_inpainting,
    )

    assert_features_selected(generation_parameters, img2img=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.image2image_params, Image2ImageGenerationParameters)
    assert isinstance(additional_params.image2image_params.source_image, bytes)
    assert isinstance(additional_params.image2image_params.source_mask, bytes)


def test_convert_image_job_pop_response_to_parameters_outpainting_alpha(
    simple_image_gen_job_pop_response_outpainting_alpha: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for outpainting with alpha."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_outpainting_alpha,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_outpainting_alpha,
    )

    assert generation_parameters.source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.inpainting

    assert_features_selected(generation_parameters, img2img=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.image2image_params, Image2ImageGenerationParameters)
    assert isinstance(additional_params.image2image_params.source_image, bytes)


def test_convert_image_job_pop_response_to_parameters_controlnet_openpose(
    simple_image_gen_job_pop_response_controlnet_openpose: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for controlnet with openpose."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_controlnet_openpose,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_controlnet_openpose,
    )

    assert_features_selected(generation_parameters, control_net=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.controlnet_params, ControlnetGenerationParameters)
    assert additional_params.controlnet_params.control_map is not None
    assert isinstance(additional_params.controlnet_params.control_map, bytes)
    assert additional_params.controlnet_params.source_image is None


def test_convert_image_job_pop_response_to_parameters_hires_fix(
    simple_image_gen_job_pop_response_hires_fix: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for hires fix."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_hires_fix,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_hires_fix,
    )

    assert_features_selected(generation_parameters, hires_fix=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.hires_fix_params, HiresFixGenerationParameters)

    assert additional_params.hires_fix_params.first_pass is not None
    assert_base_image_generation_parameters(
        base_params=additional_params.hires_fix_params.first_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix,
    )

    assert additional_params.hires_fix_params.second_pass is not None
    assert_base_image_generation_parameters(
        base_params=additional_params.hires_fix_params.second_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix,
    )


def test_convert_image_job_pop_response_to_parameters_hires_fix_denoise(
    simple_image_gen_job_pop_response_hires_fix_denoise: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for hires fix with denoise."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_hires_fix_denoise,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_hires_fix_denoise,
    )

    assert_features_selected(generation_parameters, hires_fix=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.hires_fix_params, HiresFixGenerationParameters)

    assert additional_params.hires_fix_params.first_pass is not None
    assert_base_image_generation_parameters(
        base_params=additional_params.hires_fix_params.first_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix_denoise,
    )

    assert additional_params.hires_fix_params.second_pass is not None
    assert_base_image_generation_parameters(
        base_params=additional_params.hires_fix_params.second_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix_denoise,
    )
    assert (
        additional_params.hires_fix_params.second_pass.denoising_strength
        == simple_image_gen_job_pop_response_hires_fix_denoise.payload.hires_fix_denoising_strength
    )


def assert_lora_parameters(
    generation_parameters: ImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm that LoRa parameters are correctly mapped."""
    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.lora_params, list)
    assert len(additional_params.lora_params) > 0

    assert api_response.payload.loras is not None

    assert len(additional_params.lora_params) == len(api_response.payload.loras)

    for i in range(len(additional_params.lora_params)):
        assert isinstance(additional_params.lora_params[i], LoRaEntry)
        assert additional_params.lora_params[i].lora_inject_trigger_choice == LORA_TRIGGER_INJECT_CHOICE.NO_INJECT

        if api_response.payload.loras[i].is_version:
            assert additional_params.lora_params[i].remote_version_id is not None
            assert additional_params.lora_params[i].remote_version_id == api_response.payload.loras[i].name
            assert additional_params.lora_params[i].name is None
            assert additional_params.lora_params[i].model_strength
        else:
            assert additional_params.lora_params[i].name is not None
            assert additional_params.lora_params[i].name == api_response.payload.loras[i].name
            assert additional_params.lora_params[i].remote_version_id is None


def test_convert_image_job_pop_response_to_parameters_loras(
    simple_image_gen_job_pop_response_loras: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for LoRAS."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_loras,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_loras,
    )

    assert_features_selected(generation_parameters, loras=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.lora_params, list)
    assert len(additional_params.lora_params) == 1

    assert simple_image_gen_job_pop_response_loras.payload.loras is not None

    assert_lora_parameters(generation_parameters, simple_image_gen_job_pop_response_loras)


def assert_ti_parameters(
    generation_parameters: ImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm that TI parameters are correctly mapped."""
    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.ti_params, list)
    assert len(additional_params.ti_params) > 0

    assert api_response.payload.tis is not None

    assert len(additional_params.ti_params) == len(api_response.payload.tis)

    for i in range(len(additional_params.ti_params)):
        assert isinstance(additional_params.ti_params[i], TIEntry)

        assert additional_params.ti_params[i].name == api_response.payload.tis[i].name


def test_convert_image_job_pop_response_to_parameters_tis(
    simple_image_gen_job_pop_response_tis: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for TIs."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_tis,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_tis,
    )

    assert_features_selected(generation_parameters, tis=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.ti_params, list)
    assert len(additional_params.ti_params) == 1

    assert simple_image_gen_job_pop_response_tis.payload.tis is not None

    assert isinstance(additional_params.ti_params[0], TIEntry)

    for i in range(len(additional_params.ti_params)):
        assert isinstance(additional_params.ti_params[i], TIEntry)

        assert additional_params.ti_params[i].ti_inject_trigger_choice == TI_TRIGGER_INJECT_CHOICE.NEGATIVE_PROMPT
        assert additional_params.ti_params[i].name == simple_image_gen_job_pop_response_tis.payload.tis[i].name


def test_convert_image_job_pop_response_to_parameters_remix(
    simple_image_gen_job_pop_response_remix: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters for remix."""
    generation_parameters, dispatch_parameters = convert_image_job_pop_response_to_parameters(
        api_response=simple_image_gen_job_pop_response_remix,
        model_reference_manager=model_reference_manager,
    )

    assert_common_image_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_image_gen_job_pop_response_remix,
    )

    assert_features_selected(generation_parameters, remix=True)

    additional_params = generation_parameters.additional_params

    assert isinstance(additional_params.remix_params, RemixGenerationParameters)
