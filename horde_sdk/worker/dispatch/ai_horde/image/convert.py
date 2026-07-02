"""Contains functions to convert API responses to image generation parameters."""

from urllib.parse import urlparse

from horde_model_reference.meta_consts import (
    KNOWN_IMAGE_GENERATION_BASELINE,
    MODEL_REFERENCE_CATEGORY,
    get_baseline_native_resolution,
)
from horde_model_reference.model_reference_manager import ModelReferenceManager
from loguru import logger
from pydantic import BaseModel, ConfigDict

from horde_sdk.ai_horde_api.apimodels.base import GenMetadataEntry
from horde_sdk.ai_horde_api.apimodels.generate.pop import ImageGenerateJobPopResponse
from horde_sdk.ai_horde_api.consts import DEFAULT_HIRES_DENOISE_STRENGTH, METADATA_TYPE, METADATA_VALUE
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import KNOWN_DISPATCH_SOURCE, KNOWN_INFERENCE_BACKEND
from horde_sdk.generation_parameters.alchemy import (
    AlchemyParameters,
    FacefixAlchemyParameters,
    SingleAlchemyParameters,
    UpscaleAlchemyParameters,
)
from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    is_facefixer_form,
    is_upscaler_form,
)
from horde_sdk.generation_parameters.generic.consts import KNOWN_AUX_MODEL_SOURCE
from horde_sdk.generation_parameters.image import (
    DEFAULT_BASELINE_RESOLUTION,
    HIRES_FIX_DENOISE_STRENGTH_DEFAULT,
    BasicImageGenerationParameters,
    ControlnetGenerationParameters,
    CustomWorkflowGenerationParameters,
    ExtraTextEntry,
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
from horde_sdk.generation_parameters.image.object_models import ImageGenerationComponentContainer
from horde_sdk.utils.image_utils import (
    base64_str_to_bytes,
    calc_upscale_sampler_steps,
    get_first_pass_image_resolution_by_baseline,
)
from horde_sdk.worker.consts import (
    REQUESTED_BACKEND_CONSTRAINTS,
    REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE,
)
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeR2DispatchParameters

AI_HORDE_PROMPT_SEPARATOR = "###"
"""The AI-Horde specific separator between the positive and negative prompt in a combined prompt string."""


class ImageConversionResult(BaseModel):
    """Represents the outcome of converting an image job pop response to generation parameters.

    Conversion is fault-tolerant: unusable inputs (such as an undecodable source image) degrade
    the request rather than abort it, and each degradation is recorded in `faults`.
    """

    model_config = ConfigDict(frozen=True)

    generation_parameters: ImageGenerationParameters
    """The backend-agnostic generation parameters."""

    dispatch_parameters: AIHordeR2DispatchParameters
    """The AI-Horde specific dispatch parameters (result routing, TTL, upload URLs)."""

    faults: list[GenMetadataEntry] = []
    """Metadata entries describing any degradations applied during conversion."""


def _split_ai_horde_prompt(combined_prompt: str) -> tuple[str, str | None]:
    """Split an AI-Horde combined prompt into its positive and negative halves."""
    if AI_HORDE_PROMPT_SEPARATOR in combined_prompt:
        positive_prompt, negative_prompt = combined_prompt.split(AI_HORDE_PROMPT_SEPARATOR, 1)
        return positive_prompt, negative_prompt

    return combined_prompt, None


def _is_url(value: str) -> bool:
    """Check whether the value is an HTTP(S) URL rather than inline base64 data."""
    return urlparse(value).scheme in ("http", "https")


def _resolve_source_image_field(
    field_value: str | None,
    downloaded_value: str | None,
    field_description: str,
) -> str | None:
    """Resolve a source-image field to its base64 form, preferring the downloaded copy for URLs.

    Returns None when the field is a URL whose download never happened; callers are expected to
    run the response's `async_download_*` methods before conversion.
    """
    if field_value is None:
        return None

    if _is_url(field_value):
        if downloaded_value is None:
            logger.error(
                f"The {field_description} is a URL but was not downloaded. "
                "Run the response's `async_download_*` methods before converting.",
            )
        return downloaded_value

    return field_value


def _decode_source_image_field(
    base64_value: str | None,
    metadata_type: METADATA_TYPE,
    faults: list[GenMetadataEntry],
) -> bytes | None:
    """Decode a base64 source-image field to bytes, recording a fault when decoding fails."""
    if base64_value is None:
        return None

    try:
        return base64_str_to_bytes(base64_value)
    except Exception as err:
        faults.append(GenMetadataEntry(type=metadata_type, value=METADATA_VALUE.parse_failed))
        logger.warning(f"Failed to decode {metadata_type} data: {err}")
        return None


def _get_img2img_params(
    api_response: ImageGenerateJobPopResponse,
    faults: list[GenMetadataEntry],
) -> Image2ImageGenerationParameters | None:
    """Get the image-to-image parameters from the API response, if applicable."""
    if api_response.source_processing not in [
        KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
        KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
        KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
    ]:
        return None

    resolved_source_image = _resolve_source_image_field(
        api_response.source_image,
        api_response.get_downloaded_source_image(),
        "source image",
    )
    source_image = _decode_source_image_field(resolved_source_image, METADATA_TYPE.source_image, faults)

    resolved_source_mask = _resolve_source_image_field(
        api_response.source_mask,
        api_response.get_downloaded_source_mask(),
        "source mask",
    )
    source_mask = _decode_source_image_field(resolved_source_mask, METADATA_TYPE.source_mask, faults)

    if source_image is None:
        logger.warning("No usable source image found for img2img generation. Avoiding img2img if possible.")
        return None

    return Image2ImageGenerationParameters(
        source_image=source_image,
        source_mask=source_mask,
    )


def _get_remix_images(
    api_response: ImageGenerateJobPopResponse,
    faults: list[GenMetadataEntry],
) -> list[RemixImageEntry]:
    """Get the decodable extra source images from the API response as remix entries."""
    extra_source_images = api_response.extra_source_images
    if extra_source_images is not None:
        downloaded_extra_source_images = api_response.get_downloaded_extra_source_images()
        if downloaded_extra_source_images is not None:
            extra_source_images = downloaded_extra_source_images

    remix_images: list[RemixImageEntry] = []
    if extra_source_images is None:
        return remix_images

    for extra_source_image_index, extra_source_image in enumerate(extra_source_images):
        if _is_url(extra_source_image.image):
            logger.warning(
                "Extra source image is a URL but was not downloaded; skipping it. "
                "Run the response's `async_download_*` methods before converting.",
            )
            continue

        try:
            remix_image_bytes = base64_str_to_bytes(extra_source_image.image)
        except Exception as err:
            faults.append(
                GenMetadataEntry(
                    type=METADATA_TYPE.extra_source_images,
                    value=METADATA_VALUE.parse_failed,
                    ref=str(extra_source_image_index),
                ),
            )
            logger.warning(f"Failed to decode extra source image {extra_source_image_index}: {err}")
            continue

        remix_images.append(
            RemixImageEntry(
                image=remix_image_bytes,
                strength=extra_source_image.strength,
            ),
        )

    return remix_images


def _get_remix_params(
    api_response: ImageGenerateJobPopResponse,
    faults: list[GenMetadataEntry],
) -> RemixGenerationParameters | None:
    """Get the remix parameters from the API response, if applicable."""
    if api_response.source_processing != KNOWN_IMAGE_SOURCE_PROCESSING.remix:
        return None

    resolved_source_image = _resolve_source_image_field(
        api_response.source_image,
        api_response.get_downloaded_source_image(),
        "source image",
    )
    source_image = _decode_source_image_field(resolved_source_image, METADATA_TYPE.source_image, faults)

    if source_image is None:
        logger.warning("No usable source image found for remix generation. Avoiding remix if possible.")
        return None

    return RemixGenerationParameters(
        source_image=source_image,
        remix_images=_get_remix_images(api_response, faults),
    )


def _get_controlnet_params(
    api_response: ImageGenerateJobPopResponse,
    faults: list[GenMetadataEntry],
) -> ControlnetGenerationParameters | None:
    """Get the controlnet parameters from the API response, if applicable."""
    if api_response.payload.control_type is None:
        return None

    resolved_source_image = _resolve_source_image_field(
        api_response.source_image,
        api_response.get_downloaded_source_image(),
        "source image",
    )
    source_image = _decode_source_image_field(resolved_source_image, METADATA_TYPE.source_image, faults)

    return_control_map = bool(api_response.payload.return_control_map)

    if api_response.payload.image_is_control:
        return ControlnetGenerationParameters(
            source_image=None,
            controlnet_type=api_response.payload.control_type,
            control_map=source_image,
            return_control_map=return_control_map,
        )

    return ControlnetGenerationParameters(
        source_image=source_image,
        controlnet_type=api_response.payload.control_type,
        control_map=None,
        return_control_map=return_control_map,
    )


def _hires_fix_applies(
    api_response: ImageGenerateJobPopResponse,
    model_baseline: KNOWN_IMAGE_GENERATION_BASELINE | None,
) -> bool:
    """Check whether the requested hires fix is meaningful for this generation.

    Hires fix is a two-pass upscale; it is disabled when the target resolution does not exceed
    the baseline's native resolution, and for inpainting/outpainting where the dimensions come
    from the source image.
    """
    if not api_response.payload.hires_fix:
        return False

    if api_response.source_processing in [
        KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
        KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
    ]:
        return False

    width = api_response.payload.width
    height = api_response.payload.height

    fits_single_pass_sd1 = model_baseline == KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1 and (
        width <= 512 or height <= 512
    )
    fits_single_pass_sdxl = model_baseline == KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl and (
        width <= 1024 or height <= 1024
    )

    return not (fits_single_pass_sd1 or fits_single_pass_sdxl)


def _get_hires_fix_second_pass_denoising_strength(api_response: ImageGenerateJobPopResponse) -> float:
    """Get the denoising strength for the hires-fix second pass.

    When no explicit second-pass strength is requested, non-txt2img generations inherit the
    first-pass denoising strength (the source image informs both passes); txt2img generations
    use the default.
    """
    if api_response.payload.hires_fix_denoising_strength is not None:
        return api_response.payload.hires_fix_denoising_strength

    is_txt2img = (
        api_response.source_processing is None
        or api_response.source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    )
    if not is_txt2img and api_response.payload.denoising_strength is not None:
        return api_response.payload.denoising_strength

    return DEFAULT_HIRES_DENOISE_STRENGTH


def _get_hires_fix_params(
    api_response: ImageGenerateJobPopResponse,
    model_baseline: KNOWN_IMAGE_GENERATION_BASELINE | None,
    prompt: str,
    negative_prompt: str | None,
) -> HiresFixGenerationParameters | None:
    """Get the high-resolution fix parameters from the API response, if applicable."""
    if not _hires_fix_applies(api_response, model_baseline):
        return None

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

    model = api_response.model

    if not model or model.isspace():
        raise ValueError("Model is required for hires fix generation.")

    scheduler = KNOWN_IMAGE_SCHEDULERS.karras if api_response.payload.karras else KNOWN_IMAGE_SCHEDULERS.normal

    return HiresFixGenerationParameters(
        first_pass=BasicImageGenerationParameters(
            model=model,
            model_baseline=model_baseline,
            # model_filename=None,  # TODO
            # model_hash=None,  # TODO
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=api_response.payload.seed,
            width=first_pass_width,
            height=first_pass_height,
            steps=api_response.payload.ddim_steps,
            cfg_scale=api_response.payload.cfg_scale,
            sampler_name=api_response.payload.sampler_name,
            scheduler=scheduler,
            clip_skip=api_response.payload.clip_skip,
            denoising_strength=api_response.payload.denoising_strength,
            transparent=api_response.payload.transparent,
        ),
        second_pass=BasicImageGenerationParameters(
            model=model,
            model_baseline=model_baseline,
            # model_filename=None,  # TODO
            # model_hash=None,  # TODO
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=api_response.payload.seed,
            width=second_pass_width,
            height=second_pass_height,
            steps=second_pass_steps,
            cfg_scale=api_response.payload.cfg_scale,
            sampler_name=api_response.payload.sampler_name,
            scheduler=scheduler,
            clip_skip=api_response.payload.clip_skip,
            denoising_strength=_get_hires_fix_second_pass_denoising_strength(api_response),
            transparent=api_response.payload.transparent,
        ),
    )


def _get_custom_workflow_params(
    api_response: ImageGenerateJobPopResponse,
) -> CustomWorkflowGenerationParameters | None:
    """Get the custom workflow parameters from the API response, if applicable."""
    if api_response.payload.workflow is None:
        if api_response.payload.extra_texts:
            logger.debug("Extra texts were provided without a workflow; they will not be used.")
        return None

    extra_texts: list[ExtraTextEntry] | None = None
    if api_response.payload.extra_texts is not None:
        extra_texts = [
            ExtraTextEntry(text=extra_text.text, reference=extra_text.reference)
            for extra_text in api_response.payload.extra_texts
        ]

    return CustomWorkflowGenerationParameters(
        custom_workflow_name=api_response.payload.workflow,
        custom_parameters=None,
        custom_workflow_version=None,
        extra_texts=extra_texts,
    )


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


def _get_alchemy_params(api_response: ImageGenerateJobPopResponse) -> AlchemyParameters | None:
    """Get the post-processing operations attached to the image job as alchemy parameters.

    The operations' `source_image` is None because their input is the generated image, which
    only exists at execution time. The `result_id` is the owning job's ID; embedded
    post-processing has no per-operation result IDs. The requested API order is preserved in
    `all_alchemy_operations`; any execution-policy reordering (such as running facefixers last)
    is the executor's responsibility.
    """
    post_processing = api_response.payload.post_processing
    if not post_processing:
        return None

    owning_job_id = str(api_response.id_) if api_response.id_ is not None else str(api_response.ids[0])

    upscalers: list[UpscaleAlchemyParameters] = []
    facefixers: list[FacefixAlchemyParameters] = []
    misc_post_processors: list[SingleAlchemyParameters] = []
    ordered_operations: list[SingleAlchemyParameters] = []

    for post_processor_name in post_processing:
        operation: SingleAlchemyParameters
        if is_upscaler_form(post_processor_name):
            operation = UpscaleAlchemyParameters(
                result_id=owning_job_id,
                form=KNOWN_ALCHEMY_FORMS.post_process,
                source_image=None,
                upscaler=post_processor_name,
            )
            upscalers.append(operation)
        elif is_facefixer_form(post_processor_name):
            operation = FacefixAlchemyParameters(
                result_id=owning_job_id,
                form=KNOWN_ALCHEMY_FORMS.post_process,
                source_image=None,
                facefixer=post_processor_name,
                codeformer_fidelity=api_response.payload.facefixer_strength,
            )
            facefixers.append(operation)
        else:
            operation = SingleAlchemyParameters(
                result_id=owning_job_id,
                form=str(post_processor_name),
                source_image=None,
            )
            misc_post_processors.append(operation)

        ordered_operations.append(operation)

    alchemy_parameters = AlchemyParameters(
        upscalers=upscalers or None,
        facefixers=facefixers or None,
        misc_post_processors=misc_post_processors or None,
    )
    # Pre-populate the operations cache so `all_alchemy_operations` reflects the requested API
    # order instead of the grouped field order.
    alchemy_parameters._all_alchemy_operations = ordered_operations

    return alchemy_parameters


def convert_image_job_pop_response_to_parameters(
    api_response: ImageGenerateJobPopResponse,
    model_reference_manager: ModelReferenceManager,
) -> ImageConversionResult:
    """Convert an API response to the parameters for a generation.

    Conversion is fault-tolerant for source images: when an img2img-family or remix request has
    no usable source image, the generation degrades to txt2img and a fault is recorded, matching
    the `TXT2IMG_FALLBACK` choice declared in the dispatch parameters.
    """
    if api_response.model is None:
        raise ValueError("Model is required for generation.")

    faults: list[GenMetadataEntry] = []

    model_record = (
        model_reference_manager.query(MODEL_REFERENCE_CATEGORY.image_generation).where(name=api_response.model).first()
    )
    model_baseline: KNOWN_IMAGE_GENERATION_BASELINE | None = None

    if model_record is not None:
        try:
            model_baseline = KNOWN_IMAGE_GENERATION_BASELINE(model_record.baseline)
        except ValueError:
            logger.debug(
                f"Invalid baseline {model_record.baseline} for model {api_response.model}. Using None instead.",
            )
            model_baseline = None

        # model_version = model_record.version # TODO

    combined_prompt = api_response.payload.prompt
    if not combined_prompt or combined_prompt.isspace():
        raise ValueError("Prompt is required for generation.")

    prompt, negative_prompt = _split_ai_horde_prompt(combined_prompt)

    base_params = BasicImageGenerationParameters(
        model=api_response.model,
        model_baseline=model_baseline,
        # model_version=model_version,
        # model_filename=None,  # TODO
        # model_hash=None,  # TODO
        prompt=prompt,
        negative_prompt=negative_prompt,
        seed=api_response.payload.seed,
        height=api_response.payload.height,
        width=api_response.payload.width,
        steps=api_response.payload.ddim_steps,
        cfg_scale=api_response.payload.cfg_scale,
        sampler_name=api_response.payload.sampler_name,
        scheduler=KNOWN_IMAGE_SCHEDULERS.karras if api_response.payload.karras else KNOWN_IMAGE_SCHEDULERS.normal,
        clip_skip=api_response.payload.clip_skip,
        denoising_strength=api_response.payload.denoising_strength,
        tiling=api_response.payload.tiling,
        transparent=api_response.payload.transparent,
    )

    img2img_params: Image2ImageGenerationParameters | None = _get_img2img_params(api_response, faults)
    remix_params: RemixGenerationParameters | None = _get_remix_params(api_response, faults)
    controlnet_params: ControlnetGenerationParameters | None = _get_controlnet_params(api_response, faults)
    hires_fix_params: HiresFixGenerationParameters | None = _get_hires_fix_params(
        api_response,
        model_baseline,
        prompt,
        negative_prompt,
    )
    custom_workflow_params: CustomWorkflowGenerationParameters | None = _get_custom_workflow_params(api_response)
    alchemy_params: AlchemyParameters | None = _get_alchemy_params(api_response)

    loras: list[LoRaEntry] | None = _get_lora_params(api_response)
    tis: list[TIEntry] | None = _get_ti_params(api_response)

    source_processing = api_response.source_processing

    img2img_family_without_source = (
        source_processing
        in [
            KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
            KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
            KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
        ]
        and img2img_params is None
    )
    remix_without_source = source_processing == KNOWN_IMAGE_SOURCE_PROCESSING.remix and remix_params is None

    if img2img_family_without_source or remix_without_source:
        # The source image is unusable; degrade to txt2img rather than abort, matching the
        # TXT2IMG_FALLBACK choice declared below.
        logger.warning(
            f"Source processing {source_processing} requested without a usable source image; falling back to txt2img.",
        )
        if not any(fault.type_ == METADATA_TYPE.source_image for fault in faults):
            faults.append(
                GenMetadataEntry(type=METADATA_TYPE.source_image, value=METADATA_VALUE.parse_failed),
            )
        source_processing = KNOWN_IMAGE_SOURCE_PROCESSING.txt2img

    raw_uuids = [id_.root for id_ in api_response.ids]

    additional_params: list[
        Image2ImageGenerationParameters
        | RemixGenerationParameters
        | ControlnetGenerationParameters
        | HiresFixGenerationParameters
        | LoRaEntry
        | TIEntry
        | CustomWorkflowGenerationParameters
    ] = []

    if img2img_params is not None:
        additional_params.append(img2img_params)
    if remix_params is not None:
        additional_params.append(remix_params)
    if controlnet_params is not None:
        additional_params.append(controlnet_params)
    if hires_fix_params is not None:
        additional_params.append(hires_fix_params)
    if loras is not None:
        additional_params.extend(loras)
    if tis is not None:
        additional_params.extend(tis)
    if custom_workflow_params is not None:
        additional_params.append(custom_workflow_params)

    image_generation_parameters = ImageGenerationParameters(
        result_ids=raw_uuids,
        batch_size=api_response.payload.n_iter,
        source_processing=source_processing,
        base_params=base_params,
        additional_params=ImageGenerationComponentContainer(
            components=additional_params,
        ),
        alchemy_params=alchemy_params,
    )

    r2_upload_url_map = {}

    if api_response.r2_upload is not None:
        r2_upload_url_map[api_response.id_] = api_response.r2_upload
    elif api_response.r2_uploads is not None:
        r2_upload_url_map = dict(zip(api_response.ids, api_response.r2_uploads, strict=True))
    else:
        raise ValueError("No R2 upload URL found in the API response.")

    ai_horde_dispatch_parameters = AIHordeR2DispatchParameters(
        generation_ids=[GenerationID(root=uuid_) for uuid_ in raw_uuids],
        dispatch_source=KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL,
        ttl=api_response.ttl,
        inference_backend=KNOWN_INFERENCE_BACKEND.COMFYUI,
        requested_backend_constraints=REQUESTED_BACKEND_CONSTRAINTS.SPECIFIED,
        no_valid_request_found_reasons=api_response.skipped,
        source_image_fallback_choice=REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.TXT2IMG_FALLBACK,
        r2_upload_url_map=r2_upload_url_map,
    )

    return ImageConversionResult(
        generation_parameters=image_generation_parameters,
        dispatch_parameters=ai_horde_dispatch_parameters,
        faults=faults,
    )
