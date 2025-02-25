import PIL.Image
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
)
from horde_sdk.generation_parameters.image import (
    BasicImageGenerationParameters,
    ControlnetGenerationParameters,
    CustomWorkflowGenerationParameters,
    HiresFixGenerationParameters,
    Image2ImageGenerationParameters,
    ImageGenerationParameters,
    LoRaEntry,
    RemixGenerationParameters,
    TIEntry,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.worker.consts import REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeDispatchParameters, AIHordeR2DispatchParameters
from horde_sdk.worker.dispatch.image.api_parsing.ai_horde.convert import convert_image_job_pop_response_to_parameters


def assert_image_generation_parameters(
    image_generation_parameters: ImageGenerationParameters,
    response: ImageGenerateJobPopResponse,
    source_processing: str,
) -> None:
    """Confirm all common image generation parameters are correctly mapped."""
    assert isinstance(image_generation_parameters, ImageGenerationParameters)
    assert image_generation_parameters.base_params.model == response.model
    assert image_generation_parameters.base_params.prompt == response.payload.prompt
    assert image_generation_parameters.base_params.seed == response.payload.seed
    assert image_generation_parameters.base_params.steps == response.payload.ddim_steps
    assert image_generation_parameters.batch_size == response.payload.n_iter
    assert image_generation_parameters.source_processing == source_processing
    assert image_generation_parameters.remix_params is None
    assert image_generation_parameters.hires_fix_params is None
    assert image_generation_parameters.custom_workflow_params is None
    assert image_generation_parameters.loras is None
    assert image_generation_parameters.tis is None


def assert_image_dispatch_parameters(
    dispatch_parameters: AIHordeR2DispatchParameters,
    response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm all common image dispatch parameters are correctly mapped."""
    assert isinstance(dispatch_parameters, AIHordeR2DispatchParameters)
    assert dispatch_parameters.ids == response.ids
    assert dispatch_parameters.no_valid_request_found_reasons == response.skipped == ImageGenerateJobPopSkippedStatus()
    assert dispatch_parameters.source_image_fallback_choice == REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.TXT2IMG_FALLBACK


def assert_common_image_parameters(
    image_generation_parameters: ImageGenerationParameters,
    dispatch_parameters: AIHordeR2DispatchParameters,
    response: ImageGenerateJobPopResponse,
) -> None:
    """Confirm all common image generation and dispatch parameters are correctly mapped."""
    source_processing = response.source_processing
    assert_image_generation_parameters(image_generation_parameters, response, source_processing)
    assert_image_dispatch_parameters(dispatch_parameters, response)


def test_convert_job_pop_response_to_parameters(
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
    assert generation_parameters.img2img_params is None
    assert generation_parameters.controlnet_params is None


def test_convert_job_pop_response_to_parameters_img2img(
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
    assert generation_parameters.img2img_params is not None
    assert generation_parameters.controlnet_params is None

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert generation_parameters.img2img_params.source_mask is None


def test_convert_job_pop_response_to_parameters_img2img_masked(
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

    assert generation_parameters.img2img_params is not None
    assert generation_parameters.controlnet_params is None

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert isinstance(generation_parameters.img2img_params.source_mask, PIL.Image.Image)


def test_convert_job_pop_response_to_parameters_inpainting(
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

    assert generation_parameters.img2img_params is not None
    assert generation_parameters.controlnet_params is None

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)
    assert isinstance(generation_parameters.img2img_params.source_mask, PIL.Image.Image)


def test_convert_job_pop_response_to_parameters_outpainting_alpha(
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

    assert generation_parameters.source_processing == KNOWN_SOURCE_PROCESSING.inpainting
    assert generation_parameters.img2img_params is not None
    assert generation_parameters.controlnet_params is None

    assert isinstance(generation_parameters.img2img_params, Image2ImageGenerationParameters)
    assert isinstance(generation_parameters.img2img_params.source_image, PIL.Image.Image)


def test_convert_job_pop_response_to_parameters_controlnet_openpose(
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

    assert generation_parameters.img2img_params is None

    assert generation_parameters.controlnet_params is not None
    assert isinstance(generation_parameters.controlnet_params, ControlnetGenerationParameters)
    assert generation_parameters.controlnet_params.control_map is not None
    assert isinstance(generation_parameters.controlnet_params.control_map, PIL.Image.Image)
    assert generation_parameters.controlnet_params.source_image is None
