import horde_sdk.ai_horde_api as ai_horde_api
from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.utils.swagger import (
    SwaggerEndpoint,
    SwaggerParser,
)


def test_all_ai_horde_model_defs_in_swagger() -> None:
    """Ensure all models defined in ai_horde_api are defined in the swagger doc."""
    all_request_types = get_all_request_types(ai_horde_api.__name__)
    assert len(all_request_types) > 0, (
        f"Failed to find any request types in {ai_horde_api.__name__}. "
        "Something is critically wrong. Check `ai_horde_api/__init__.py` imports."
    )

    # Retrieve the swagger doc
    swagger_doc = None
    try:
        swagger_doc = SwaggerParser(get_ai_horde_swagger_url()).get_swagger_doc()
    except RuntimeError as e:
        raise RuntimeError(f"Failed to get swagger doc: {e}") from e
    assert swagger_doc, "Failed to get SwaggerDoc"

    swagger_defined_models = swagger_doc.definitions.keys()
    swagger_defined_examples: dict[
        str, dict[HTTPMethod, dict[str, object]]
    ] = swagger_doc.extract_all_payload_examples()

    for request_type in all_request_types:
        endpoint_subpath = request_type.get_endpoint_subpath()
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

            assert endpoint_subpath in swagger_defined_examples, f"Missing {request_type.__name__} in swagger examples"
