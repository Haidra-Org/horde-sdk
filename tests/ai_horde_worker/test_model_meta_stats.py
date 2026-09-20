"""Network-free regression tests for statistics fetching during model selection."""

from unittest.mock import MagicMock

import pytest
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageStatsModelsResponse
from horde_sdk.worker.model_meta import ImageModelLoadResolver


def _resolver() -> ImageModelLoadResolver:
    manager = MagicMock(spec=ModelReferenceManager)
    manager.get_all_model_references.return_value = {}
    manager.get_model_reference.return_value = {}
    return ImageModelLoadResolver(model_reference_manager=manager)


def _stats(first: str, second: str) -> ImageStatsModelsResponse:
    return ImageStatsModelsResponse(day={}, month={first: 10, second: 1}, total={})


def test_combined_instructions_share_one_snapshot_and_refresh_on_the_next_call() -> None:
    client = MagicMock(spec=AIHordeAPIManualClient)
    client.submit_request.side_effect = [_stats("A", "B"), _stats("C", "D")]
    resolver = _resolver()
    instructions = ["top 1", "bottom 1", "top 2"]

    assert resolver.resolve_meta_instructions(instructions, client) == {"A", "B"}
    assert client.submit_request.call_count == 1
    assert resolver.resolve_meta_instructions(instructions, client) == {"C", "D"}
    assert client.submit_request.call_count == 2


def test_cached_stats_are_optional_across_resolution_calls() -> None:
    client = MagicMock(spec=AIHordeAPIManualClient)
    client.submit_request.side_effect = [_stats("A", "B"), _stats("C", "D")]
    resolver = _resolver()
    instructions = ["top 1", "bottom 1"]

    assert resolver.resolve_meta_instructions(instructions, client, use_cached_stats_response=True) == {"A", "B"}
    assert resolver.resolve_meta_instructions(instructions, client, use_cached_stats_response=True) == {"A", "B"}
    assert client.submit_request.call_count == 1
    assert resolver.resolve_meta_instructions(instructions, client) == {"C", "D"}
    assert client.submit_request.call_count == 2


@pytest.mark.parametrize("instructions", [[], ["Deliberate"], ["all"], ["all sdxl"], ["new 1"]])
def test_instructions_without_statistics_do_not_fetch(instructions: list[str]) -> None:
    client = MagicMock(spec=AIHordeAPIManualClient)
    resolver = _resolver()

    assert resolver.resolve_meta_instructions(instructions, client) == set()
    client.submit_request.assert_not_called()
