import json
from types import NoneType, UnionType
from typing import Any

import pytest
from pydantic import BaseModel

import horde_sdk.ai_horde_api.apimodels
from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod, HTTPStatusCode, get_all_success_status_codes
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import HordeRequest, HordeResponse
from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH
from horde_sdk.generic_api.utils.swagger import (
    SwaggerDoc,
    SwaggerEndpoint,
    SwaggerParser,
)


def get_fields_descriptions_and_types(class_type: type[BaseModel]) -> dict[str, dict[str, str | list[str] | None]]:
    field_names_and_descriptions: dict[str, dict[str, str | list[str] | None]] = {}
    for field_name, field_info in class_type.model_fields.items():
        if field_info.description is not None:
            field_names_and_descriptions[field_name] = {"description": field_info.description}
        else:
            field_names_and_descriptions[field_name] = {"description": None}

        if field_info.annotation is not None:
            # Builtin-types should use their simple name while horde_sdk classes should use their fully qualified name
            # dict and list types should use their string representation
            types_list = []
            if isinstance(field_info.annotation, UnionType):
                for anno_type in field_info.annotation.__args__:
                    if "horde_sdk" in anno_type.__module__:
                        types_list.append(anno_type.__module__ + "." + anno_type.__name__)
                    elif hasattr(anno_type, "__origin__") and (
                        anno_type.__origin__ is dict or anno_type.__origin__ is list
                    ):
                        types_list.append(str(anno_type))
                    else:
                        types_list.append(anno_type.__name__ if anno_type is not NoneType else "None")
            else:
                if "horde_sdk" in field_info.annotation.__module__:
                    types_list.append(field_info.annotation.__module__ + "." + field_info.annotation.__name__)
                elif hasattr(field_info.annotation, "__origin__") and (
                    field_info.annotation.__origin__ is dict or field_info.annotation.__origin__ is list
                ):
                    types_list.append(str(field_info.annotation))
                else:
                    types_list.append(field_info.annotation.__name__)

            field_names_and_descriptions[field_name]["types"] = types_list

    return field_names_and_descriptions


@pytest.mark.object_verify
def all_ai_horde_model_defs_in_swagger(swagger_doc: SwaggerDoc) -> None:
    """Ensure all models defined in ai_horde_api are defined in the swagger doc."""
    all_request_types: list[type[HordeRequest]] = get_all_request_types(horde_sdk.ai_horde_api.apimodels.__name__)
    assert len(all_request_types) > 0, (
        f"Failed to find any request types in {horde_sdk.ai_horde_api.apimodels.__name__}. "
        "Something is critically wrong. Check `ai_horde_api/apimodels/__init__.py` imports."
    )

    swagger_defined_models = swagger_doc.definitions.keys()
    swagger_defined_payload_examples: dict[str, dict[HTTPMethod, dict[str, object]]]
    swagger_defined_payload_examples = swagger_doc.get_all_payload_examples()

    swagger_defined_response_examples: dict[str, dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list[Any]]]]
    swagger_defined_response_examples = swagger_doc.get_all_response_examples()

    api_to_sdk_payload_model_map: dict[str, dict[HTTPMethod, type[HordeRequest]]] = {}
    api_to_sdk_response_model_map: dict[str, dict[HTTPStatusCode, type[HordeResponse]]] = {}

    request_field_names_and_descriptions: dict[str, dict[str, dict[str, str | list[str] | None]]] = {}
    response_field_names_and_descriptions: dict[str, dict[str, dict[str, str | list[str] | None]]] = {}

    default_num_request_fields = len(HordeRequest.model_fields)

    for request_type in all_request_types:
        endpoint_subpath: GENERIC_API_ENDPOINT_SUBPATH = request_type.get_api_endpoint_subpath()
        assert endpoint_subpath, f"Failed to get endpoint subpath for {request_type.__name__}"

        # print(f"Found VERB: `{request_type.get_http_method()}` REQUEST TYPE: `{request_type.__name__}` in swagger")

        # Check if the endpoint subpath is defined in the Swagger documentation
        assert endpoint_subpath in swagger_doc.paths, f"Endpoint {endpoint_subpath} not found in the swagger"
        swagger_endpoint: SwaggerEndpoint = swagger_doc.paths[endpoint_subpath]

        # Check if the HTTP method used by the request type is defined in the Swagger documentation
        assert swagger_endpoint.get_endpoint_method_from_http_method(request_type.get_http_method()) is not None

        # If `.get_api_model_name()` is None, then the request type has no payload,
        # and is supposed to be a GET or DELETE
        if request_type.get_api_model_name() is None:
            assert request_type.get_http_method() in [
                HTTPMethod.GET,
                HTTPMethod.DELETE,
            ], (
                f"Request type {request_type.__name__} has no model name, but is not a GET or DELETE request. "
                "It should probably be a POST, PUT, or PATCH request."
            )
        # Otherwise, the request type has a payload, and is (probably) supposed to be a POST, PUT, or PATCH with
        # a payload
        else:
            if request_type.get_api_model_name() == _ANONYMOUS_MODEL:
                print(
                    f"Request type {request_type.__name__} has an anonymous model name. "
                    "This is probably not what you want. "
                    "Consider giving it a unique name on the API.",
                )
            else:

                assert (
                    request_type.get_api_model_name() in swagger_defined_models
                ), f"Model is defined in horde_sdk, but not in swagger: {request_type.get_api_model_name()}"

            assert endpoint_subpath in swagger_doc.paths, f"Missing {request_type.__name__} in swagger"

            assert (
                endpoint_subpath in swagger_defined_payload_examples
            ), f"Missing {request_type.__name__} in swagger examples"

        endpoint_http_status_code_responses: dict[HTTPStatusCode, dict[str, object] | list[Any]] | None | None = None

        if len(request_type.model_fields) == default_num_request_fields:
            print(f"Request type {request_type.__name__} has no additional fields")
        else:
            endpoint_http_method_examples = swagger_defined_response_examples.get(endpoint_subpath)
            assert endpoint_http_method_examples, f"Failed to get all HTTP method examples for {endpoint_subpath}"

            endpoint_http_status_code_responses = endpoint_http_method_examples.get(request_type.get_http_method())
            assert endpoint_http_status_code_responses, f"Failed to get example response for {request_type.__name__}"

        if endpoint_subpath not in api_to_sdk_payload_model_map:
            api_to_sdk_payload_model_map[endpoint_subpath] = {}

        api_to_sdk_payload_model_map[endpoint_subpath][request_type.get_http_method()] = request_type

        request_field_dict = get_fields_descriptions_and_types(request_type)
        request_field_names_and_descriptions[request_type.__name__] = request_field_dict

        endpoint_success_http_status_codes: list[HTTPStatusCode] = []

        if endpoint_http_status_code_responses is not None:
            endpoint_success_http_status_codes = [
                success_code
                for success_code in get_all_success_status_codes()
                if success_code in endpoint_http_status_code_responses
            ]
            assert (
                len(endpoint_success_http_status_codes) > 0
            ), f"Failed to find any success status codes in {request_type.__name__}"

            for success_code in endpoint_success_http_status_codes:
                assert (
                    success_code in request_type.get_success_status_response_pairs()
                ), f"Missing success response type for {request_type.__name__} with status code {success_code}"
        else:
            assert (
                request_type.get_default_success_response_type() is not None
            ), f"Failed to get default success response type for {request_type.__name__}"

        api_to_sdk_response_model_map[endpoint_subpath] = request_type.get_success_status_response_pairs()

        for response_type in request_type.get_success_status_response_pairs().values():
            if len(response_type.model_fields) == 0:
                print(f"Response type {response_type.__name__} has no fields")
                continue

            response_field_dict = get_fields_descriptions_and_types(response_type)
            response_field_names_and_descriptions[response_type.__name__] = response_field_dict

    def json_serializer(obj: object) -> object:
        if isinstance(obj, str):
            return obj
        if isinstance(obj, type):
            # Return the fully qualified (with all namespaces) name of the type
            return obj.__module__ + "." + obj.__name__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    with open("docs/api_to_sdk_payload_map.json", "w") as f:
        f.write(json.dumps(api_to_sdk_payload_model_map, indent=4, default=json_serializer))
        f.write("\n")

    with open("docs/api_to_sdk_response_map.json", "w") as f:
        f.write(json.dumps(api_to_sdk_response_model_map, indent=4, default=json_serializer))
        f.write("\n")

    with open("docs/request_field_names_and_descriptions.json", "w") as f:
        f.write(json.dumps(request_field_names_and_descriptions, indent=4, default=json_serializer))
        f.write("\n")

    with open("docs/response_field_names_and_descriptions.json", "w") as f:
        f.write(json.dumps(response_field_names_and_descriptions, indent=4, default=json_serializer))
        f.write("\n")


@pytest.mark.object_verify
def test_all_ai_horde_model_defs_in_swagger_from_prod_swagger() -> None:
    swagger_doc: SwaggerDoc | None = None
    try:
        swagger_doc = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url()).get_swagger_doc()
    except RuntimeError as e:
        raise RuntimeError(f"Failed to get swagger doc: {e}") from e
    assert swagger_doc, "Failed to get SwaggerDoc"
    assert swagger_doc.definitions, "Failed to get SwaggerDoc definitions"
    all_ai_horde_model_defs_in_swagger(swagger_doc)
