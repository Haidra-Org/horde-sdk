import json
import os
from pathlib import Path
from types import ModuleType

import horde_sdk.ai_horde_api as ai_horde_api
import horde_sdk.ai_horde_api.apimodels
import horde_sdk.generic_api as generic_api
import horde_sdk.ratings_api as ratings_api
import horde_sdk.ratings_api.apimodels
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import BaseResponse
from horde_sdk.generic_api.utils.swagger import SwaggerDoc

EXAMPLE_PAYLOADS: dict[ModuleType, Path] = {
    ai_horde_api: Path("tests/test_data/ai_horde_api/example_payloads"),
    ratings_api: Path("tests/test_data/ratings_api/example_payloads"),
}

EXAMPLE_RESPONSES: dict[ModuleType, Path] = {
    ai_horde_api: Path("tests/test_data/ai_horde_api/example_responses"),
    ratings_api: Path("tests/test_data/ratings_api/example_responses"),
}

EXAMPLE_PRODUCTION_RESPONSES: dict[ModuleType, Path] = {
    ai_horde_api: Path("tests/test_data/ai_horde_api/example_production_responses"),
    ratings_api: Path("tests/test_data/ratings_api/example_production_responses"),
}


class Test_reflection_and_dynamic:  # noqa: D101
    def test_example_response_folders_exist(self) -> None:  # noqa: D102
        for api, folder in EXAMPLE_RESPONSES.items():
            assert folder.exists(), f"Missing example response folder for {api.__name__}: {folder}"

    def test_get_all_request_types(self) -> None:  # noqa: D102
        supported_apis_models = [horde_sdk.ai_horde_api.apimodels, horde_sdk.ratings_api.apimodels]
        for api in supported_apis_models:
            all_request_types = get_all_request_types(api.__name__)
            assert len(all_request_types) > 0, f"Failed to find any request types in {api.__name__}"
            for request_type in all_request_types:
                assert issubclass(
                    request_type,
                    generic_api.BaseRequest,
                ), f"Request type is not a subclass if `BaseRequest`: {request_type}"

                assert issubclass(
                    request_type.get_success_response_type(),
                    BaseResponse,
                ), f"Response type is not a subclass of `BaseResponse`: {request_type}"

    @staticmethod
    def dynamic_json_load(module: ModuleType) -> None:
        """Attempts to create instances of all non-abstract children of `RequestBase`."""
        # This test does a lot of heavy lifting. If you're looking to make additions/changes.
        # This is probably the first test that will fail if you break something.
        #
        # If you're here because it failed and you're not sure why,
        # check the implementation of `BaseRequestUserSpecific` and `UserRatingsRequest`

        module_name = module.__name__
        example_payload_folder = EXAMPLE_PAYLOADS[module]
        example_response_folder = EXAMPLE_RESPONSES[module]

        all_request_types: list[type[generic_api.BaseRequest]] = get_all_request_types(module_name)

        for request_type in all_request_types:
            # print(f"Testing {request_type.__name__}")
            assert issubclass(
                request_type,
                generic_api.BaseRequest,
            ), f"Request type is not a subclass if `BaseRequest`: {request_type}"

            response_type: type[BaseResponse] = request_type.get_success_response_type()
            assert issubclass(
                response_type,
                BaseResponse,
            ), f"Response type is not a subclass of `BaseResponse`: {response_type}"

            if request_type.get_http_method() not in [HTTPMethod.GET, HTTPMethod.DELETE]:
                example_payload_filename = SwaggerDoc.filename_from_endpoint_path(
                    request_type.get_endpoint_subpath(),
                    request_type.get_http_method(),
                )

                target_payload_file_path = f"{example_payload_folder}/{example_payload_filename}.json"
                assert os.path.exists(
                    target_payload_file_path,
                ), f"Missing example payload file: {target_payload_file_path}"

            success_status_codes = request_type.get_success_status_response_pairs()
            for success_status_code, success_response_type in success_status_codes.items():
                example_response_filename = SwaggerDoc.filename_from_endpoint_path(
                    request_type.get_endpoint_subpath(),
                    request_type.get_http_method(),
                    http_status_code=success_status_code,
                )
                target_response_file_path = f"{example_response_folder}/{example_response_filename}.json"
                with open(target_response_file_path) as sample_file_handle:
                    sample_data_json = json.loads(sample_file_handle.read())
                    if response_type.is_array_response():
                        success_response_type().set_array(sample_data_json)
                    else:
                        success_response_type(**sample_data_json)

                example_production_response_file_path = (
                    f"{EXAMPLE_PRODUCTION_RESPONSES[module]}/{example_response_filename}.json"
                )
                if os.path.exists(example_production_response_file_path):
                    with open(example_production_response_file_path, encoding="utf8") as sample_file_handle:
                        sample_data_json = json.loads(sample_file_handle.read())
                        if response_type.is_array_response():
                            success_response_type().set_array(sample_data_json)
                        else:
                            _ = success_response_type(**sample_data_json)

    def test_horde_api(self) -> None:
        self.dynamic_json_load(ai_horde_api)

    # def test_ratings_api(self) -> None:
    #     self.dynamic_json_load(ratings_api)
