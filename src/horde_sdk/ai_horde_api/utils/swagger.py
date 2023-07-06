from __future__ import annotations

import requests
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.consts import HTTPMethod
from pydantic import BaseModel, Field, model_validator

SWAGGER_DOC_URL = f"{AI_HORDE_BASE_URL}/swagger.json"


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


class SwaggerModelDefinition(BaseModel):
    """A definition of a model (data structure) used in the API."""

    model_config = {"extra": "forbid"}

    type_: str | None = Field(None, alias="type")
    properties: dict[str, SwaggerModelDefinitionProperty] | None = None
    required: list[str] | None = None


class SwaggerModelDefinitionSchemaValidationMethods(BaseModel):
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


class SwaggerEndpointMethodParameterSchemaItem(BaseModel):
    model_config = {"extra": "forbid"}
    ref: str | None = Field(None, alias="$ref")


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
    schema_: SwaggerEndpointMethodParameterSchema | SwaggerEndpointMethodParameterSchemaItem | None = Field(
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


class SwaggerParser:
    _swagger_json: dict

    def __init__(self) -> None:
        # Try to get the swagger.json from the server
        try:
            response = requests.get(SWAGGER_DOC_URL)
            response.raise_for_status()
            self._swagger_json = response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Failed to get swagger.json from server: {e.response.text}") from e

    def get_swagger_doc(self) -> SwaggerDoc:
        return SwaggerDoc.model_validate(self._swagger_json)
