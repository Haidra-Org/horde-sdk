import json

from horde_sdk.generic_api import RequestErrorResponse


def test_error_response():
    with open("tests/test_data/RequestErrorResponse.json") as error_response_file:
        json_error_response = json.load(error_response_file)
        RequestErrorResponse(**json_error_response)
