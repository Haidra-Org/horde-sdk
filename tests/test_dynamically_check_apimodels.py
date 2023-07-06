import json
import os
from pathlib import Path
from types import ModuleType

import horde_sdk.ai_horde_api as ai_horde_api
import horde_sdk.generic_api as generic_api
import horde_sdk.ratings_api as ratings_api
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import BaseResponse

EXAMPLE_RESPONSES: dict[ModuleType, Path] = {
    ai_horde_api: Path("tests/test_data/ai_horde_api/example_responses"),
    ratings_api: Path("tests/test_data/ratings_api/example_responses"),
}


class Test_reflection_and_dynamic:  # noqa: D101
    def test_example_response_folders_exist(self) -> None:  # noqa: D102
        for api, folder in EXAMPLE_RESPONSES.items():
            assert folder.exists(), f"Missing example response folder for {api.__name__}: {folder}"

    def test_get_all_request_types(self) -> None:  # noqa: D102
        supported_apis = [ai_horde_api, ratings_api]
        for api in supported_apis:
            all_request_types = get_all_request_types(api.__name__)
            assert len(all_request_types) > 0, f"Failed to find any request types in {api.__name__}"
            for request_type in all_request_types:
                assert issubclass(
                    request_type, generic_api.BaseRequest
                ), f"Request type is not a subclass if `BaseRequest`: {request_type}"

                assert issubclass(
                    request_type.get_expected_response_type(), BaseResponse
                ), f"Response type is not a subclass of `BaseResponse`: {request_type}"

    @staticmethod
    def dynamic_json_load(module_name: str, sample_data_folder: str | Path) -> None:
        """Attempts to create instances of all non-abstract children of `RequestBase`."""
        # This test does a lot of heavy lifting. If you're looking to make additions/changes.
        # This is probably the first test that will fail if you break something.
        #
        # If you're here because it failed and you're not sure why,
        # check the implementation of `BaseRequestUserSpecific` and `UserRatingsRequest`

        all_request_types: list[type[generic_api.BaseRequest]] = get_all_request_types(module_name)

        for request_type in all_request_types:
            # print(f"Testing {request_type.__name__}")
            assert issubclass(
                request_type, generic_api.BaseRequest
            ), f"Request type is not a subclass if `BaseRequest`: {request_type}"

            response_type: type[BaseResponse] = request_type.get_expected_response_type()
            assert issubclass(
                response_type, BaseResponse
            ), f"Response type is not a subclass of `BaseResponse`: {response_type}"

            target_file = f"{sample_data_folder}/{response_type.__name__}.json"
            assert os.path.exists(target_file), f"Missing sample data file: {target_file}"

            with open(target_file) as sample_file_handle:
                sample_data_json = json.loads(sample_file_handle.read())
                response_type(**sample_data_json)

    def test_horde_api(self) -> None:
        self.dynamic_json_load(ai_horde_api.__name__, EXAMPLE_RESPONSES[ai_horde_api])

    def test_ratings_api(self) -> None:
        self.dynamic_json_load(ratings_api.__name__, EXAMPLE_RESPONSES[ratings_api])
