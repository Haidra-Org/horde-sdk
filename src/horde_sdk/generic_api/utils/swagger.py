from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path

import requests
from horde_sdk.consts import PAYLOAD_HTTP_METHODS, HTTPMethod, HTTPStatusCode
from loguru import logger
from pydantic import BaseModel, Field, model_validator
from typing_extensions import override


class SwaggerModelDefinitionAdditionalProperty(BaseModel):
    # TODO: Is this actually a recursive SwaggerModelDefinitionProperty?
    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    description: str | None = None


class SwaggerModelDefinitionProperty(BaseModel):
    """A property of a model (data structure) used in the API.

    This might also be referred to as a "field" or an "attribute" of the model.

    See https://swagger.io/docs/specification/data-models/data-types/#objects
    """

    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    description: str | None = None
    title: str | None = None
    default: object | None = None
    example: object | None = None
    format_: str | None = Field(None, alias="format")
    enum: list[str] | None = None
    ref: str | None = Field(None, alias="$ref")
    minimum: float | None = None
    maximum: float | None = None
    minLength: int | None = None
    maxLength: int | None = None
    multipleOf: float | None = None
    uniqueItems: bool | None = None
    additionalProperties: SwaggerModelDefinitionAdditionalProperty | None = None
    items: SwaggerModelDefinitionProperty | list[SwaggerModelDefinitionProperty] | None = None


class SwaggerModelDefinitionRef(BaseModel):
    """A reference to a model (data structure) used in the API."""

    model_config = {"extra": "forbid"}

    ref: str | None = Field(None, alias="$ref")


class SwaggerModelDefinitionEntry(BaseModel, ABC):
    """An entry in the definitions section of the swagger doc. This could be a model definition, or a schema validation
    method object. See `SwaggerModelDefinitionSchemaValidationMethods` for more info."""

    @abstractmethod
    def get_all_definitions(self) -> list[SwaggerModelDefinition | SwaggerModelDefinitionRef]:
        """Get all definitions from all validation methods."""
        raise NotImplementedError


class SwaggerModelDefinition(SwaggerModelDefinitionEntry):
    """A definition of a model (data structure) used in the API."""

    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    properties: dict[str, SwaggerModelDefinitionProperty] | None = None
    required: list[str] | None = None

    @override
    def get_all_definitions(self) -> list[SwaggerModelDefinition | SwaggerModelDefinitionRef]:
        """Get all definitions from all validation methods."""
        return [self]  # This looks odd, but `SwaggerModelDefinitionSchemaValidationMethods` is the wrinkle here.


class SwaggerModelDefinitionSchemaValidationMethods(SwaggerModelDefinitionEntry):
    """When used instead of a SwaggerModelDefinition, it means that the model is validated against one or more schemas.

    See the `allOf`, `oneOf`, and `anyOf` properties of the Swagger spec:
    https://swagger.io/docs/specification/data-models/oneof-anyof-allof-not/
    """

    model_config = {"extra": "forbid"}

    allOf: list[SwaggerModelDefinition | SwaggerModelDefinitionRef] | None = None
    """The model must match all of the schemas in this list."""
    oneOf: list[SwaggerModelDefinition | SwaggerModelDefinitionRef] | None = None
    """The model must match exactly one of the schemas in this list."""
    anyOf: list[SwaggerModelDefinition | SwaggerModelDefinitionRef] | None = None
    """The model must match at least one of the schemas in this list."""

    @model_validator(mode="before")
    def one_method_specified(cls, v):
        """Ensure at least one of the validation methods is specified."""
        if not any([v.get("allOf"), v.get("oneOf"), v.get("anyOf")]):
            raise ValueError("At least one of allOf, oneOf, or anyOf must be specified.")

        return v

    @override
    def get_all_definitions(self) -> list[SwaggerModelDefinition | SwaggerModelDefinitionRef]:
        """Get all definitions from all validation methods."""
        return_list = []
        if self.allOf:
            return_list.extend(self.allOf)
        if self.oneOf:
            return_list.extend(self.oneOf)
        if self.anyOf:
            return_list.extend(self.anyOf)

        return return_list


class SwaggerDocTagsItem(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    description: str | None = None


class SwaggerDocResponseItem(BaseModel):
    model_config = {"extra": "forbid"}

    description: str | None = None


class SwaggerDocInfo(BaseModel):
    model_config = {"extra": "forbid"}

    title: str | None = None
    version: str | None = None
    description: str | None = None


class SwaggerEndpointMethodParameterSchemaRef(BaseModel):
    model_config = {"extra": "forbid"}
    ref: str | None = Field(alias="$ref")


class SwaggerEndpointMethodParameterSchemaProperty(BaseModel):
    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    format_: str | None = Field(None, alias="format")


class SwaggerEndpointMethodParameterSchema(BaseModel):
    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    properties: dict[str, SwaggerEndpointMethodParameterSchemaProperty] | None = None


class SwaggerEndpointMethodParameter(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    in_: str = Field("", alias="in")
    description: str | None = None
    required: bool | None = None
    schema_: SwaggerEndpointMethodParameterSchema | SwaggerEndpointMethodParameterSchemaRef | None = Field(
        None, alias="schema"
    )
    default: object | None = None
    type_: str | None = Field(None, alias="type")
    format_: str | None = Field(None, alias="format")


class SwaggerEndpointResponseSchemaItem(BaseModel):
    # model_config = {"extra": "forbid"}

    ref: str | None = Field(None, alias="$ref")


class SwaggerEndpointResponseSchema(BaseModel):
    # model_config = {"extra": "forbid"}

    ref: str | None = Field(None, alias="$ref")
    type_: str | None = Field(None, alias="type")
    items: SwaggerEndpointResponseSchemaItem | None = None


class SwaggerEndpointResponse(BaseModel):
    model_config = {"extra": "forbid"}

    description: str
    schema_: SwaggerEndpointResponseSchema | None = Field(None, alias="schema")


class SwaggerEndpointMethod(BaseModel):
    model_config = {"extra": "forbid"}

    summary: str | None = None
    description: str | None = None
    operation_id: str | None = Field(None, alias="operationId")
    parameters: list[SwaggerEndpointMethodParameter] | None = None
    responses: dict[str, SwaggerEndpointResponse] | None = None
    tags: list[str] | None = None


class SwaggerEndpointParameter(BaseModel):
    model_config = {"extra": "forbid"}

    name: str | None = None
    in_: str = Field("", alias="in")
    description: str | None = None
    required: bool | None = None
    type_: str | None = Field(None, alias="type")


class SwaggerEndpoint(BaseModel):
    model_config = {"extra": "forbid"}

    parameters: list[SwaggerEndpointParameter] | None = None

    get: SwaggerEndpointMethod | None = None
    post: SwaggerEndpointMethod | None = None
    put: SwaggerEndpointMethod | None = None
    delete: SwaggerEndpointMethod | None = None
    patch: SwaggerEndpointMethod | None = None
    options: SwaggerEndpointMethod | None = None
    head: SwaggerEndpointMethod | None = None

    def get_endpoint_method_from_http_method(self, http_method: HTTPMethod | str) -> SwaggerEndpointMethod | None:
        """Get the endpoint method for the given HTTP method."""
        if isinstance(http_method, str):
            http_method = HTTPMethod(http_method)
        return getattr(self, http_method.value.lower(), None)

    def get_defined_endpoints(self) -> dict[str, SwaggerEndpointMethod]:
        """Get the endpoints that are specified in the swagger doc."""
        return_dict = {}
        for http_method, endpoint_method in self.__dict__.items():
            if isinstance(endpoint_method, SwaggerEndpointMethod):
                return_dict[http_method] = endpoint_method
        return return_dict

    @model_validator(mode="before")
    def at_least_one_method_specified(cls, v):
        """Ensure at least one method is specified."""
        if not any(
            [
                v.get("get"),
                v.get("post"),
                v.get("put"),
                v.get("delete"),
                v.get("patch"),
                v.get("options"),
                v.get("head"),
            ]
        ):
            raise ValueError("At least one method must be specified.")

        return v


class SwaggerDoc(BaseModel):
    model_config = {"extra": "forbid"}

    swagger: str
    """The swagger version of the document"""
    basePath: str
    """The base path (after the top level domain) of the API. IE, `/api`."""
    paths: dict[str, SwaggerEndpoint]
    """The endpoints of the API. IE, `/api/v2/generate/async`."""
    info: SwaggerDocInfo
    """The info section of the document"""
    produces: list[str]
    """The content types that the API can produce in responses."""
    consumes: list[str]
    """The content types that the API can consume in payloads."""
    tags: list[SwaggerDocTagsItem] | None = None
    """Metadata about the document."""
    responses: dict[str, SwaggerDocResponseItem] | None = None
    """Unknown"""
    definitions: dict[str, SwaggerModelDefinition | SwaggerModelDefinitionSchemaValidationMethods]
    """The definitions of the models (data structures) used in the API."""

    def extract_all_response_examples(self) -> dict[str, dict[HTTPMethod, dict[HTTPStatusCode, object]]]:
        """Extract all response examples from the swagger doc.

        This in the form of:
        `dict[endpoint_path, dict[http_method, dict[http_status_code, example_response]]]`
        """
        every_endpoint_example: dict[str, dict[HTTPMethod, dict[HTTPStatusCode, object]]] = {}

        # Iterate through each endpoint in the Swagger documentation
        for endpoint_path, endpoint in self.paths.items():
            endpoint_examples: dict[HTTPMethod, dict[HTTPStatusCode, object]] = {}

            # Iterate through each HTTP method used by the endpoint
            for http_method_name, endpoint_method_definition in endpoint.get_defined_endpoints().items():
                endpoint_method_examples: dict[HTTPStatusCode, object] = {}

                if not endpoint_method_definition.responses:
                    continue

                logger.debug(f"Found {endpoint_path} {http_method_name.upper()} with response")

                # Iterate through each defined response for the HTTP method
                for http_status_code_str, response_definition in endpoint_method_definition.responses.items():
                    http_status_code_object = HTTPStatusCode(int(http_status_code_str))

                    if not response_definition.schema_:
                        continue

                    # If the response schema is a reference to an API model, resolve the reference and include
                    # its defaults too
                    if isinstance(response_definition.schema_, SwaggerEndpointResponseSchema):
                        logger.debug(f"Resolving {response_definition.schema_.ref}")
                        example_response = self._resolve_model_ref_defaults(response_definition.schema_.ref)
                        endpoint_method_examples.update(
                            {http_status_code_object: example_response},
                        )
                    # If there is an explicit, endpoint specific schema, use that too
                    elif isinstance(response_definition.schema_, SwaggerEndpointResponseSchemaItem):
                        if not response_definition.schema_.ref:
                            continue
                        logger.debug(f"Resolving {response_definition.schema_.ref}")
                        example_response = self._resolve_model_ref_defaults(response_definition.schema_.ref)
                        endpoint_method_examples.update(
                            {http_status_code_object: example_response},
                        )

                if endpoint_method_examples:
                    endpoint_examples.update(
                        {HTTPMethod(http_method_name.upper()): endpoint_method_examples},
                    )

            if endpoint_examples:
                every_endpoint_example[endpoint_path] = endpoint_examples

        return every_endpoint_example

    def extract_all_payload_examples(self) -> dict[str, dict[HTTPMethod, dict[str, object]]]:
        """Extract all examples from the swagger doc.

        This in the form of:
        `dict[endpoint_path, dict[param_name, param_example_value]]]`
        """
        every_endpoint_example: dict[str, dict[HTTPMethod, dict[str, object]]] = {}
        for endpoint_path, endpoint in self.paths.items():
            endpoint_examples: dict[HTTPMethod, dict[str, object]] = {}

            for http_method_name, endpoint_method_definition in endpoint.get_defined_endpoints().items():
                if http_method_name.upper() not in PAYLOAD_HTTP_METHODS:
                    continue

                if not endpoint_method_definition.parameters:
                    continue

                logger.debug(f"Found {endpoint_path} {http_method_name.upper()} with payload")
                _payload_definitions = [d for d in endpoint_method_definition.parameters if d.name == "payload"]

                if len(_payload_definitions) != 1:
                    raise RuntimeError(
                        f"Expected to find exactly one payload definition for {endpoint_path} {http_method_name}"
                    )

                payload_definition = _payload_definitions[0]

                if not payload_definition.schema_:
                    raise RuntimeError(
                        f"Expected to find a schema for {endpoint_path} {http_method_name} payload definition"
                    )

                if isinstance(payload_definition.schema_, SwaggerEndpointMethodParameterSchemaRef):
                    logger.debug(f"Resolving {payload_definition.schema_.ref}")
                    example_payload = self._resolve_model_ref_defaults(payload_definition.schema_.ref)
                    endpoint_examples.update(
                        {HTTPMethod(http_method_name.upper()): example_payload},
                    )

                elif isinstance(payload_definition.schema_, SwaggerEndpointMethodParameterSchema):
                    if not payload_definition.schema_.properties:
                        continue
                    if not payload_definition.required:
                        continue
                    endpoint_specific_schema = {}
                    for prop_name, prop in payload_definition.schema_.properties.items():
                        if not prop.type_:
                            raise RuntimeError(
                                f"Expected to find a type for {endpoint_path} {http_method_name} payload definition"
                            )
                        endpoint_specific_schema[prop_name] = default_swagger_value_from_type_name(prop.type_)

                    endpoint_examples.update(
                        {HTTPMethod(http_method_name.upper()): endpoint_specific_schema},
                    )

            if endpoint_examples:
                every_endpoint_example[endpoint_path] = endpoint_examples

        return every_endpoint_example

    @staticmethod
    def filename_from_endpoint_path(endpoint_path: str, http_method: HTTPMethod) -> str:
        """Get the filename for the given endpoint path."""
        endpoint_path = re.sub(r"\W+", "_", endpoint_path)
        endpoint_path = endpoint_path + "_" + http_method.value.lower()
        return re.sub(r"__+", "_", endpoint_path)

    def write_all_payload_examples_to_file(self, directory: str | Path) -> bool:
        directory = Path(directory)
        all_examples = self.extract_all_payload_examples()
        for endpoint_path, endpoint_examples_info in all_examples.items():
            for http_method, example_payload in endpoint_examples_info.items():
                filename = self.filename_from_endpoint_path(endpoint_path, http_method)
                filepath = directory / f"{filename}.json"
                with open(filepath, "w") as f:
                    json.dump(example_payload, f, indent=4)
        return True

    def _resolve_model_ref_defaults(
        self,
        ref: str | None,
    ) -> dict[str, object]:
        """For ref entries, recursively resolve the default values for all properties.

        Note that this will combine all properties from all definitions that are referenced.
        This function is more useful when trying to determine the expected payload for a request
        or the expected response for a particular endpoint, rather than the schema for a particular model.
        """
        # example ref: "#/definitions/RequestError"

        if not ref:
            return {}

        return_dict = {}

        if ref.startswith("#/definitions/"):
            ref = ref[len("#/definitions/") :]

        if ref not in self.definitions:
            raise RuntimeError(f"Failed to find definition for {ref}")

        found_def_parent = self.definitions[ref]

        logger.debug(f"Found definition for {ref}")

        all_defs = found_def_parent.get_all_definitions()

        if not all_defs:
            raise RuntimeError(f"Failed to find any definitions for {ref}")
        for definition in all_defs:
            if not isinstance(definition, SwaggerModelDefinitionRef):
                continue

            logger.debug(f"Recursing ref: {definition.ref}")
            return_dict.update(self._resolve_model_ref_defaults(definition.ref))

        if len(all_defs) > 1:
            logger.debug(f"Found {len(all_defs)} definitions for {ref}")

        for definition in all_defs:
            if not isinstance(definition, SwaggerModelDefinition):
                if definition.ref:
                    continue
                raise RuntimeError(f"Unexpected definition type: {type(definition)}")

            if not definition.properties:
                continue

            for prop_name, prop in definition.properties.items():
                if prop_name == "models":
                    pass
                if prop.ref:
                    continue
                if prop.example is not None:
                    return_dict[prop_name] = prop.example
                    continue
                if prop.default is not None:
                    return_dict[prop_name] = prop.default
                    continue

                if not prop.type_:
                    raise RuntimeError(f"Failed to find type for {prop_name} in {ref}")
                return_dict[prop_name] = default_swagger_value_from_type_name(prop.type_)

        return return_dict


class SwaggerParser:
    _swagger_json: dict

    def __init__(self, swagger_doc_url: str) -> None:
        # Try to get the swagger.json from the server
        try:
            response = requests.get(swagger_doc_url)
            response.raise_for_status()
            self._swagger_json = response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Failed to get swagger.json from server: {e.response.text}") from e

    def get_swagger_doc(self) -> SwaggerDoc:
        return SwaggerDoc.model_validate(self._swagger_json)

    def get_all_examples(self) -> dict[str, dict[str, object]]:
        return {}


_SWAGGER_TYPE_TO_PYTHON_TYPE = {
    "integer": int,
    "number": float,
    "string": str,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def resolve_swagger_type_name(type_name: str) -> type:
    """Resolve a swagger type name to a python type."""
    return _SWAGGER_TYPE_TO_PYTHON_TYPE[type_name]


def default_swagger_value_from_type_name(type_name: str) -> object:
    return resolve_swagger_type_name(type_name)()
