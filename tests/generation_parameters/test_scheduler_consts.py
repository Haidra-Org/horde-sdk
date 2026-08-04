"""The scheduler field, its precedence over the legacy karras flag, and the backend schedule mapping.

`karras` is a boolean that can name two of the schedules a backend implements. The field replaces it
without displacing it: an unset `scheduler` still derives from the flag, so existing requests render
exactly as they did.
"""

from horde_model_reference.meta_consts import (
    KNOWN_IMAGE_GENERATION_BASELINE,
)

from horde_sdk.ai_horde_api.apimodels.base import ImageGenerateParamMixin
from horde_sdk.backend_parsing.image.comfyui.hordelib import (
    KNOWN_COMFYUI_IMAGE_SCHEDULERS,
    ComfyUIBackendValuesMapper,
)
from horde_sdk.generation_parameters.image.constraints import is_scheduler_applicable
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_SCHEDULERS,
)
from horde_sdk.worker.dispatch.ai_horde.image.convert import resolve_scheduler


class TestBackCompatDefaults:
    def test_scheduler_defaults_to_unset(self) -> None:
        # Unset rather than "normal": the flag has to remain the thing that decides when nobody asked.
        assert ImageGenerateParamMixin().scheduler is None

    def test_karras_still_defaults_true(self) -> None:
        assert ImageGenerateParamMixin().karras is True


class TestSchedulerPrecedence:
    def test_explicit_scheduler_beats_the_flag(self) -> None:
        params = ImageGenerateParamMixin(scheduler=KNOWN_IMAGE_SCHEDULERS.sgm_uniform, karras=True)
        assert resolve_scheduler(params) == KNOWN_IMAGE_SCHEDULERS.sgm_uniform

    def test_karras_true_resolves_to_karras(self) -> None:
        assert resolve_scheduler(ImageGenerateParamMixin(karras=True)) == KNOWN_IMAGE_SCHEDULERS.karras

    def test_karras_false_resolves_to_normal(self) -> None:
        # Ruled: `karras: false` keeps meaning `normal`, so no existing request changes output.
        assert resolve_scheduler(ImageGenerateParamMixin(karras=False)) == KNOWN_IMAGE_SCHEDULERS.normal

    def test_every_schedule_survives_resolution(self) -> None:
        for schedule in KNOWN_IMAGE_SCHEDULERS:
            params = ImageGenerateParamMixin(scheduler=schedule, karras=False)
            assert resolve_scheduler(params) == schedule, schedule


class TestBackendScheduleMapping:
    def test_every_schedule_maps_both_directions(self) -> None:
        mapper = ComfyUIBackendValuesMapper()
        for schedule in KNOWN_IMAGE_SCHEDULERS:
            backend = mapper.map_to_backend_scheduler(schedule)
            assert mapper.map_to_sdk_scheduler(backend) == schedule, schedule

    def test_backend_and_api_vocabularies_agree(self) -> None:
        # The backend spells its schedules exactly as the API does; a divergence here would make the
        # identity mapping wrong rather than merely incomplete.
        assert {s.value for s in KNOWN_COMFYUI_IMAGE_SCHEDULERS} == {s.value for s in KNOWN_IMAGE_SCHEDULERS}

    def test_the_sigma_generator_schedules_are_mapped_too(self) -> None:
        # These two reach the backend through sigma-generator nodes rather than its scheduler list, so
        # it would be easy to leave them out of the mapping and make them unrequestable.
        mapper = ComfyUIBackendValuesMapper()
        for schedule in (KNOWN_IMAGE_SCHEDULERS.align_your_steps, KNOWN_IMAGE_SCHEDULERS.gits):
            assert mapper.map_to_sdk_scheduler(mapper.map_to_backend_scheduler(schedule)) == schedule


class TestSigmaGeneratorBaselineGate:
    def test_the_sigma_generator_schedules_are_baseline_restricted(self) -> None:
        for schedule in (KNOWN_IMAGE_SCHEDULERS.align_your_steps, KNOWN_IMAGE_SCHEDULERS.gits):
            assert not is_scheduler_applicable(schedule, KNOWN_IMAGE_GENERATION_BASELINE.flux_1)
            assert is_scheduler_applicable(schedule, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1)
            assert is_scheduler_applicable(schedule, KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl)

    def test_the_ordinary_schedules_are_not_restricted(self) -> None:
        restricted = {KNOWN_IMAGE_SCHEDULERS.align_your_steps, KNOWN_IMAGE_SCHEDULERS.gits}
        for schedule in KNOWN_IMAGE_SCHEDULERS:
            if schedule in restricted:
                continue
            for baseline in KNOWN_IMAGE_GENERATION_BASELINE:
                assert is_scheduler_applicable(schedule, baseline), (schedule, baseline)


class TestModelReferenceVocabularyLockstep:
    """The model reference names schedules too, and the two vocabularies have to agree.

    A model's `requirements` can demand a schedule, and the API checks that demand against the schedule a
    request actually resolves to. If the two enums drift, a model could require a schedule no request can
    ask for, or a request could name one no model can require. The model reference cannot import this
    package (it is the dependency, not the dependent), so the check lives here.
    """

    def test_the_vocabularies_are_identical(self) -> None:
        assert {str(s) for s in KNOWN_IMAGE_SCHEDULER} == {str(s) for s in KNOWN_IMAGE_SCHEDULERS}

    def test_every_api_schedule_can_be_required_by_a_model(self) -> None:
        for schedule in KNOWN_IMAGE_SCHEDULERS:
            assert is_known_image_scheduler(str(schedule)), schedule

    def test_the_two_legacy_flag_schedules_are_in_both(self) -> None:
        # These are the only two the karras boolean can express, on either side of the wire.
        for schedule in (KNOWN_IMAGE_SCHEDULERS.karras, KNOWN_IMAGE_SCHEDULERS.normal):
            assert is_known_image_scheduler(str(schedule))
            assert str(schedule) in {str(s) for s in KNOWN_IMAGE_SCHEDULER}
