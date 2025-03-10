import PIL.Image
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
    assert (generation_parameters.controlnet_params is not None) == control_net
    assert (generation_parameters.custom_workflow_params is not None) == custom_workflow
    assert (generation_parameters.hires_fix_params is not None) == hires_fix
    assert (generation_parameters.img2img_params is not None) == img2img
    assert (generation_parameters.remix_params is not None) == remix
    assert (generation_parameters.loras is not None) == loras
    assert (generation_parameters.tis is not None) == tis


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

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert generation_parameters.img2img_params.source_mask is None


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

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert isinstance(generation_parameters.img2img_params.source_mask, PIL.Image.Image)


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

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert isinstance(generation_parameters.img2img_params.source_mask, PIL.Image.Image)


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

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)


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

    assert isinstance(generation_parameters.controlnet_params, ControlnetGenerationParameters)
    assert generation_parameters.controlnet_params.control_map is not None
    assert isinstance(generation_parameters.controlnet_params.control_map, PIL.Image.Image)
    assert generation_parameters.controlnet_params.source_image is None


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

    assert isinstance(generation_parameters.hires_fix_params, HiresFixGenerationParameters)

    assert generation_parameters.hires_fix_params.first_pass is not None
    assert_base_image_generation_parameters(
        base_params=generation_parameters.hires_fix_params.first_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix,
    )

    assert generation_parameters.hires_fix_params.second_pass is not None
    assert_base_image_generation_parameters(
        base_params=generation_parameters.hires_fix_params.second_pass,
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

    assert isinstance(generation_parameters.hires_fix_params, HiresFixGenerationParameters)

    assert generation_parameters.hires_fix_params.first_pass is not None
    assert_base_image_generation_parameters(
        base_params=generation_parameters.hires_fix_params.first_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix_denoise,
    )

    assert generation_parameters.hires_fix_params.second_pass is not None
    assert_base_image_generation_parameters(
        base_params=generation_parameters.hires_fix_params.second_pass,
        api_response=simple_image_gen_job_pop_response_hires_fix_denoise,
    )
    assert (
        generation_parameters.hires_fix_params.second_pass.denoising_strength
        == simple_image_gen_job_pop_response_hires_fix_denoise.payload.hires_fix_denoising_strength
    )


def assert_lora_parameters(
    generation_parameters: ImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm that LoRa parameters are correctly mapped."""
    assert isinstance(generation_parameters.loras, list)
    assert len(generation_parameters.loras) > 0

    assert api_response.payload.loras is not None

    assert len(generation_parameters.loras) == len(api_response.payload.loras)

    for i in range(len(generation_parameters.loras)):
        assert isinstance(generation_parameters.loras[i], LoRaEntry)
        assert generation_parameters.loras[i].lora_inject_trigger_choice == LORA_TRIGGER_INJECT_CHOICE.NO_INJECT

        if api_response.payload.loras[i].is_version:
            assert generation_parameters.loras[i].remote_version_id is not None
            assert generation_parameters.loras[i].remote_version_id == api_response.payload.loras[i].name
            assert generation_parameters.loras[i].name is None
            assert generation_parameters.loras[i].model_strength
        else:
            assert generation_parameters.loras[i].name is not None
            assert generation_parameters.loras[i].name == api_response.payload.loras[i].name
            assert generation_parameters.loras[i].remote_version_id is None


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

    assert isinstance(generation_parameters.loras, list)
    assert len(generation_parameters.loras) == 1

    assert simple_image_gen_job_pop_response_loras.payload.loras is not None

    assert_lora_parameters(generation_parameters, simple_image_gen_job_pop_response_loras)


def assert_ti_parameters(
    generation_parameters: ImageGenerationParameters,
    api_response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm that TI parameters are correctly mapped."""
    assert isinstance(generation_parameters.tis, list)
    assert len(generation_parameters.tis) > 0

    assert api_response.payload.tis is not None

    assert len(generation_parameters.tis) == len(api_response.payload.tis)

    for i in range(len(generation_parameters.tis)):
        assert isinstance(generation_parameters.tis[i], TIEntry)

        assert generation_parameters.tis[i].name == api_response.payload.tis[i].name


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

    assert isinstance(generation_parameters.tis, list)
    assert len(generation_parameters.tis) == 1

    assert simple_image_gen_job_pop_response_tis.payload.tis is not None

    assert isinstance(generation_parameters.tis[0], TIEntry)

    for i in range(len(generation_parameters.tis)):
        assert isinstance(generation_parameters.tis[i], TIEntry)

        assert generation_parameters.tis[i].ti_inject_trigger_choice == TI_TRIGGER_INJECT_CHOICE.NEGATIVE_PROMPT
        assert generation_parameters.tis[i].name == simple_image_gen_job_pop_response_tis.payload.tis[i].name


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

    assert isinstance(generation_parameters.remix_params, RemixGenerationParameters)
