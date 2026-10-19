"""Offline checks for the moderator review and retained-evidence API contracts."""

import pytest
from pydantic import ValidationError
from yarl import URL

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import (
    ModerationOverviewRequest,
    PromptModerationEventsRequest,
    PromptModerationNote,
    PromptModerationNoteRequest,
    WorkerSuspicionEventsRequest,
)
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.consts import HTTPStatusCode

_APIKEY = "0123456789abcdefghijkl"


@pytest.mark.parametrize(
    "api_request",
    [
        ModerationOverviewRequest(worker_type=["image", "text"], suspicion_id=[1, 2], online=True),
        PromptModerationEventsRequest(event_id=5, user_id=7, worker_id="reporter", reason=["worker_csam"]),
        WorkerSuspicionEventsRequest(worker_id="subject", user_id=7, before_id=10),
    ],
)
def test_moderation_filters_are_query_parameters(api_request: BaseAIHordeRequest) -> None:
    api_request = api_request.model_copy(update={"apikey": _APIKEY})
    parsed = AIHordeAPIManualClient()._validate_and_prepare_request(api_request)

    assert parsed.request_body is None
    assert parsed.request_headers["apikey"] == _APIKEY
    for key in api_request.get_query_fields():
        value = getattr(api_request, key)
        if value is not None:
            expected = str(value).lower() if isinstance(value, bool) else value
            assert parsed.request_queries[key] == expected

    # aiohttp's query encoder rejects Python booleans and must preserve repeatable filters.
    query = URL(parsed.endpoint_no_query).with_query(parsed.request_queries).query
    if isinstance(api_request, ModerationOverviewRequest):
        assert query.getall("worker_type") == ["image", "text"]
        assert query.getall("suspicion_id") == ["1", "2"]
        assert query["online"] == "true"


def test_moderation_note_routes_the_event_id_and_expects_created() -> None:
    request = PromptModerationNoteRequest(event_id=5, note="Reviewed.", apikey=_APIKEY)
    parsed = AIHordeAPIManualClient()._validate_and_prepare_request(request)

    assert parsed.endpoint_no_query.endswith("/prompts/5/notes")
    assert parsed.request_body == {"note": "Reviewed."}
    assert request.get_success_status_response_pairs() == {HTTPStatusCode.CREATED: PromptModerationNote}


@pytest.mark.parametrize("note", ["", "x" * 2001, "before\x00after"])
def test_moderation_notes_reject_invalid_text(note: str) -> None:
    with pytest.raises(ValidationError):
        PromptModerationNoteRequest(event_id=5, note=note)
