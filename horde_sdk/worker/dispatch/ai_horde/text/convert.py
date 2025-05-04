"""Contains functions to convert API responses to text generation parameters."""

from horde_sdk.ai_horde_api.apimodels.generate.text.pop import TextGenerateJobPopResponse
from horde_sdk.generation_parameters.text import (
    BasicTextGenerationFormatParameters,
    BasicTextGenerationParameters,
    KoboldAITextGenerationParameters,
)
from horde_sdk.worker.consts import (
    KNOWN_DISPATCH_SOURCE,
    KNOWN_INFERENCE_BACKEND,
    REQUESTED_BACKEND_CONSTRAINTS,
)
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeDispatchParameters


def convert_text_job_pop_response_to_parameters(
    api_response: TextGenerateJobPopResponse,
) -> tuple[KoboldAITextGenerationParameters, AIHordeDispatchParameters]:
    """Convert a text API response to the parameters for a generation."""
    dispatch_parameters = AIHordeDispatchParameters(
        generation_ids=[str(id_) for id_ in api_response.ids],
        dispatch_source=KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL,
        ttl=api_response.ttl,
        inference_backend=KNOWN_INFERENCE_BACKEND.IN_MODEL_NAME,
        requested_backend_constraints=REQUESTED_BACKEND_CONSTRAINTS.ANY,
        no_valid_request_found_reasons=api_response.skipped,
    )

    generation_parameters = KoboldAITextGenerationParameters(
        generation_ids=[str(id_) for id_ in api_response.ids],
        base_params=BasicTextGenerationParameters(
            model=api_response.model,
            prompt=api_response.payload.prompt,
            soft_prompt=api_response.softprompt,
            max_context_length=api_response.payload.max_context_length,
            max_length=api_response.payload.max_length,
            stop_sequence=api_response.payload.stop_sequence,
            temperature=api_response.payload.temperature,
            dynamic_temp_exponent=api_response.payload.dynatemp_exponent,
            dynamic_temp_range=api_response.payload.dynatemp_range,
            tfs=api_response.payload.tfs,
            typical=api_response.payload.typical,
            sampler_order=api_response.payload.sampler_order,
            smoothing_factor=api_response.payload.smoothing_factor,
            top_a=api_response.payload.top_a,
            top_k=api_response.payload.top_k,
            top_p=api_response.payload.top_p,
            min_p=api_response.payload.min_p,
            rep_pen=api_response.payload.rep_pen,
            rep_pen_range=api_response.payload.rep_pen_range,
            rep_pen_slope=api_response.payload.rep_pen_slope,
        ),
        format_params=BasicTextGenerationFormatParameters(
            frmtadsnsp=api_response.payload.frmtadsnsp,
            frmtrmblln=api_response.payload.frmtrmblln,
            frmtrmspch=api_response.payload.frmtrmspch,
            frmttriminc=api_response.payload.frmttriminc,
            singleline=api_response.payload.singleline,
        ),
        use_default_bad_words_ids=api_response.payload.use_default_badwordsids,
    )

    return generation_parameters, dispatch_parameters
