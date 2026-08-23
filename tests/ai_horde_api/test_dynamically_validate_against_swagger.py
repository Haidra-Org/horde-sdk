from typing import Any, cast, get_args

import pytest
from pydantic import AliasChoices, BaseModel, RootModel

import horde_sdk.ai_horde_api.apimodels
from horde_sdk import HordeAPIObject
from horde_sdk.ai_horde_api.endpoints import get_ai_horde_swagger_url
from horde_sdk.consts import (
    _ANONYMOUS_MODEL,
    _OVERLOADED_MODEL,
    HTTPMethod,
    HTTPStatusCode,
    get_all_success_status_codes,
)
from horde_sdk.generic_api._reflection import get_all_request_types
from horde_sdk.generic_api.apimodels import HordeRequest
from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH
from horde_sdk.generic_api.utils.swagger import (
    SwaggerDoc,
    SwaggerEndpoint,
    SwaggerModelDefinition,
    SwaggerModelRef,
    SwaggerParser,
)
from horde_sdk.meta import find_subclasses


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

    default_num_request_fields = len(HordeRequest.model_fields)

    sdk_defined_endpoint_verbs: dict[str, list[HTTPMethod]] = {}

    for request_type in all_request_types:
        endpoint_subpath: GENERIC_API_ENDPOINT_SUBPATH = request_type.get_api_endpoint_subpath()
        assert endpoint_subpath, f"Failed to get endpoint subpath for {request_type.__name__}"

        # print(f"Found VERB: `{request_type.get_http_method()}` REQUEST TYPE: `{request_type.__name__}` in swagger")

        # Check if the endpoint subpath is defined in the Swagger documentation
        assert endpoint_subpath in swagger_doc.paths, f"Endpoint {endpoint_subpath} not found in the swagger"
        swagger_endpoint: SwaggerEndpoint = swagger_doc.paths[endpoint_subpath]

        if endpoint_subpath not in sdk_defined_endpoint_verbs:
            sdk_defined_endpoint_verbs[endpoint_subpath] = []

        sdk_defined_endpoint_verbs[endpoint_subpath].append(request_type.get_http_method())

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
                assert request_type.get_api_model_name() in swagger_defined_models, (
                    f"Model is defined in horde_sdk, but not in swagger: {request_type.get_api_model_name()}"
                )

            assert endpoint_subpath in swagger_doc.paths, f"Missing {request_type.__name__} in swagger"

            assert endpoint_subpath in swagger_defined_payload_examples, (
                f"Missing {request_type.__name__} in swagger examples"
            )

        endpoint_http_status_code_responses: dict[HTTPStatusCode, dict[str, object] | list[Any]] | None | None = None

        if len(request_type.model_fields) == default_num_request_fields:
            print(f"Request type {request_type.__name__} has no additional fields")
        else:
            endpoint_http_method_examples = swagger_defined_response_examples.get(endpoint_subpath)
            assert endpoint_http_method_examples, f"Failed to get all HTTP method examples for {endpoint_subpath}"

            endpoint_http_status_code_responses = endpoint_http_method_examples.get(request_type.get_http_method())
            assert endpoint_http_status_code_responses, f"Failed to get example response for {request_type.__name__}"

        endpoint_success_http_status_codes: list[HTTPStatusCode] = []

        if endpoint_http_status_code_responses is not None:
            endpoint_success_http_status_codes = [
                success_code
                for success_code in get_all_success_status_codes()
                if success_code in endpoint_http_status_code_responses
            ]
            assert len(endpoint_success_http_status_codes) > 0, (
                f"Failed to find any success status codes in {request_type.__name__}"
            )

            for success_code in endpoint_success_http_status_codes:
                assert success_code in request_type.get_success_status_response_pairs(), (
                    f"Missing success response type for {request_type.__name__} with status code {success_code}"
                )
        else:
            assert request_type.get_default_success_response_type() is not None, (
                f"Failed to get default success response type for {request_type.__name__}"
            )

        for response_type in request_type.get_success_status_response_pairs().values():
            if len(response_type.model_fields) == 0:
                print(f"Response type {response_type.__name__} has no fields")

    endpoint_verbs_missing_from_sdk: dict[str, list[HTTPMethod]] = {}
    endpoint_verbs_missing_from_swagger: dict[str, list[HTTPMethod]] = {}

    for sdk_endpoint_subpath, sdk_endpoint_verbs in sdk_defined_endpoint_verbs.items():
        all_swagger_endpoint_verbs = swagger_doc.get_all_verbs_for_endpoint(sdk_endpoint_subpath)

        # Identify verbs missing from SDK
        missing_from_sdk = [verb for verb in all_swagger_endpoint_verbs if verb not in sdk_endpoint_verbs]
        if missing_from_sdk:
            endpoint_verbs_missing_from_sdk[sdk_endpoint_subpath] = missing_from_sdk

        # Identify verbs missing from Swagger
        missing_from_swagger = [verb for verb in sdk_endpoint_verbs if verb not in all_swagger_endpoint_verbs]
        if missing_from_swagger:
            endpoint_verbs_missing_from_swagger[sdk_endpoint_subpath] = missing_from_swagger

    assert not endpoint_verbs_missing_from_sdk, (
        "The following endpoints are defined in the Swagger documentation but not in the SDK: "
        f"{endpoint_verbs_missing_from_sdk}"
    )
    assert not endpoint_verbs_missing_from_swagger, (
        "The following endpoints are defined in the SDK but not in the Swagger documentation: "
        f"{endpoint_verbs_missing_from_swagger}"
    )


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


def _swagger_definition_property_names(swagger_doc: SwaggerDoc, definition_name: str) -> set[str]:
    """Return every property a swagger definition declares, following ``allOf`` references."""
    properties: set[str] = set()

    def _collect(name: str, seen: set[str]) -> None:
        if name in seen:
            return
        seen.add(name)

        definition = swagger_doc.definitions.get(name)
        if definition is None:
            return

        if isinstance(definition, SwaggerModelDefinition):
            if definition.properties:
                properties.update(definition.properties.keys())
            return

        _method, sub_definitions = definition.get_model_definitions()
        for sub_definition in sub_definitions:
            if isinstance(sub_definition, SwaggerModelRef) and sub_definition.ref:
                ref = sub_definition.ref
                if ref.startswith("#/definitions/"):
                    ref = ref[len("#/definitions/") :]
                _collect(ref, seen)
            elif isinstance(sub_definition, SwaggerModelDefinition) and sub_definition.properties:
                properties.update(sub_definition.properties.keys())

    _collect(definition_name, set())
    # A `*` property is a wildcard for additionalProperties, not a concrete field.
    return properties - {"*"}


def _inner_base_models(annotation: object) -> list[type[BaseModel]]:
    """Return the pydantic model types reachable through a (possibly generic) field annotation."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return [annotation]

    inner: list[type[BaseModel]] = []
    for arg in get_args(annotation):
        inner.extend(_inner_base_models(arg))
    return inner


def _sdk_field_names(model: type[BaseModel], seen: set[type[BaseModel]] | None = None) -> set[str]:
    """Return every wire name (field name and aliases) a model can accept."""
    if seen is None:
        seen = set()
    if model in seen:
        return set()
    seen.add(model)

    # A RootModel exposes its wire fields through its `root` type.
    if issubclass(model, RootModel):
        root_names: set[str] = set()
        root_annotation = model.model_fields["root"].annotation
        for inner_model in _inner_base_models(root_annotation):
            root_names.update(_sdk_field_names(inner_model, seen))
        return root_names

    names: set[str] = set()
    for field_name, field_info in model.model_fields.items():
        names.add(field_name)
        if field_info.alias is not None:
            names.add(field_info.alias)
        validation_alias = field_info.validation_alias
        if isinstance(validation_alias, AliasChoices):
            for choice in validation_alias.choices:
                if isinstance(choice, str):
                    names.add(choice)
        elif isinstance(validation_alias, str):
            names.add(validation_alias)
        if field_info.serialization_alias is not None:
            names.add(field_info.serialization_alias)
    return names


_KNOWN_FIELD_MISMATCHES: dict[str, set[str]] = {
    # The API reuses the image `SubmitInputStable` schema for alchemy submissions; the SDK models only the
    # fields alchemy actually consumes.
    "AlchemyJobSubmitRequest": {"seed", "censored", "gen_metadata", "generation"},
    # Privileged/admin fields that the public client cannot use.
    "UserDetailsResponse": {"proxy_passkey"},
    "ModifyUserResponse": {"proxy_passkey"},
    "ModifyUserRequest": {"generate_proxy_passkey"},
}


def all_ai_horde_model_fields_in_swagger(swagger_doc: SwaggerDoc) -> None:
    """Ensure every SDK model covers every field its swagger definition declares."""
    all_classes = find_subclasses(horde_sdk.ai_horde_api.apimodels, HordeAPIObject)

    missing_fields: dict[str, set[str]] = {}

    for class_type in all_classes:
        if not issubclass(class_type, HordeAPIObject):
            continue
        model_name = class_type.get_api_model_name()
        if model_name in (None, _ANONYMOUS_MODEL, _OVERLOADED_MODEL):
            continue
        if model_name not in swagger_doc.definitions:
            continue

        swagger_fields = _swagger_definition_property_names(swagger_doc, model_name)
        sdk_fields = _sdk_field_names(cast(type[BaseModel], class_type))

        missing = (swagger_fields - sdk_fields) - _KNOWN_FIELD_MISMATCHES.get(class_type.__name__, set())
        if missing:
            missing_fields[class_type.__name__] = missing

    assert not missing_fields, (
        f"The following SDK models are missing fields that their swagger definitions declare: {missing_fields}"
    )


@pytest.mark.object_verify
def test_all_ai_horde_model_fields_match_swagger_from_prod_swagger() -> None:
    swagger_doc: SwaggerDoc | None = None
    try:
        swagger_doc = SwaggerParser(swagger_doc_url=get_ai_horde_swagger_url()).get_swagger_doc()
    except RuntimeError as e:
        raise RuntimeError(f"Failed to get swagger doc: {e}") from e
    assert swagger_doc, "Failed to get SwaggerDoc"
    assert swagger_doc.definitions, "Failed to get SwaggerDoc definitions"
    all_ai_horde_model_fields_in_swagger(swagger_doc)
