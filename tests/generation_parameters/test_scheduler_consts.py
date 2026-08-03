"""The scheduler field, its precedence over the legacy karras flag, and the backend schedule mapping.

`karras` is a boolean that can name two of the nine schedules a backend implements. The field replaces
it without displacing it: an unset `scheduler` still derives from the flag, so existing requests render
exactly as they did.
"""

from horde_sdk.ai_horde_api.apimodels.base import ImageGenerateParamMixin
from horde_sdk.backend_parsing.image.comfyui.hordelib import (
    KNOWN_COMFYUI_IMAGE_SCHEDULERS,
    ComfyUIBackendValuesMapper,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SCHEDULERS
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
