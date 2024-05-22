"""Check that all models defined in all APIs `apimodels` module/subpackage can be instantiated from example JSON."""

import json
import os
from pathlib import Path
from types import ModuleType

import pytest
from loguru import logger

import horde_sdk.ai_horde_api.apimodels
import horde_sdk.ratings_api.apimodels
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import HordeRequest, HordeResponse
from horde_sdk.generic_api.decoration import is_unhashable
from horde_sdk.generic_api.utils.swagger import SwaggerDoc

EXAMPLE_PAYLOADS: dict[ModuleType, Path] = {
    horde_sdk.ai_horde_api.apimodels: Path("tests/test_data/ai_horde_api/example_payloads"),
    horde_sdk.ratings_api.apimodels: Path("tests/test_data/ratings_api/example_payloads"),
}
"""Automatically generated example payloads based on the swagger doc."""

EXAMPLE_RESPONSES: dict[ModuleType, Path] = {
    horde_sdk.ai_horde_api.apimodels: Path("tests/test_data/ai_horde_api/example_responses"),
    horde_sdk.ratings_api.apimodels: Path("tests/test_data/ratings_api/example_responses"),
}
"""Automatically generated example responses based on the swagger doc."""

EXAMPLE_PRODUCTION_RESPONSES: dict[ModuleType, Path] = {
    horde_sdk.ai_horde_api.apimodels: Path("tests/test_data/ai_horde_api/example_production_responses"),
    horde_sdk.ratings_api.apimodels: Path("tests/test_data/ratings_api/example_production_responses"),
}
"""Automatically generated production responses based on the swagger doc."""

PRODUCTION_RESPONSES: dict[ModuleType, Path] = {
    horde_sdk.ai_horde_api.apimodels: Path("tests/test_data/ai_horde_api/production_responses"),
    horde_sdk.ratings_api.apimodels: Path("tests/test_data/ratings_api/production_responses"),
}
"""Manually generated production responses by the developers."""


class Test_reflection_and_dynamic:
    def test_example_response_folders_exist(self) -> None:
        for api, folder in EXAMPLE_RESPONSES.items():
            assert folder.exists(), f"Missing example response folder for {api.__name__}: {folder}"

    def test_get_all_request_types(self) -> None:
        """Tests the `get_all_request_types` function."""
        # Define a list of API modules to test.
        supported_apis_models = [horde_sdk.ai_horde_api.apimodels, horde_sdk.ratings_api.apimodels]

        # Loop through each API module and test its request types.
        for api in supported_apis_models:
            # Get a list of all request types in the API module.
            all_request_types = get_all_request_types(api.__name__)

            # Check that at least one request type was found.
            assert len(all_request_types) > 0, f"Failed to find any request types in {api.__name__}"

            # Loop through each request type and check that it is a subclass of `HordeRequest`.
            for request_type in all_request_types:
                assert issubclass(
                    request_type,
                    HordeRequest,
                ), f"Request type is not a subclass if `HordeRequest`: {request_type}"

                # Check that the success response type for the request type is a subclass of `HordeResponse`.
                assert issubclass(
                    request_type.get_default_success_response_type(),
                    HordeResponse,
                ), f"Response type is not a subclass of `HordeResponse`: {request_type}"

    @staticmethod
    def dynamic_json_load(module: ModuleType) -> None:
        """Attempts to create instances of all non-abstract children of `RequestBase`."""
        # Get the name of the module being tested.
        module_name = module.__name__

        # Get a list of all non-abstract request types in the module.
        all_request_types: list[type[HordeRequest]] = get_all_request_types(module_name)

        # Loop through each request type and test it.
        for request_type in all_request_types:
            # Check that the request type is a subclass of `HordeRequest`.
            assert issubclass(
                request_type,
                HordeRequest,
            ), f"Request type is not a subclass if `HordeRequest`: {request_type}"

            # Get the success response type for the request type.
            response_type: type[HordeResponse] = request_type.get_default_success_response_type()

            # Check that the response type is a subclass of `HordeResponse`.
            assert issubclass(
                response_type,
                HordeResponse,
            ), f"Response type is not a subclass of `HordeResponse`: {response_type}"

            # If the request type is not a GET or DELETE request, check that the example payload file exists.
            if request_type.get_http_method() not in [HTTPMethod.GET, HTTPMethod.DELETE]:
                example_payload_filename = SwaggerDoc.filename_from_endpoint_path(
                    request_type.get_api_endpoint_subpath(),
                    request_type.get_http_method(),
                )
                target_payload_file_path = f"{EXAMPLE_PAYLOADS[module]}/{example_payload_filename}.json"
                assert os.path.exists(
                    target_payload_file_path,
                ), f"Missing example payload file: {target_payload_file_path}"

            # Loop through each success status code and test the corresponding success response type.
            success_status_codes = request_type.get_success_status_response_pairs()
            for success_status_code, success_response_type in success_status_codes.items():
                if len(success_response_type.model_fields) == 0:
                    print(f"Response type {success_response_type.__name__} has no fields")
                    continue

                example_response_filename = SwaggerDoc.filename_from_endpoint_path(
                    request_type.get_api_endpoint_subpath(),
                    request_type.get_http_method(),
                    http_status_code=success_status_code,
                )
                example_response_file_path = f"{EXAMPLE_RESPONSES[module]}/{example_response_filename}.json"

                # Load the example response JSON from the file and validate it against the success response type.
                with open(example_response_file_path, encoding="utf-8") as sample_file_handle:
                    sample_data_json = json.loads(sample_file_handle.read())
                    try:
                        parsed_model = success_response_type.model_validate(sample_data_json)
                        try:
                            if is_unhashable(parsed_model):
                                logger.debug(f"Unhashable model for {example_response_file_path}")
                            else:
                                hash(parsed_model)
                        except NotImplementedError:
                            logger.debug(f"Hashing not implemented for {example_response_file_path}")
                        except Exception as e:
                            print(f"Failed to hash {example_response_file_path}")
                            print(f"Error: {e}")
                            raise e
                    except Exception as e:
                        print(f"Failed to validate {example_response_file_path}")
                        print(f"Error: {e}")
                        print(f"Sample data: {sample_data_json}")
                        raise e

                production_response_file_path = f"{PRODUCTION_RESPONSES[module]}/{example_response_filename}.json"

                # If a production response file exists, load it and validate it against the success response type.
                if os.path.exists(production_response_file_path):
                    with open(production_response_file_path, encoding="utf-8") as sample_file_handle:
                        sample_data_json = json.loads(sample_file_handle.read())
                        try:
                            parsed_model = success_response_type.model_validate(sample_data_json)
                            try:
                                if is_unhashable(parsed_model):
                                    logger.debug(f"Unhashable model for {example_response_file_path}")
                                else:
                                    hash(parsed_model)
                            except NotImplementedError:
                                logger.debug(f"Hashing not implemented for {example_response_file_path}")
                            except Exception as e:
                                print(f"Failed to hash {example_response_file_path}")
                                print(f"Error: {e}")
                                raise e
                        except Exception as e:
                            print(f"Failed to validate {production_response_file_path}")
                            print(f"Error: {e}")
                            print(f"Sample data: {sample_data_json}")
                            raise e

                # If an example production response file exists, load it and validate it against the success
                # response type.
                example_production_response_file_path = (
                    f"{EXAMPLE_PRODUCTION_RESPONSES[module]}/{example_response_filename}.json"
                )
                if os.path.exists(example_production_response_file_path):
                    with open(example_production_response_file_path, encoding="utf-8") as sample_file_handle:
                        sample_data_json = json.loads(sample_file_handle.read())
                        parsed_model = success_response_type.model_validate(sample_data_json)
                        try:
                            if is_unhashable(parsed_model):
                                logger.debug(f"Unhashable model for {example_response_file_path}")
                            else:
                                hash(parsed_model)
                        except NotImplementedError:
                            logger.debug(f"Hashing not implemented for {example_response_file_path}")
                        except Exception as e:
                            print(f"Failed to hash {example_response_file_path}")
                            print(f"Error: {e}")
                            raise e

    @pytest.mark.object_verify
    def test_horde_api(self) -> None:
        """Test all models in the `horde_sdk.ai_horde_api.apimodels` module can be instantiated from example JSON."""
        self.dynamic_json_load(horde_sdk.ai_horde_api.apimodels)

    # def test_ratings_api(self) -> None:
    #     self.dynamic_json_load(horde_sdk.ratings_api.apimodels)
