from horde_sdk.ai_horde_api.apimodels.generate.text.pop import TextGenerateJobPopResponse
from horde_sdk.worker.consts import (
    KNOWN_DISPATCH_SOURCE,
    KNOWN_INFERENCE_BACKEND,
    REQUESTED_BACKEND_CONSTRAINTS,
)
from horde_sdk.worker.dispatch.ai_horde.text.convert import (
    convert_text_job_pop_response_to_parameters,
)


def test_convert_text_job_pop_response_to_parameters(
    simple_text_gen_job_pop_response: TextGenerateJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    generation_parameters, dispatch_parameters = convert_text_job_pop_response_to_parameters(
        simple_text_gen_job_pop_response,
    )

    # Dispatch parameters.
    assert dispatch_parameters.generation_ids == simple_text_gen_job_pop_response.ids
    assert dispatch_parameters.dispatch_source == KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL
    assert dispatch_parameters.ttl == simple_text_gen_job_pop_response.ttl
    assert dispatch_parameters.inference_backend == KNOWN_INFERENCE_BACKEND.IN_MODEL_NAME
    assert dispatch_parameters.requested_backend_constraints == REQUESTED_BACKEND_CONSTRAINTS.ANY
    assert dispatch_parameters.no_valid_request_found_reasons == simple_text_gen_job_pop_response.skipped

    # Base generation parameters.
    assert generation_parameters.generation_ids == simple_text_gen_job_pop_response.ids

    assert generation_parameters.base_params.model == simple_text_gen_job_pop_response.model
    assert generation_parameters.base_params.prompt == simple_text_gen_job_pop_response.payload.prompt
    assert generation_parameters.base_params.soft_prompt == simple_text_gen_job_pop_response.softprompt
    assert (
        generation_parameters.base_params.max_context_length
        == simple_text_gen_job_pop_response.payload.max_context_length
    )
    assert generation_parameters.base_params.max_length == simple_text_gen_job_pop_response.payload.max_length
    assert generation_parameters.base_params.stop_sequence == simple_text_gen_job_pop_response.payload.stop_sequence
    assert generation_parameters.base_params.temperature == simple_text_gen_job_pop_response.payload.temperature
    assert (
        generation_parameters.base_params.dynamic_temp_exponent
        == simple_text_gen_job_pop_response.payload.dynatemp_exponent
    )
    assert (
        generation_parameters.base_params.dynamic_temp_range == simple_text_gen_job_pop_response.payload.dynatemp_range
    )
    assert generation_parameters.base_params.tfs == simple_text_gen_job_pop_response.payload.tfs
    assert generation_parameters.base_params.typical == simple_text_gen_job_pop_response.payload.typical
    assert generation_parameters.base_params.sampler_order == simple_text_gen_job_pop_response.payload.sampler_order
    assert (
        generation_parameters.base_params.smoothing_factor == simple_text_gen_job_pop_response.payload.smoothing_factor
    )
    assert generation_parameters.base_params.top_a == simple_text_gen_job_pop_response.payload.top_a
    assert generation_parameters.base_params.top_k == simple_text_gen_job_pop_response.payload.top_k
    assert generation_parameters.base_params.top_p == simple_text_gen_job_pop_response.payload.top_p
    assert generation_parameters.base_params.min_p == simple_text_gen_job_pop_response.payload.min_p
    assert generation_parameters.base_params.rep_pen == simple_text_gen_job_pop_response.payload.rep_pen
    assert generation_parameters.base_params.rep_pen_range == simple_text_gen_job_pop_response.payload.rep_pen_range
    assert generation_parameters.base_params.rep_pen_slope == simple_text_gen_job_pop_response.payload.rep_pen_slope

    # Format parameters.
    format_params = generation_parameters.format_params

    assert format_params is not None

    assert format_params.frmtadsnsp == simple_text_gen_job_pop_response.payload.frmtadsnsp
    assert format_params.frmtrmblln == simple_text_gen_job_pop_response.payload.frmtrmblln
    assert format_params.frmtrmspch == simple_text_gen_job_pop_response.payload.frmtrmspch
    assert format_params.frmttriminc == simple_text_gen_job_pop_response.payload.frmttriminc
    assert format_params.singleline == simple_text_gen_job_pop_response.payload.singleline

    # KoboldAI parameters.
    koboldai_params = generation_parameters.koboldai_params

    assert koboldai_params is not None
    assert (
        koboldai_params.use_default_bad_words_ids == simple_text_gen_job_pop_response.payload.use_default_badwordsids
    )
