"""Contains functions to convert API responses to image generation parameters."""

from horde_model_reference.meta_consts import (
    KNOWN_IMAGE_GENERATION_BASELINE,
    get_baseline_native_resolution,
)
from horde_model_reference.model_reference_manager import ModelReferenceManager
from loguru import logger

from horde_sdk.ai_horde_api.apimodels.generate.pop import ImageGenerateJobPopResponse
from horde_sdk.ai_horde_api.consts import DEFAULT_HIRES_DENOISE_STRENGTH
from horde_sdk.generation_parameters.generic import GenerationParameterComponentBase
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image import (
    DEFAULT_BASELINE_RESOLUTION,
    HIRES_FIX_DENOISE_STRENGTH_DEFAULT,
    BasicImageGenerationParameters,
    ControlnetGenerationParameters,
    CustomWorkflowGenerationParameters,
    HiresFixGenerationParameters,
    Image2ImageGenerationParameters,
    ImageGenerationParameters,
    LoRaEntry,
    RemixGenerationParameters,
    RemixImageEntry,
    TIEntry,
)
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_SCHEDULERS,
    KNOWN_IMAGE_SOURCE_PROCESSING,
    LORA_TRIGGER_INJECT_CHOICE,
    TI_TRIGGER_INJECT_CHOICE,
)
from horde_sdk.utils.image_utils import (
    base64_str_to_bytes,
    calc_upscale_sampler_steps,
    get_first_pass_image_resolution_by_baseline,
)
from horde_sdk.worker.consts import (
    KNOWN_DISPATCH_SOURCE,
    KNOWN_INFERENCE_BACKEND,
    REQUESTED_BACKEND_CONSTRAINTS,
    REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE,
)
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeR2DispatchParameters


def _get_img2img_params(api_response: ImageGenerateJobPopResponse) -> Image2ImageGenerationParameters | None:
    """Get the image-to-image parameters from the API response, if applicable."""
    if api_response.source_processing in [
        KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
        KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
        KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
    ]:
        source_image: bytes | None = None
        if isinstance(api_response.source_image, str):
            source_image = base64_str_to_bytes(api_response.source_image)

        source_mask: bytes | None = None
        if isinstance(api_response.source_mask, str):
            source_mask = base64_str_to_bytes(api_response.source_mask)

        if source_image is None:
            logger.warning("No source image found for img2img generation. Avoiding img2img if possible.")
            return None

        return Image2ImageGenerationParameters(
            source_image=source_image,
            source_mask=source_mask,
        )

    return None


def _get_remix_params(api_response: ImageGenerateJobPopResponse) -> RemixGenerationParameters | None:
    """Get the remix parameters from the API response, if applicable."""
    if api_response.source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.remix:
        source_image: bytes | None = None
        if isinstance(api_response.source_image, str):
            source_image = base64_str_to_bytes(api_response.source_image)

        remix_images: list[RemixImageEntry] = []
        if api_response.extra_source_images is not None:
            for remix_image in api_response.extra_source_images:
                remix_images.append(
                    RemixImageEntry(
                        image=base64_str_to_bytes(remix_image.image),
                        strength=remix_image.strength,
                    ),
                )

        return RemixGenerationParameters(
            source_image=source_image,
            remix_images=remix_images,
        )

    return None


def _get_controlnet_params(api_response: ImageGenerateJobPopResponse) -> ControlnetGenerationParameters | None:
    """Get the controlnet parameters from the API response, if applicable."""
    if api_response.payload.control_type is not None:
        source_image: bytes | None = None

        if isinstance(api_response.source_image, str):
            source_image = base64_str_to_bytes(api_response.source_image)

        if api_response.payload.image_is_control:
            controlnet_params = ControlnetGenerationParameters(
                source_image=None,
                controlnet_type=api_response.payload.control_type,
                control_map=source_image,
            )
        else:
            controlnet_params = ControlnetGenerationParameters(
                source_image=source_image,
                controlnet_type=api_response.payload.control_type,
                control_map=None,
            )

        return controlnet_params

    return None


def _get_hires_fix_params(
    api_response: ImageGenerateJobPopResponse,
    model_baseline: KNOWN_IMAGE_GENERATION_BASELINE | None = None,
) -> HiresFixGenerationParameters | None:
    """Get the high-resolution fix parameters from the API response, if applicable."""
    first_pass_width, first_pass_height = get_first_pass_image_resolution_by_baseline(
        width=api_response.payload.width,
        height=api_response.payload.height,
        baseline=model_baseline,
    )

    second_pass_width = api_response.payload.width
    second_pass_height = api_response.payload.height

    second_pass_steps = calc_upscale_sampler_steps(
        model_native_resolution=(
            get_baseline_native_resolution(model_baseline) if model_baseline else DEFAULT_BASELINE_RESOLUTION
        ),
        width=api_response.payload.width,
        height=api_response.payload.height,
        hires_fix_denoising_strength=(
            api_response.payload.hires_fix_denoising_strength or HIRES_FIX_DENOISE_STRENGTH_DEFAULT
        ),
        ddim_steps=api_response.payload.ddim_steps,
    )

    if api_response.payload.hires_fix:
        return HiresFixGenerationParameters(
            first_pass=BasicImageGenerationParameters(
                model=api_response.model,
                model_baseline=model_baseline,
                model_filename=None,  # TODO
                model_hash=None,  # TODO
                prompt=api_response.payload.prompt,
                seed=api_response.payload.seed,
                width=first_pass_width,
                height=first_pass_height,
                steps=api_response.payload.ddim_steps,
                cfg_scale=api_response.payload.cfg_scale,
                sampler_name=api_response.payload.sampler_name,
                scheduler=(
                    KNOWN_IMAGE_SCHEDULERS.karras if api_response.payload.karras else KNOWN_IMAGE_SCHEDULERS.normal
                ),
                clip_skip=api_response.payload.clip_skip,
                denoising_strength=api_response.payload.denoising_strength,
            ),
            second_pass=BasicImageGenerationParameters(
                model=api_response.model,
                model_baseline=model_baseline,
                model_filename=None,  # TODO
                model_hash=None,  # TODO
                prompt=api_response.payload.prompt,
                seed=api_response.payload.seed,
                width=second_pass_width,
                height=second_pass_height,
                steps=second_pass_steps,
                cfg_scale=api_response.payload.cfg_scale,
                sampler_name=api_response.payload.sampler_name,
                scheduler=(
                    KNOWN_IMAGE_SCHEDULERS.karras if api_response.payload.karras else KNOWN_IMAGE_SCHEDULERS.normal
                ),
                clip_skip=api_response.payload.clip_skip,
                denoising_strength=api_response.payload.hires_fix_denoising_strength or DEFAULT_HIRES_DENOISE_STRENGTH,
            ),
        )

    return None


def _get_custom_workflow_params(
    api_response: ImageGenerateJobPopResponse,
) -> CustomWorkflowGenerationParameters | None:
    """Get the custom workflow parameters from the API response, if applicable."""
    if api_response.payload.workflow is not None:
        return CustomWorkflowGenerationParameters(
            custom_workflow_name=api_response.payload.workflow,
            custom_parameters=None,
            custom_workflow_version=None,
        )

    return None


def _get_lora_params(api_response: ImageGenerateJobPopResponse) -> list[LoRaEntry] | None:
    """Get the LoRa parameters from the API response, if applicable."""
    if api_response.payload.loras is not None:
        loras = []
        for lora in api_response.payload.loras:
            trigger_inject_choice = LORA_TRIGGER_INJECT_CHOICE.NO_INJECT

            if lora.inject_trigger is not None:
                trigger_inject_choice = LORA_TRIGGER_INJECT_CHOICE.FUZZY_POSITIVE

            if lora.is_version:
                loras.append(
                    LoRaEntry(
                        name=None,
                        release_version=None,
                        remote_version_id=lora.name,
                        source=KNOWN_AUX_MODEL_SOURCE.CIVITAI,
                        model_strength=lora.model,
                        clip_strength=lora.clip,
                        lora_inject_trigger_choice=trigger_inject_choice,
                        lora_triggers=[lora.inject_trigger] if lora.inject_trigger is not None else None,
                    ),
                )
            else:
                loras.append(
                    LoRaEntry(
                        name=lora.name,
                        release_version=None,
                        remote_version_id=None,
                        source=KNOWN_AUX_MODEL_SOURCE.CIVITAI,
                        model_strength=lora.model,
                        clip_strength=lora.clip,
                        lora_inject_trigger_choice=trigger_inject_choice,
                        lora_triggers=[lora.inject_trigger] if lora.inject_trigger is not None else None,
                    ),
                )

        return loras

    return None


def _get_ti_params(api_response: ImageGenerateJobPopResponse) -> list[TIEntry] | None:
    """Get the TI parameters from the API response, if applicable."""
    if api_response.payload.tis is not None:
        tis = []
        for ti in api_response.payload.tis:
            ti_trigger_inject_choice = TI_TRIGGER_INJECT_CHOICE.NO_INJECT

            if ti.inject_ti == "prompt":
                ti_trigger_inject_choice = TI_TRIGGER_INJECT_CHOICE.POSITIVE_PROMPT
            elif ti.inject_ti == "negprompt":
                ti_trigger_inject_choice = TI_TRIGGER_INJECT_CHOICE.NEGATIVE_PROMPT

            tis.append(
                TIEntry(
                    name=ti.name,
                    remote_version_id=None,
                    source=KNOWN_AUX_MODEL_SOURCE.HORDELING,
                    ti_inject_trigger_choice=ti_trigger_inject_choice,
                    model_strength=ti.strength,
                ),
            )

        return tis

    return None


def convert_image_job_pop_response_to_parameters(
    api_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> tuple[ImageGenerationParameters, AIHordeR2DispatchParameters]:
    """Convert an API response to the parameters for a generation."""
    if api_response.model is None:
        raise ValueError("Model is required for generation.")

    model_record = model_reference_manager.stable_diffusion.root.get(api_response.model)
    model_baseline: KNOWN_IMAGE_GENERATION_BASELINE | None = None

    if model_record is not None:
        try:
            model_baseline = KNOWN_IMAGE_GENERATION_BASELINE(model_record.baseline)
        except ValueError:
            logger.debug(
                f"Invalid baseline {model_record.baseline} for model {api_response.model}. Using None instead.",
            )
            model_baseline = None

        model_version = model_record.version

    base_params = BasicImageGenerationParameters(
        model=api_response.model,
        model_baseline=model_baseline,
        model_version=model_version,
        model_filename=None,  # TODO
        model_hash=None,  # TODO
        prompt=api_response.payload.prompt,
        seed=api_response.payload.seed,
        height=api_response.payload.height,
        width=api_response.payload.width,
        steps=api_response.payload.ddim_steps,
        cfg_scale=api_response.payload.cfg_scale,
        sampler_name=api_response.payload.sampler_name,
        scheduler=KNOWN_IMAGE_SCHEDULERS.karras if api_response.payload.karras else KNOWN_IMAGE_SCHEDULERS.normal,
        clip_skip=api_response.payload.clip_skip,
        denoising_strength=api_response.payload.denoising_strength,
    )

    img2img_params: Image2ImageGenerationParameters | None = _get_img2img_params(api_response)
    remix_params: RemixGenerationParameters | None = _get_remix_params(api_response)
    controlnet_params: ControlnetGenerationParameters | None = _get_controlnet_params(api_response)
    hires_fix_params: HiresFixGenerationParameters | None = _get_hires_fix_params(api_response, model_baseline)
    custom_workflow_params: CustomWorkflowGenerationParameters | None = _get_custom_workflow_params(api_response)

    loras: list[LoRaEntry] | None = _get_lora_params(api_response)
    tis: list[TIEntry] | None = _get_ti_params(api_response)

    raw_uuids = [id_.root for id_ in api_response.ids]

    additional_params: list[GenerationParameterComponentBase] = []

    if img2img_params is not None:
        additional_params.append(img2img_params)
    if remix_params is not None:
        additional_params.append(remix_params)
    if controlnet_params is not None:
        additional_params.append(controlnet_params)
    if hires_fix_params is not None:
        additional_params.append(hires_fix_params)
    if custom_workflow_params is not None:
        additional_params.append(custom_workflow_params)

    image_generation_parameters = ImageGenerationParameters(
        generation_ids=raw_uuids,
        batch_size=api_response.payload.n_iter,
        tiling=api_response.payload.tiling,
        source_processing=api_response.source_processing,
        base_params=base_params,
        additional_params=additional_params,
        loras=loras,
        tis=tis,
    )

    r2_upload_url_map = {}

    if api_response.r2_upload is not None:
        r2_upload_url_map[api_response.id_] = api_response.r2_upload
    elif api_response.r2_uploads is not None:
        r2_upload_url_map = dict(zip(api_response.ids, api_response.r2_uploads, strict=True))
    else:
        raise ValueError("No R2 upload URL found in the API response.")

    ai_horde_dispatch_parameters = AIHordeR2DispatchParameters(
        generation_ids=raw_uuids,
        dispatch_source=KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL,
        ttl=api_response.ttl,
        inference_backend=KNOWN_INFERENCE_BACKEND.COMFYUI,
        inference_backend_constraints=REQUESTED_BACKEND_CONSTRAINTS.SPECIFIED,
        no_valid_request_found_reasons=api_response.skipped,
        source_image_fallback_choice=REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.TXT2IMG_FALLBACK,
        r2_upload_url_map=r2_upload_url_map,
    )

    return image_generation_parameters, ai_horde_dispatch_parameters
