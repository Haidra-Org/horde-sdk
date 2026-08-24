"""The solver-knob and flow-shift fields: their defaults, their serialization, and their dispatch.

Every one of these fields is optional and unset by default, because a request that names none of them
has to keep producing exactly the image it produced before they existed. The tests below pin both
halves of that: the wire shape of a request that sets nothing, and the forwarding of a request that
sets everything.
"""

import json
from uuid import UUID

from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateJobPopPayload,
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
)
from horde_sdk.ai_horde_api.apimodels.base import ImageGenerateParamMixin
from horde_sdk.generation_parameters.image.constraints import KNOWN_SAMPLER_SOLVER_TYPES
from horde_sdk.generation_parameters.image.object_models import (
    BasicImageGenerationParametersTemplate,
    default_basic_image_generation_parameters,
)
from horde_sdk.worker.dispatch.ai_horde.image.convert import (
    convert_image_job_pop_response_to_parameters,
    solver_knob_arguments,
)

SOLVER_KNOB_FIELD_NAMES = (
    "sampler_eta",
    "sampler_s_noise",
    "sampler_s_churn",
    "sampler_s_tmin",
    "sampler_s_tmax",
    "sampler_solver_type",
    "sampler_order",
    "flow_shift",
)

# Every optional field the mixin gained after the snapshots below were taken. The knobs are the bulk of
# it; control strength arrived later and is optional on the same terms.
MIXIN_FIELDS_ADDED_SINCE_SNAPSHOT = (*SOLVER_KNOB_FIELD_NAMES, "control_strength")

# The serialization of a default-constructed mixin immediately before these fields were introduced.
_MIXIN_JSON_BEFORE = (
    '{"height":512,"width":512,"sampler_name":"k_euler","scheduler":null,"karras":true,'
    '"cfg_scale":7.5,"denoising_strength":1.0,"clip_skip":1,"post_processing":[],'
    '"post_processing_order":"facefixers_first","facefixer_strength":null,"hires_fix":false,'
    '"hires_fix_denoising_strength":null,"loras":null,"tis":null,"workflow":null,'
    '"transparent":null,"tiling":false,"special":null,"seed":null,"seed_variation":null,'
    '"control_type":null,"image_is_control":null,"return_control_map":null,"extra_texts":null,'
    '"use_nsfw_censor":false}'
)

# The serialization of the example generation parameters immediately before the same change.
_TEMPLATE_JSON_BEFORE = (
    '{"schema_version":"1.0","underlying_generation_scheme":"MODEL","model":"EXAMPLE_MODEL",'
    '"model_baseline":"infer","prompt":"EXAMPLE_PROMPT","negative_prompt":null,"seed":"1",'
    '"height":512,"width":512,"steps":20,"cfg_scale":7.0,"sampler_name":"k_lms",'
    '"scheduler":"normal","clip_skip":1,"clip_skip_representation":"NEGATIVE_OFFSET",'
    '"denoising_strength":0.75,"tiling":null,"transparent":null}'
)

_EVERY_KNOB_SET = {
    "sampler_eta": 0.25,
    "sampler_s_noise": 1.5,
    "sampler_s_churn": 2.0,
    "sampler_s_tmin": 0.5,
    "sampler_s_tmax": 12.0,
    "sampler_solver_type": KNOWN_SAMPLER_SOLVER_TYPES.heun,
    "sampler_order": 3,
    "flow_shift": 3.5,
}


class TestDefaults:
    def test_the_mixin_leaves_every_knob_unset(self) -> None:
        payload = ImageGenerateParamMixin()
        for field_name in SOLVER_KNOB_FIELD_NAMES:
            assert getattr(payload, field_name) is None, field_name

    def test_the_generation_parameters_leave_every_knob_unset(self) -> None:
        for field_name in SOLVER_KNOB_FIELD_NAMES:
            assert getattr(default_basic_image_generation_parameters, field_name) is None, field_name

    def test_both_models_carry_the_same_field_names(self) -> None:
        # A knob present on only one side would be silently dropped somewhere in dispatch.
        mixin_fields = set(ImageGenerateParamMixin.model_fields)
        template_fields = set(BasicImageGenerationParametersTemplate.model_fields)

        assert set(SOLVER_KNOB_FIELD_NAMES) <= mixin_fields
        assert set(SOLVER_KNOB_FIELD_NAMES) <= template_fields


class TestSerializationIsUnchangedForOldRequests:
    """A request that sets none of the knobs must carry exactly what it carried before.

    A full dump does gain one null key per new field, which is the ordinary and backwards-compatible
    result of adding optional fields. What must not change is any pre-existing key, and what must not
    appear is any new *content*.
    """

    def test_an_unset_mixin_serializes_to_nothing_new(self) -> None:
        assert ImageGenerateParamMixin().model_dump_json(exclude_unset=True) == "{}"

    def test_an_explicitly_built_mixin_carries_only_what_was_asked_for(self) -> None:
        payload = ImageGenerateParamMixin(width=768, height=768, cfg_scale=5.0)

        assert payload.model_dump_json(exclude_unset=True) == '{"height":768,"width":768,"cfg_scale":5.0}'

    def test_every_pre_existing_mixin_key_is_untouched(self) -> None:
        before = json.loads(_MIXIN_JSON_BEFORE)
        after = json.loads(ImageGenerateParamMixin().model_dump_json())

        for key, value in before.items():
            assert after[key] == value, key

    def test_the_only_new_mixin_keys_are_the_expected_optional_fields(self) -> None:
        before = json.loads(_MIXIN_JSON_BEFORE)
        after = json.loads(ImageGenerateParamMixin().model_dump_json())

        assert set(after) - set(before) == set(MIXIN_FIELDS_ADDED_SINCE_SNAPSHOT)

    def test_every_pre_existing_generation_parameter_key_is_untouched(self) -> None:
        before = json.loads(_TEMPLATE_JSON_BEFORE)
        after = json.loads(default_basic_image_generation_parameters.model_dump_json())

        for key, value in before.items():
            assert after[key] == value, key

    def test_the_only_new_generation_parameter_keys_are_the_knobs(self) -> None:
        before = json.loads(_TEMPLATE_JSON_BEFORE)
        after = json.loads(default_basic_image_generation_parameters.model_dump_json())

        assert set(after) - set(before) == set(SOLVER_KNOB_FIELD_NAMES)

    def test_new_keys_serialize_as_null_when_unset(self) -> None:
        dumped = json.loads(ImageGenerateParamMixin().model_dump_json())

        for field_name in SOLVER_KNOB_FIELD_NAMES:
            assert dumped[field_name] is None, field_name


class TestKnobArgumentCollection:
    def test_unset_knobs_collect_as_none(self) -> None:
        collected = solver_knob_arguments(ImageGenerateParamMixin())

        assert dict(collected) == dict.fromkeys(SOLVER_KNOB_FIELD_NAMES)

    def test_set_knobs_collect_verbatim(self) -> None:
        collected = solver_knob_arguments(ImageGenerateParamMixin(**_EVERY_KNOB_SET))

        assert dict(collected) == _EVERY_KNOB_SET

    def test_collection_covers_every_knob_field(self) -> None:
        # A field added to the mixin but forgotten here would never reach a worker.
        assert set(solver_knob_arguments(ImageGenerateParamMixin())) == set(SOLVER_KNOB_FIELD_NAMES)


def _make_job_pop_response(single_id: UUID, payload: ImageGenerateJobPopPayload) -> ImageGenerateJobPopResponse:
    """Create a job pop response carrying the given payload."""
    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=payload,
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


class TestDispatchForwarding:
    def test_the_knobs_reach_the_base_generation_parameters(
        self,
        single_id: UUID,
        model_reference_manager: ModelReferenceManager,
    ) -> None:
        api_response = _make_job_pop_response(
            single_id,
            ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="42", **_EVERY_KNOB_SET),
        )

        conversion_result = convert_image_job_pop_response_to_parameters(
            api_response=api_response,
            model_reference_manager=model_reference_manager,
        )
        base_params = conversion_result.generation_parameters.base_params

        for field_name, expected in _EVERY_KNOB_SET.items():
            assert getattr(base_params, field_name) == expected, field_name

    def test_the_knobs_reach_both_hires_fix_passes(
        self,
        single_id: UUID,
        model_reference_manager: ModelReferenceManager,
    ) -> None:
        api_response = _make_job_pop_response(
            single_id,
            ImageGenerateJobPopPayload(
                prompt="a cat in a hat",
                seed="42",
                hires_fix=True,
                width=1024,
                height=1024,
                **_EVERY_KNOB_SET,
            ),
        )

        conversion_result = convert_image_job_pop_response_to_parameters(
            api_response=api_response,
            model_reference_manager=model_reference_manager,
        )
        hires_fix_params = conversion_result.generation_parameters.additional_params.hires_fix_params

        assert hires_fix_params is not None

        for field_name, expected in _EVERY_KNOB_SET.items():
            assert getattr(hires_fix_params.first_pass, field_name) == expected, field_name
            assert getattr(hires_fix_params.second_pass, field_name) == expected, field_name

    def test_unset_knobs_stay_unset_through_dispatch(
        self,
        single_id: UUID,
        model_reference_manager: ModelReferenceManager,
    ) -> None:
        api_response = _make_job_pop_response(
            single_id,
            ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="42"),
        )

        conversion_result = convert_image_job_pop_response_to_parameters(
            api_response=api_response,
            model_reference_manager=model_reference_manager,
        )
        base_params = conversion_result.generation_parameters.base_params

        for field_name in SOLVER_KNOB_FIELD_NAMES:
            assert getattr(base_params, field_name) is None, field_name
