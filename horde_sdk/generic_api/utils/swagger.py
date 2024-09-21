"""Utilities for parsing a swagger doc."""

from __future__ import annotations

import json
import re
from abc import ABC
from pathlib import Path
from typing import Any, ClassVar

import requests
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, model_validator
from strenum import StrEnum

from horde_sdk.consts import PAYLOAD_HTTP_METHODS, HTTPMethod, HTTPStatusCode, is_error_status_code


class SwaggerModelAdditionalProperty(BaseModel):
    """An additional property of a model (data structure) used in the API."""

    # TODO: Is this actually a recursive SwaggerModelDefinitionProperty?
    model_config = {"extra": "forbid"}

    type_: str | None = Field(default=None, alias="type")
    description: str | None = None


class SwaggerModelProperty(BaseModel):
    """A property of a model (data structure) used in the API.

    This might also be referred to as a "field" or an "attribute" of the model.

    See https://swagger.io/docs/specification/data-models/data-types/#objects
    """

    model_config = {"extra": "forbid"}

    type_: str | None = Field(default=None, alias="type")
    description: str | None = None
    title: str | None = None
    default: object | None = None
    example: object | None = None
    format_: str | None = Field(default=None, alias="format")
    enum: list[str] | None = None
    ref: str | None = Field(default=None, alias="$ref")
    minimum: float | None = None
    maximum: float | None = None
    minLength: int | None = None
    maxLength: int | None = None
    multipleOf: float | None = None
    uniqueItems: bool | None = None
    additionalProperties: SwaggerModelAdditionalProperty | None = None
    items: SwaggerModelProperty | list[SwaggerModelProperty] | None = None


class SwaggerModelRef(BaseModel):
    """A reference to a model (data structure) used in the API."""

    model_config = {"extra": "forbid"}

    ref: str | None = Field(default=None, alias="$ref")


class SwaggerModelEntry(BaseModel, ABC):
    """An entry in the definitions section of the swagger doc.

    This could be a model definition, or a schema validation method object.
    See `SwaggerModelDefinitionSchemaValidationMethods` for more info.
    """


class SwaggerModelDefinition(SwaggerModelEntry):
    """A definition of a model (data structure) used in the API."""

    model_config: ClassVar[ConfigDict] = {"extra": "forbid"}

    type_: str | None = Field(default=None, alias="type")
    properties: dict[str, SwaggerModelProperty] | None = None
    required: list[str] | None = None


class SwaggerSchemaValidationMethod(StrEnum):
    """The type of schema validation method used in the Swagger doc."""

    allOf = "allOf"
    """The model must match all of the schemas in this list."""
    oneOf = "oneOf"
    """The model must match exactly one of the schemas in this list."""
    anyOf = "anyOf"
    """The model must match at least one of the schemas in this list."""


class SwaggerModelDefinitionSchemaValidation(SwaggerModelEntry):
    """When used instead of a SwaggerModelDefinition, it means that the model is validated against one or more schemas.

    See the `allOf`, `oneOf`, and `anyOf` properties of the Swagger spec:
    https://swagger.io/docs/specification/data-models/oneof-anyof-allof-not/
    """

    model_config: ClassVar[ConfigDict] = {"extra": "forbid"}

    allOf: list[SwaggerModelDefinition | SwaggerModelRef] | None = None
    """The model must match all of the schemas in this list."""
    oneOf: list[SwaggerModelDefinition | SwaggerModelRef] | None = None
    """The model must match exactly one of the schemas in this list."""
    anyOf: list[SwaggerModelDefinition | SwaggerModelRef] | None = None
    """The model must match at least one of the schemas in this list."""

    @model_validator(mode="before")
    def one_method_specified(cls, v: dict[Any, Any]) -> dict[Any, Any]:
        """Ensure at least one of the validation methods is specified."""
        if not any([v.get("allOf"), v.get("oneOf"), v.get("anyOf")]):
            raise ValueError("At least one of allOf, oneOf, or anyOf must be specified.")

        return v

    def get_validation_method(self) -> SwaggerSchemaValidationMethod | None:
        """Get the schema validation method used for this model."""
        if self.allOf:
            return SwaggerSchemaValidationMethod.allOf
        if self.oneOf:
            return SwaggerSchemaValidationMethod.oneOf
        if self.anyOf:
            return SwaggerSchemaValidationMethod.anyOf

        raise RuntimeError("No validation method defined!")

    def get_model_definitions(
        self,
    ) -> tuple[SwaggerSchemaValidationMethod, list[SwaggerModelDefinition | SwaggerModelRef]]:
        """Get the model definitions used for this model."""
        if self.allOf:
            return (SwaggerSchemaValidationMethod.allOf, self.allOf)
        if self.oneOf:
            return (SwaggerSchemaValidationMethod.oneOf, self.oneOf)
        if self.anyOf:
            return (SwaggerSchemaValidationMethod.anyOf, self.anyOf)

        raise RuntimeError("No validation method specified!")


class SwaggerDocTagsItem(BaseModel):
    """A description of a tag in the swagger doc."""

    model_config = {"extra": "forbid"}

    name: str | None = None
    description: str | None = None


class SwaggerDocResponseItem(BaseModel):
    """A description of a response in the swagger doc."""

    model_config = {"extra": "forbid"}

    description: str | None = None


class SwaggerDocInfo(BaseModel):
    """The info section of the swagger doc."""

    model_config = {"extra": "forbid"}

    title: str | None = None
    version: str | None = None
    description: str | None = None


class SwaggerEndpointMethodParameterSchemaRef(BaseModel):
    """A schema definition of an endpoint method parameter that is a reference to another model."""

    model_config = {"extra": "forbid"}
    ref: str | None = Field(alias="$ref")


class SwaggerEndpointMethodParameterSchemaProperty(BaseModel):
    """A property definition of an endpoint method parameter schema."""

    model_config = {"extra": "forbid"}

    type_: str | None = Field(default=None, alias="type")
    format_: str | None = Field(default=None, alias="format")


class SwaggerEndpointMethodParameterSchema(BaseModel):
    """A schema definition of an endpoint method parameter."""

    model_config = {"extra": "forbid"}

    type_: str | None = Field(default=None, alias="type")
    properties: dict[str, SwaggerEndpointMethodParameterSchemaProperty] | None = None


class SwaggerEndpointMethodParameter(BaseModel):
    """A parameter definition of an endpoint method."""

    model_config = {"extra": "forbid"}

    name: str | None = None
    in_: str = Field("", alias="in")
    description: str | None = None
    required: bool | None = None
    schema_: SwaggerEndpointMethodParameterSchema | SwaggerEndpointMethodParameterSchemaRef | None = Field(
        default=None,
        alias="schema",
    )
    default: object | None = None
    type_: str | None = Field(default=None, alias="type")
    format_: str | None = Field(default=None, alias="format")


class SwaggerEndpointResponseSchemaItem(BaseModel):
    """A response item definition pointing to a schema ("$ref")."""

    # model_config = {"extra": "forbid"}

    ref: str | None = Field(default=None, alias="$ref")


class SwaggerEndpointResponseSchema(BaseModel):
    """A response schema definition of an endpoint."""

    # model_config = {"extra": "forbid"}

    ref: str | None = Field(default=None, alias="$ref")
    type_: str | None = Field(default=None, alias="type")
    items: SwaggerEndpointResponseSchemaItem | None = None


class SwaggerEndpointResponse(BaseModel):
    """A response definition of an endpoint."""

    model_config = {"extra": "forbid"}

    description: str
    schema_: SwaggerEndpointResponseSchema | None = Field(default=None, alias="schema")


class SwaggerEndpointMethod(BaseModel):
    """A method definition of an endpoint."""

    model_config = {"extra": "forbid"}

    summary: str | None = None
    description: str | None = None
    operation_id: str | None = Field(default=None, alias="operationId")
    parameters: list[SwaggerEndpointMethodParameter] | None = None
    responses: dict[str, SwaggerEndpointResponse] | None = None
    tags: list[str] | None = None


class SwaggerEndpointParameter(BaseModel):
    """A parameter definition of an endpoint."""

    model_config = {"extra": "forbid"}

    name: str | None = None
    in_: str = Field("", alias="in")
    description: str | None = None
    required: bool | None = None
    type_: str | None = Field(default=None, alias="type")


class SwaggerEndpoint(BaseModel):
    """An endpoint definition of the API."""

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

    def _remove_ref_syntax(self, ref: str) -> str:
        """Remove the reference syntax from a ref string.

        Args:
            ref: The reference string to remove the syntax from.

        Returns:
            A string representing the reference without the syntax.
        """
        if not ref.startswith("#/definitions/"):
            raise ValueError("Reference must start with '#/definitions/'")
        return ref[len("#/definitions/") :]

    def get_defined_endpoints(self) -> dict[str, SwaggerEndpointMethod]:
        """Get the endpoints that are specified in the swagger doc."""
        return_dict = {}
        for http_method, endpoint_method in self.__dict__.items():
            if isinstance(endpoint_method, SwaggerEndpointMethod):
                return_dict[http_method] = endpoint_method
        return return_dict

    def get_all_request_models(self) -> list[str]:
        """Get all the request models for the endpoint."""
        request_models = []
        for _http_method, endpoint_method in self.get_defined_endpoints().items():
            if endpoint_method.parameters:
                for param in endpoint_method.parameters:
                    if (
                        param.schema_
                        and isinstance(param.schema_, SwaggerEndpointMethodParameterSchemaRef)
                        and param.schema_.ref is not None
                    ):
                        request_models.append(self._remove_ref_syntax(param.schema_.ref))
        return request_models

    def get_all_response_models(self) -> list[str]:
        """Get all the response models for the endpoint."""
        response_models = []
        for _http_method, endpoint_method in self.get_defined_endpoints().items():
            if endpoint_method.responses:
                for _status_code, response in endpoint_method.responses.items():
                    if response.schema_ and response.schema_.ref:
                        response_models.append(self._remove_ref_syntax(response.schema_.ref))
        return response_models

    @model_validator(mode="before")
    def at_least_one_method_specified(cls, v: dict[Any, Any]) -> dict[Any, Any]:
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
            ],
        ):
            raise ValueError("At least one method must be specified.")

        return v


class SwaggerDoc(BaseModel):
    """The swagger doc for an API, represented as an object."""

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
    definitions: dict[str, SwaggerModelDefinition | SwaggerModelDefinitionSchemaValidation]
    """The definitions of the models (data structures) used in the API."""

    def get_all_response_examples(
        self,
    ) -> dict[str, dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list[Any]]]]:
        """Extract all response examples from the swagger doc.

        This in the form of:
        `dict[endpoint_path, dict[http_method, dict[http_status_code, example_response]]]`
        """
        # Create an empty dictionary to hold all endpoint examples.
        every_endpoint_example: dict[str, dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list[Any]]]] = {}

        # Iterate through each endpoint in the Swagger documentation.
        for endpoint_path, endpoint in self.paths.items():
            # Skip the "/v2/stats/img/models" endpoint.
            if endpoint_path == "/v2/stats/img/models":
                pass

            # Get the response examples for this endpoint.
            endpoint_examples = self.get_endpoint_examples(endpoint)

            # If there are any response examples for this endpoint, add them to the dictionary of all endpoint examples
            if endpoint_examples:
                every_endpoint_example[endpoint_path] = endpoint_examples

        # Return the dictionary of all endpoint examples.
        return every_endpoint_example

    def get_endpoint_examples(
        self,
        endpoint: SwaggerEndpoint,
    ) -> dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list[Any]]]:
        """Extract response examples for a single endpoint.

        Args:
            endpoint: The SwaggerEndpoint object to extract response examples from.

        Returns:
            A dictionary of response examples for the endpoint in the form of:
            `dict[http_method, dict[http_status_code, example_response]]`
        """
        # Create an empty dictionary to hold the response examples for each HTTP method used by the endpoint.
        endpoint_examples: dict[HTTPMethod, dict[HTTPStatusCode, dict[str, object] | list[Any]]] = {}

        # Iterate through each HTTP method used by the endpoint.
        for http_method_name, endpoint_method_definition in endpoint.get_defined_endpoints().items():
            # Get the response examples for this HTTP method.
            endpoint_method_examples = self.get_endpoint_method_examples(endpoint_method_definition)

            # If there are any response examples for this HTTP method, add them to the dictionary of endpoint examples.
            if endpoint_method_examples:
                endpoint_examples[HTTPMethod(http_method_name.upper())] = endpoint_method_examples

        # Return the dictionary of response examples for the endpoint.
        return endpoint_examples

    def get_endpoint_method_examples(
        self,
        endpoint_method_definition: SwaggerEndpointMethod,
    ) -> dict[HTTPStatusCode, dict[str, object] | list[Any]]:
        """Extract response examples for a single HTTP method used by an endpoint.

        Args:
            endpoint_method_definition: The SwaggerEndpointMethod object to extract response examples from.

        Returns:
            A dictionary of response examples for the HTTP method in the form of:
            `dict[http_status_code, example_response]`
        """
        # Create an empty dictionary to hold the response examples for each HTTP status code used by the HTTP method.
        endpoint_method_examples: dict[HTTPStatusCode, dict[str, object] | list[Any]] = {}

        # If there are no defined responses for the HTTP method, return the empty dictionary of response examples.
        if not endpoint_method_definition.responses:
            return endpoint_method_examples

        # Iterate through each defined response for the HTTP method.
        for http_status_code_str, response_definition in endpoint_method_definition.responses.items():
            # Convert the HTTP status code string to an HTTPStatusCode object.
            http_status_code_object = HTTPStatusCode(int(http_status_code_str))

            # Get the response example for this HTTP status code.
            example_response = self.get_response_example(response_definition)

            # If there is a response example for this HTTP status code, add it to the dictionary of endpoint method
            # examples.
            if example_response:
                endpoint_method_examples[http_status_code_object] = example_response

        # Return the dictionary of response examples for the HTTP method.
        return endpoint_method_examples

    def get_response_example(self, response_definition: SwaggerEndpointResponse) -> dict[str, object] | list[Any]:
        """Extract an example response for a single HTTP response definition.

        Args:
            response_definition: The SwaggerEndpointResponse object to extract an example response from.

        Returns:
            A dictionary or list representing an example response for the HTTP response definition.
        """
        # Create an empty dictionary or list to hold the example response.
        example_response: dict[str, object] | list[Any] = {}

        # If there is no response schema, return the empty dictionary or list of example response.
        if not response_definition.schema_:
            return example_response

        # If the response schema is a reference to an API model, resolve the reference and include its defaults too.
        if isinstance(response_definition.schema_, SwaggerEndpointResponseSchema) and response_definition.schema_.ref:
            example_response = self._resolve_model_ref_defaults(response_definition.schema_.ref)

        # If the response schema is an array, get the example response for the array items and return it as a list.
        if response_definition.schema_.items:
            example_response = self._resolve_model_ref_defaults(response_definition.schema_.items.ref)
            if response_definition.schema_.type_ == "array":
                example_response = [example_response]

        # If the response schema is an object, return the example response as a dictionary with a "properties" key.
        elif response_definition.schema_.type_ == "object":
            example_response = {"properties": example_response}

        # Return the dictionary or list representing the example response for the HTTP response definition.
        return example_response

    def get_all_payload_examples(self) -> dict[str, dict[HTTPMethod, dict[str, object]]]:
        """Extract all examples from the swagger doc.

        This in the form of:
        `dict[endpoint_path, dict[param_name, param_example_value]]]`
        """
        # Create an empty dictionary to hold all endpoint examples.
        every_endpoint_example: dict[str, dict[HTTPMethod, dict[str, object]]] = {}

        # Loop through each endpoint in the Swagger doc.
        for endpoint_path, endpoint in self.paths.items():
            # Create an empty dictionary to hold the examples for this endpoint.
            endpoint_examples: dict[HTTPMethod, dict[str, object]] = {}

            # Skip the "/v2/generate/async" endpoint.
            if endpoint_path == "/v2/generate/async":
                pass

            # Loop through each HTTP method defined for this endpoint.
            for http_method_name, endpoint_method_definition in endpoint.get_defined_endpoints().items():
                # Skip HTTP methods that do not have a payload.
                if http_method_name.upper() not in PAYLOAD_HTTP_METHODS:
                    continue

                # Skip HTTP methods that do not have any parameters.
                if not endpoint_method_definition.parameters:
                    continue

                # Get the payload definition for this HTTP method.
                _payload_definitions = [d for d in endpoint_method_definition.parameters if d.name == "payload"]
                if len(_payload_definitions) != 1:
                    raise RuntimeError(
                        f"Expected to find exactly one payload definition for {endpoint_path} {http_method_name}",
                    )
                payload_definition = _payload_definitions[0]

                # Check that the payload definition has a schema.
                if not payload_definition.schema_:
                    raise RuntimeError(
                        f"Expected to find a schema for {endpoint_path} {http_method_name} payload definition",
                    )

                # If the payload definition is a reference to another model, resolve the reference and use its defaults
                # as the example payload.
                if isinstance(payload_definition.schema_, SwaggerEndpointMethodParameterSchemaRef):
                    example_payload = self._resolve_model_ref_defaults(payload_definition.schema_.ref)
                    if isinstance(example_payload, list):
                        raise RuntimeError(
                            f"Expected to find a dict for {endpoint_path} {http_method_name} payload definition",
                        )
                    endpoint_examples.update(
                        {HTTPMethod(http_method_name.upper()): example_payload},
                    )

                # If the payload definition is a direct schema, create an example payload using the schema's
                # properties and types.
                elif isinstance(payload_definition.schema_, SwaggerEndpointMethodParameterSchema):
                    if not payload_definition.schema_.properties:
                        continue
                    if not payload_definition.required:
                        continue
                    endpoint_specific_schema = {}
                    for prop_name, prop in payload_definition.schema_.properties.items():
                        if not prop.type_:
                            raise RuntimeError(
                                f"Expected to find a type for {endpoint_path} {http_method_name} payload definition",
                            )
                        endpoint_specific_schema[prop_name] = default_swagger_value_from_type_name(prop.type_)
                    endpoint_examples.update(
                        {HTTPMethod(http_method_name.upper()): endpoint_specific_schema},
                    )

            # If there are any examples for this endpoint, add them to the dictionary of all endpoint examples.
            if endpoint_examples:
                every_endpoint_example[endpoint_path] = endpoint_examples

        # Return the dictionary of all endpoint examples.
        return every_endpoint_example

    @staticmethod
    def filename_from_endpoint_path(
        endpoint_path: str,
        http_method: HTTPMethod,
        *,
        http_status_code: HTTPStatusCode | None = None,
    ) -> str:
        """Get the filename for the given endpoint path.

        Args:
            endpoint_path: The path of the endpoint.
            http_method: The HTTP method used by the endpoint.
            http_status_code: The HTTP status code of the response (optional).

        Returns:
            A string representing the filename for the given endpoint path.
        """
        # Replace any non-alphanumeric characters in the endpoint path with underscores.
        endpoint_path = re.sub(r"\W+", "_", endpoint_path)

        # Append the HTTP method to the endpoint path, separated by an underscore.
        endpoint_path = endpoint_path + "_" + http_method.value.lower()

        # If an HTTP status code is provided, append it to the endpoint path, separated by an underscore.
        if http_status_code:
            endpoint_path = endpoint_path + "_" + str(http_status_code.value)

        # Replace any consecutive underscores with a single underscore.
        return re.sub(r"__+", "_", endpoint_path)

    def write_all_payload_examples_to_file(self, directory: str | Path) -> bool:
        """Write all example payloads to a file in the test_data directory.

        Args:
            directory: The directory to write the files to.

        Returns:
            A boolean indicating whether the operation succeeded.
        """
        # Convert the directory path to a Path object.
        directory = Path(directory)

        # Get all payload examples for all endpoints.
        all_examples = self.get_all_payload_examples()

        # Iterate through each endpoint and its associated HTTP methods and example payloads.
        for endpoint_path, endpoint_examples_info in all_examples.items():
            for http_method, example_payload in endpoint_examples_info.items():
                # Generate a filename for the example payload based on the endpoint path and HTTP method.
                filename = self.filename_from_endpoint_path(endpoint_path, http_method)

                # If an HTTP status code is provided, append it to the filename.
                if isinstance(example_payload, dict) and "status_code" in example_payload:
                    filename = filename + "_" + str(example_payload["status_code"])

                # Create a filepath for the example payload based on the directory and filename.
                filepath = directory / f"{filename}.json"

                # Write the example payload to the filepath as a JSON file.
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(json.dumps(example_payload, indent=4) + "\n")

        # Return True to indicate that the operation succeeded.
        return True

    def write_all_response_examples_to_file(
        self,
        directory: str | Path,
        *,
        error_responses: bool = False,
    ) -> bool:
        """Write all example responses to a file in the test_data directory.

        Args:
            directory: The directory to write the files to.
            error_responses: Whether to include error responses. Defaults to False.

        Returns:
            A boolean indicating whether the operation succeeded.
        """
        # Convert the directory path to a Path object.
        directory = Path(directory)

        # Get all response examples for all endpoints.
        all_examples = self.get_all_response_examples()

        # Iterate through each endpoint and its associated HTTP methods and example responses.
        for endpoint_path, endpoint_examples_info in all_examples.items():
            for http_method, http_status_code_examples in endpoint_examples_info.items():
                for http_status_code, example_response in http_status_code_examples.items():
                    # If error responses are not included and this is an error status code, skip this example.
                    if not error_responses and is_error_status_code(http_status_code.value):
                        continue

                    # Generate a filename for the example response based on the endpoint path, HTTP method, and
                    # status code.
                    filename = self.filename_from_endpoint_path(
                        endpoint_path,
                        http_method,
                        http_status_code=http_status_code,
                    )

                    # Create a filepath for the example response based on the directory and filename.
                    filepath = directory / f"{filename}.json"

                    # Write the example response to the filepath as a JSON file.
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(json.dumps(example_response, indent=4) + "\n")
        # Return True to indicate that the operation succeeded.
        return True

    def _resolve_model_ref_defaults(
        self,
        ref: str | None,
        *,
        _recursed_property_name: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """For ref entries, recursively resolve the default values for all properties.

        Note that this will combine all properties from all definitions that are referenced.
        This function is more useful when trying to determine the expected payload for a request
        or the expected response for a particular endpoint, rather than the schema for a particular model.
        """
        # example ref: "#/definitions/RequestError"

        if not ref:
            return {}

        # `return_list` has a special specifically for the "*" property, where the endpoint accepts or returns N
        # objects of the same type. In this case, three dummy entries are created in `return_list`, which are
        # recognized on recursion and ultimately returned as a dict.
        # This solution was implemented in response to the SinglePeriodImgModelStats model, see it for an example.
        return_dict: dict[str, Any] = {}
        return_list: list[dict[str, Any]] = []

        # Remove the "#/definitions/" prefix from the ref as it is fixed for all refs and not needed
        if ref.startswith("#/definitions/"):
            ref = ref[len("#/definitions/") :]

        if ref not in self.definitions:
            raise RuntimeError(f"Failed to find definition for {ref}")

        found_def_parent = self.definitions[ref]
        # logger.debug(f"Found definition for {ref}")

        validation_method: SwaggerSchemaValidationMethod | None = None
        all_defs: list[SwaggerModelDefinition | SwaggerModelRef] = []

        if isinstance(found_def_parent, SwaggerModelDefinitionSchemaValidation):
            validation_method, all_defs = found_def_parent.get_model_definitions()
        elif isinstance(found_def_parent, SwaggerModelDefinition):
            all_defs = [found_def_parent]
        else:
            raise RuntimeError(f"Unexpected definition type: {type(found_def_parent)}")

        for definition in all_defs:
            # If the definition is not a SwaggerModelRef, skip it
            if not isinstance(definition, SwaggerModelRef):
                continue

            # Recursively resolve the reference
            resolved_model = self._resolve_model_ref_defaults(definition.ref)

            # If the resolved model is a dictionary, update the return dictionary
            if isinstance(resolved_model, dict):
                if validation_method == SwaggerSchemaValidationMethod.allOf:
                    return_dict.update(resolved_model)
                elif (
                    validation_method == SwaggerSchemaValidationMethod.oneOf
                    or validation_method == SwaggerSchemaValidationMethod.anyOf
                ):
                    # Warn the user that oneOf and anyOf are not well supported
                    logger.warning(
                        (
                            "oneOf and anyOf are not well supported. You may experience unexpected behavior. "
                            f"ref: {definition.ref}"
                        ),
                    )
                    break

            # If the resolved model is a list, raise an error (this should not happen)
            elif isinstance(resolved_model, list):
                raise RuntimeError(f"Unexpected list type: {type(resolved_model)}")

        for definition in all_defs:
            # If the definition is not a SwaggerModelDefinition, skip it
            if not isinstance(definition, SwaggerModelDefinition):
                # If the definition is a SwaggerModelRef, continue to the next iteration
                if definition.ref:
                    continue
                # Otherwise, raise an error
                raise RuntimeError(f"Unexpected definition type: {type(definition)}")

            # If the definition has no properties, skip it
            if not definition.properties:
                continue

            # Iterate over each property in the definition
            for prop_name, prop in definition.properties.items():
                # If the property is a reference to another model, recursively resolve the reference
                if prop.ref:
                    resolved_model = self._resolve_model_ref_defaults(prop.ref)
                    # If the resolved model is a dictionary, add it to the return dictionary
                    if isinstance(resolved_model, dict):
                        return_dict.update({prop_name: resolved_model})
                    # If the resolved model is a list, add the first item to the return dictionary
                    elif isinstance(resolved_model, list):
                        return_dict.update({prop_name: resolved_model[0]})
                    continue

                # If the property is a wildcard property with additionalProperties, add default values for
                # three additional properties
                if prop_name == "*" and prop.additionalProperties:
                    assert prop.additionalProperties.type_
                    default = default_swagger_value_from_type_name(prop.additionalProperties.type_)
                    return_list.append(
                        {
                            "additionalProp1": default,
                            "additionalProp2": default,
                            "additionalProp3": default,
                        },
                    )
                    continue

                # If the property is an array, recursively resolve any references in the items property
                if prop.items:
                    items_as_list = [prop.items] if isinstance(prop.items, SwaggerModelProperty) else prop.items
                    sub_item_return_list: list[object] = []
                    for item in items_as_list:
                        if item.ref:
                            # This is were the recursion happens
                            resolved_model = self._resolve_model_ref_defaults(item.ref)
                            # If the resolved model is a dictionary, add it to the sub-item return list
                            if isinstance(resolved_model, dict):
                                sub_item_return_list.append(resolved_model)
                            # If the resolved model is a list, add the first item to the sub-item return list
                            elif isinstance(resolved_model, list):
                                sub_item_return_list.append(resolved_model[0])
                            continue

                        # Otherwise, get the default value for the item and add it to the sub-item return list
                        sub_item_return_list.append(self.get_default_with_constraint(item))

                    # Add the sub-item return list to the return dictionary
                    return_dict[prop_name] = sub_item_return_list
                    continue

                # Otherwise, get the default value for the property and add it to the return dictionary
                return_dict[prop_name] = self.get_default_with_constraint(prop)

        return return_dict if return_dict else return_list

    def get_default_with_constraint(self, model_property: SwaggerModelProperty) -> object:
        """Get the example value, defaulting to a a value appropriate to the type with any constraints applied."""
        # If the model property has a description that includes the word "optionally", do nothing
        if model_property.description and "optionally" in model_property.description:
            pass

        # If the model property has an example value, return it
        if model_property.example is not None:
            return model_property.example

        # If the model property has a default value, return it
        if model_property.default is not None:
            return model_property.default

        # If the model property is a number or integer type, check for minimum, maximum, and multipleOf properties and
        # return a constrained value based on it
        if model_property.type_ == "number" or model_property.type_ == "integer":
            if model_property.minimum is not None:
                return model_property.minimum
            if model_property.maximum is not None:
                return model_property.maximum
            if model_property.multipleOf is not None:
                return model_property.multipleOf

        # If the model property is a string type, check for enum, minLength, maxLength, and format properties and
        # return a constrained value based on it
        elif model_property.type_ == "string":
            if model_property.enum is not None:
                return model_property.enum[0]
            if model_property.minLength is not None:
                return "a" * model_property.minLength
            if model_property.maxLength is not None:
                return "a" * model_property.maxLength
            if model_property.format_ == "date-time":
                return "2021-01-01T00:00:00Z"

        # If the model property has a type property, return the default value for that type
        if model_property.type_ is not None:
            return default_swagger_value_from_type_name(model_property.type_)

        # If none of the above conditions are met, return None
        return None


class SwaggerParser:
    """Parse a swagger doc from a URL or a local file."""

    _swagger_json: dict[str, Any]

    def __init__(
        self,
        *,
        swagger_doc_url: str | None = None,
        swagger_doc_path: str | Path | None = None,
    ) -> None:
        """Parse a swagger doc from a URL or a local file.

        Args:
            swagger_doc_url (str | None, optional): The URL of the Swagger doc to parse. Defaults to None.
            swagger_doc_path (str | Path | None, optional): The path to the Swagger doc to parse. Defaults to None.

        Raises:
            RuntimeError: If the Swagger doc cannot be found or loaded.
        """
        # If a local Swagger doc path is provided, load the JSON from the file
        if swagger_doc_path:
            swagger_doc_path = Path(swagger_doc_path)
            if swagger_doc_path.exists():
                with open(swagger_doc_path, encoding="utf-8") as f:
                    self._swagger_json = json.load(f)
            else:
                raise RuntimeError(f"Failed to find swagger.json at {swagger_doc_path}")
        # If a Swagger doc URL is provided, get the JSON from the URL
        elif swagger_doc_url:
            try:
                response = requests.get(swagger_doc_url)
                response.raise_for_status()
                self._swagger_json = response.json()
            except requests.exceptions.HTTPError as e:
                raise RuntimeError(f"Failed to get swagger.json from server: {e.response}") from e

    def get_swagger_doc(self) -> SwaggerDoc:
        """Get the swagger doc as a SwaggerDoc object."""
        return SwaggerDoc.model_validate(self._swagger_json)

    def get_all_examples(self) -> dict[str, dict[str, object]]:
        """Get all examples from the swagger doc."""
        return {}  # TODO: Implement this


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
    """Get the default value for a given swagger type name."""
    return resolve_swagger_type_name(type_name)()
