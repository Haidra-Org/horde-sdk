from horde_sdk.ai_horde_api.apimodels import (
    AlchemyJobPopResponse,
    NoValidAlchemyFound,
)
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
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_MISC_POST_PROCESSORS,
    KNOWN_NSFW_DETECTOR,
    KNOWN_UPSCALERS,
)
from horde_sdk.worker.consts import KNOWN_DISPATCH_SOURCE, REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE
from horde_sdk.worker.dispatch.ai_horde.alchemy.convert import (
    convert_alchemy_job_pop_response_to_parameters,
)
from horde_sdk.worker.dispatch.ai_horde_parameters import AIHordeR2DispatchParameters


def assert_common_parameters(
    generation_parameters: AlchemyParameters,
    dispatch_parameters: AIHordeR2DispatchParameters,
    api_response: AlchemyJobPopResponse,
) -> None:
    """Assert that the common parameters are correct."""
    assert dispatch_parameters.dispatch_source == KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL
    assert dispatch_parameters.ttl is None

    assert isinstance(generation_parameters, AlchemyParameters)
    assert isinstance(dispatch_parameters, AIHordeR2DispatchParameters)

    assert api_response.skipped == NoValidAlchemyFound()
    assert api_response.forms is not None

    assert dispatch_parameters.source_image_fallback_choice == REQUESTED_SOURCE_IMAGE_FALLBACK_CHOICE.ABANDON

    for generation_id in api_response.ids:
        assert any(str(generation_id) == x.generation_id for x in generation_parameters.all_alchemy_operations)

    for single_generation in generation_parameters.all_alchemy_operations:
        assert isinstance(single_generation, SingleAlchemyParameters)

        if isinstance(single_generation, UpscaleAlchemyParameters):
            assert single_generation.form == KNOWN_ALCHEMY_FORMS.post_process
            assert single_generation.upscaler in KNOWN_UPSCALERS
        elif isinstance(single_generation, FacefixAlchemyParameters):
            assert single_generation.form == KNOWN_ALCHEMY_FORMS.post_process
            assert single_generation.facefixer in KNOWN_FACEFIXERS
        elif isinstance(single_generation, InterrogateAlchemyParameters):
            assert single_generation.form == KNOWN_ALCHEMY_FORMS.interrogation
            assert single_generation.interrogator in KNOWN_INTERROGATORS
        elif isinstance(single_generation, CaptionAlchemyParameters):
            assert single_generation.form == KNOWN_ALCHEMY_FORMS.caption
            assert single_generation.caption_model in KNOWN_CAPTION_MODELS
        elif isinstance(single_generation, NSFWAlchemyParameters):
            assert single_generation.form == KNOWN_ALCHEMY_FORMS.nsfw
            assert single_generation.nsfw_detector in KNOWN_NSFW_DETECTOR


def test_convert_alchemy_job_pop_response_to_parameters_interrogate(
    simple_alchemy_gen_job_pop_response_interrogate: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_interrogate.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_interrogate.forms) == 1

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_interrogate,
    )

    assert len(generation_parameters.all_alchemy_operations) == 1

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_interrogate,
    )

    assert isinstance(generation_parameters.all_alchemy_operations[0], InterrogateAlchemyParameters)


def test_convert_alchemy_job_pop_response_to_parameters_nsfw_detect(
    simple_alchemy_gen_job_pop_response_nsfw_detect: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_nsfw_detect.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_nsfw_detect.forms) == 1

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_nsfw_detect,
    )

    assert len(generation_parameters.all_alchemy_operations) == 1

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_nsfw_detect,
    )

    assert isinstance(generation_parameters.all_alchemy_operations[0], NSFWAlchemyParameters)


def test_convert_alchemy_job_pop_response_to_parameters_all_feature_extractions(
    simple_alchemy_gen_job_pop_response_all_feature_extractions: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_all_feature_extractions.forms is not None

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_all_feature_extractions,
    )

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_all_feature_extractions,
    )

    all_types = [type(x) for x in generation_parameters.all_alchemy_operations]

    assert InterrogateAlchemyParameters in all_types
    assert CaptionAlchemyParameters in all_types
    assert NSFWAlchemyParameters in all_types


def test_convert_alchemy_job_pop_response_to_parameters_upscale(
    simple_alchemy_gen_job_pop_response_upscale: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_upscale.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_upscale.forms) == 1

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_upscale,
    )

    assert len(generation_parameters.all_alchemy_operations) == 1

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_upscale,
    )

    assert isinstance(generation_parameters.all_alchemy_operations[0], UpscaleAlchemyParameters)


def test_convert_alchemy_job_pop_response_to_parameters_upscale_multiple(
    simple_alchemy_gen_job_pop_response_upscale_multiple: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_upscale_multiple.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_upscale_multiple.forms) == 2

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_upscale_multiple,
    )

    assert len(generation_parameters.all_alchemy_operations) == 2

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_upscale_multiple,
    )

    assert all(type(x) is UpscaleAlchemyParameters for x in generation_parameters.all_alchemy_operations)


def test_convert_alchemy_job_pop_response_to_parameters_facefix(
    simple_alchemy_gen_job_pop_response_facefix: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_facefix.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_facefix.forms) == 1

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_facefix,
    )

    assert len(generation_parameters.all_alchemy_operations) == 1

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_facefix,
    )

    assert isinstance(generation_parameters.all_alchemy_operations[0], FacefixAlchemyParameters)


def test_convert_alchemy_job_pop_response_to_parameters_facefix_multiple(
    simple_alchemy_gen_job_pop_response_facefix_multiple: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_facefix_multiple.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_facefix_multiple.forms) == 2

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_facefix_multiple,
    )

    assert len(generation_parameters.all_alchemy_operations) == 2

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_facefix_multiple,
    )

    assert all(type(x) is FacefixAlchemyParameters for x in generation_parameters.all_alchemy_operations)


def test_convert_alchemy_job_pop_response_to_parameters_strip_background(
    simple_alchemy_gen_job_pop_response_strip_background: AlchemyJobPopResponse,
) -> None:
    """Confirm that API responses are correctly mapped to generation parameters."""
    assert simple_alchemy_gen_job_pop_response_strip_background.forms is not None
    assert len(simple_alchemy_gen_job_pop_response_strip_background.forms) == 1

    generation_parameters, dispatch_parameters = convert_alchemy_job_pop_response_to_parameters(
        simple_alchemy_gen_job_pop_response_strip_background,
    )

    assert len(generation_parameters.all_alchemy_operations) == 1

    assert_common_parameters(
        generation_parameters,
        dispatch_parameters,
        simple_alchemy_gen_job_pop_response_strip_background,
    )

    assert generation_parameters.all_alchemy_operations[0].form == KNOWN_MISC_POST_PROCESSORS.strip_background
