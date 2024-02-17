"""Test generic API models not specific to a particular API."""

import json

from horde_sdk.generic_api.apimodels import RequestErrorResponse


def test_error_response() -> None:
    """Test that `RequestErrorResponse` can be instantiated from JSON."""
    with open("tests/test_data/RequestErrorResponse.json", encoding="utf-8") as error_response_file:
        json_error_response = json.load(error_response_file)
        RequestErrorResponse(**json_error_response)
