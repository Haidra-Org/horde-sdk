"""Offline checks for authenticated retrieval of submitted generation parameters."""

import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateSubmittedRequest, TextGenerateSubmittedRequest

_APIKEY = "0123456789abcdefghijkl"
_REQUEST_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.parametrize("request_type", [ImageGenerateSubmittedRequest, TextGenerateSubmittedRequest])
def test_recorded_submission_gets_send_the_original_key_in_the_header(
    request_type: type[ImageGenerateSubmittedRequest | TextGenerateSubmittedRequest],
) -> None:
    request = request_type(id=_REQUEST_ID, apikey=_APIKEY)
    parsed = AIHordeAPIManualClient()._validate_and_prepare_request(request)

    assert parsed.endpoint_no_query.endswith(f"/request/{_REQUEST_ID}")
    assert parsed.request_headers["apikey"] == _APIKEY
    assert request_type.is_api_key_required()
    assert parsed.request_body is None
