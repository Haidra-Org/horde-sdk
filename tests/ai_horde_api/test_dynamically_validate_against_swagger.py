import json

import horde_sdk.ai_horde_api.apimodels
from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.consts import HTTPMethod, HTTPStatusCode, get_all_success_status_codes
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import HordeRequest, HordeResponse
from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH
from horde_sdk.generic_api.utils.swagger import (
    SwaggerDoc,
    SwaggerEndpoint,
    SwaggerParser,
)


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

    swagger_defined_response_examples: dict[str, dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list]]]
    swagger_defined_response_examples = swagger_doc.get_all_response_examples()

    api_to_sdk_payload_model_map: dict[str, dict[HTTPMethod, type[HordeRequest]]] = {}
    api_to_sdk_response_model_map: dict[str, dict[HTTPStatusCode, type[HordeResponse]]] = {}

    request_field_names_and_descriptions: dict[str, list[tuple[str, str | None]]] = {}
    response_field_names_and_descriptions: dict[str, list[tuple[str, str | None]]] = {}

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
            assert (
                request_type.get_api_model_name() in swagger_defined_models
            ), f"Model is defined in horde_sdk, but not in swagger: {request_type.get_api_model_name()}"

            assert endpoint_subpath in swagger_doc.paths, f"Missing {request_type.__name__} in swagger"

            assert (
                endpoint_subpath in swagger_defined_payload_examples
            ), f"Missing {request_type.__name__} in swagger examples"

        endpoint_http_method_examples = swagger_defined_response_examples.get(endpoint_subpath)
        assert endpoint_http_method_examples, f"Failed to get all HTTP method examples for {endpoint_subpath}"

        endpoint_http_status_code_responses = endpoint_http_method_examples.get(request_type.get_http_method())
        assert endpoint_http_status_code_responses, f"Failed to get example response for {request_type.__name__}"

        if endpoint_subpath not in api_to_sdk_payload_model_map:
            api_to_sdk_payload_model_map[endpoint_subpath] = {}

        api_to_sdk_payload_model_map[endpoint_subpath][request_type.get_http_method()] = request_type

        for field_name, field_info in request_type.model_fields.items():
            if request_type.__name__ not in request_field_names_and_descriptions:
                request_field_names_and_descriptions[request_type.__name__] = []

            request_field_names_and_descriptions[request_type.__name__].append((field_name, field_info.description))

        endpoint_success_http_status_codes: list[HTTPStatusCode] = [
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

        api_to_sdk_response_model_map[endpoint_subpath] = request_type.get_success_status_response_pairs()

        for response_type in request_type.get_success_status_response_pairs().values():
            for field_name, field_info in response_type.model_fields.items():
                if response_type.__name__ not in response_field_names_and_descriptions:
                    response_field_names_and_descriptions[response_type.__name__] = []

                if field_info.description is not None:
                    response_field_names_and_descriptions[response_type.__name__].append(
                        (field_name, field_info.description),
                    )
                else:
                    response_field_names_and_descriptions[response_type.__name__].append((field_name, None))

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

    with open("docs/response_field_names_and_descriptions.json", "w") as f:
        f.write(json.dumps(response_field_names_and_descriptions, indent=4, default=json_serializer))


def test_all_ai_horde_model_defs_in_swagger_from_prod_swagger() -> None:
    swagger_doc: SwaggerDoc | None = None
    try:
        swagger_doc = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url()).get_swagger_doc()
    except RuntimeError as e:
        raise RuntimeError(f"Failed to get swagger doc: {e}") from e
    assert swagger_doc, "Failed to get SwaggerDoc"
    assert swagger_doc.definitions, "Failed to get SwaggerDoc definitions"
    all_ai_horde_model_defs_in_swagger(swagger_doc)
