"""Contains functions to convert API responses to alchemy generation parameters."""

from horde_sdk.ai_horde_api.apimodels import AlchemyJobPopResponse, NoValidAlchemyFound
from horde_sdk.generation_parameters.alchemy import (
    AlchemyParameters,
    CaptionAlchemyParameters,
    FacefixAlchemyParameters,
    InterrogateAlchemyParameters,
    NSFWAlchemyParameters,
    SingleAlchemyParameters,
    UpscaleAlchemyParameters,
)
from horde_sdk.generation_parameters.alchemy.consts import (
    KNOWN_ALCHEMY_FORMS,
    KNOWN_CAPTION_MODELS,
    KNOWN_INTERROGATORS,
    KNOWN_NSFW_DETECTOR,
    is_caption_form,
    is_facefixer_form,
    is_interrogator_form,
    is_nsfw_detector_form,
    is_upscaler_form,
)
from horde_sdk.utils.image_utils import (
    base64_str_to_bytes,
)
from horde_sdk.worker.consts import (
    KNOWN_ALCHEMY_BACKEND,
    KNOWN_DISPATCH_SOURCE,
    REQUESTED_BACKEND_CONSTRAINTS,
    REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE,
)
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeR2DispatchParameters


def convert_alchemy_job_pop_response_to_parameters(
    api_response: AlchemyJobPopResponse,
) -> tuple[AlchemyParameters, AIHordeR2DispatchParameters]:
    """Convert an API response to the parameters for a generation."""
    if api_response.forms is None or len(api_response.forms) == 0:
        raise ValueError("The API response did not contain any forms. Was this a skipped response?")

    parsed_upscalers: list[UpscaleAlchemyParameters] = []
    parsed_facefixers: list[FacefixAlchemyParameters] = []
    parsed_interrogators: list[InterrogateAlchemyParameters] = []
    parsed_captions: list[CaptionAlchemyParameters] = []
    parsed_nsfw_detectors: list[NSFWAlchemyParameters] = []

    parsed_unknown_forms: list[SingleAlchemyParameters] = []

    r2_upload_url_map = {}

    for form in api_response.forms:
        if form.source_image is None:
            raise ValueError("The API response did not contain a source image for a form.")

        r2_upload_url_map[str(form.id_)] = form.r2_upload

        if is_upscaler_form(form.form):
            parsed_upscalers.append(
                UpscaleAlchemyParameters(
                    generation_id=str(form.id_),
                    form=KNOWN_ALCHEMY_FORMS.post_process,
                    source_image=base64_str_to_bytes(form.source_image),
                    upscaler=form.form,
                ),
            )

        elif is_facefixer_form(form.form):
            parsed_facefixers.append(
                FacefixAlchemyParameters(
                    generation_id=str(form.id_),
                    form=KNOWN_ALCHEMY_FORMS.post_process,
                    source_image=base64_str_to_bytes(form.source_image),
                    facefixer=form.form,
                ),
            )

        elif is_interrogator_form(form.form):
            parsed_interrogators.append(
                InterrogateAlchemyParameters(
                    generation_id=str(form.id_),
                    form=KNOWN_ALCHEMY_FORMS.interrogation,
                    source_image=base64_str_to_bytes(form.source_image),
                    interrogator=KNOWN_INTERROGATORS.vit_l_14,
                ),
            )

        elif is_caption_form(form.form):
            parsed_captions.append(
                CaptionAlchemyParameters(
                    generation_id=str(form.id_),
                    form=KNOWN_ALCHEMY_FORMS.caption,
                    source_image=base64_str_to_bytes(form.source_image),
                    caption_model=KNOWN_CAPTION_MODELS.BLIP_BASE_SALESFORCE,
                ),
            )

        elif is_nsfw_detector_form(form.form):
            parsed_nsfw_detectors.append(
                NSFWAlchemyParameters(
                    generation_id=str(form.id_),
                    form=KNOWN_ALCHEMY_FORMS.nsfw,
                    source_image=base64_str_to_bytes(form.source_image),
                    nsfw_detector=KNOWN_NSFW_DETECTOR.horde_safety,
                ),
            )

        else:
            parsed_unknown_forms.append(
                SingleAlchemyParameters(
                    generation_id=str(form.id_),
                    form=form.form,
                    source_image=base64_str_to_bytes(form.source_image),
                ),
            )

    alchemy_parameters = AlchemyParameters(
        upscalers=parsed_upscalers or None,
        facefixers=parsed_facefixers or None,
        interrogators=parsed_interrogators or None,
        captions=parsed_captions or None,
        nsfw_detectors=parsed_nsfw_detectors or None,
        misc_post_processors=parsed_unknown_forms or None,
    )

    dispatch_parameters = AIHordeR2DispatchParameters(
        generation_ids=[str(form.id_) for form in api_response.forms],
        dispatch_source=KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL,
        inference_backend=KNOWN_ALCHEMY_BACKEND.HORDE_ALCHEMIST,
        requested_backend_constraints=REQUESTED_BACKEND_CONSTRAINTS.SPECIFIED,
        no_valid_request_found_reasons=api_response.skipped or NoValidAlchemyFound(),
        r2_upload_url_map=r2_upload_url_map,
        source_image_fallback_choice=REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.ABANDON,
    )

    return alchemy_parameters, dispatch_parameters
