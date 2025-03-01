from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
    HordeResponseTypes,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class FilterDetails(HordeResponseBaseModel):
    """Details about a filter.

    Represents the data returned from the /v2/filters endpoint with http status code 200.

    v2 API Model: `FilterDetails`
    """

    description: str | None = Field(default=None, description="Description about this regex.")
    """The description of this filter."""
    filter_type: int = Field(examples=[10], ge=10, le=29)
    """The type of this filter."""
    id_: str = Field(alias="id")
    """The UUID of this filter."""
    regex: str = Field(examples=["ac.*"])
    """The regex for this filter."""
    replacement: str | None = Field(default="")
    """The replacement string for this regex."""
    user: str
    """The moderator which added or last updated this regex."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FilterDetails"


@Unhashable
@Unequatable
class FiltersListResponse(HordeResponseRootModel[list[FilterDetails]]):
    """A list of filters.

    Represents the data returned from the /v2/filters endpoint with http status code 200.

    v2 API Model: `FiltersList`
    """

    root: list[FilterDetails]
    """The underlying list of filters."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FiltersList"


class FiltersListRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to get a list of filters, with optional filtering.

    Represents a GET request to the /v2/filters endpoint.
    """

    filter_type: int | None = Field(
        default=None,
        description="The type of filter to return. If not specified, all filters are returned.",
        examples=[10],
        ge=10,
        le=29,
    )

    contains: str | None = Field(
        default=None,
        description="A string to search for in the filter description.",
        examples=["cat"],
    )

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FiltersListResponse]:
        return FiltersListResponse

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["filter_type", "contains"]

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


@Unhashable
@Unequatable
class FilterPromptSuspicionResponse(HordeResponseBaseModel):
    """The degree of suspicion for a prompt and the sections of the prompt that matched the filter.

    Represents the data returned from the /v2/filters endpoint with http status code 200.

    v2 API Model: `FilterPromptSuspicion`
    """

    matches: list[str] | None = None
    """The sections of the prompt that matched the filter."""

    suspicion: int
    """Rates how suspicious the provided prompt is. A suspicion over 2 means it would be blocked."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FilterPromptSuspicion"


class FilterPromptSuspicionRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to check a prompt for suspicion and return the sections that matched the filter.

    Represents a POST request to the /v2/filters endpoint.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    prompt: str = Field(description="The prompt to check for suspicion.", examples=["cat"])
    filter_type: int = Field(
        description="The type of filter to use. If not specified, all filters are used.",
        examples=[10],
        ge=10,
        le=29,
    )

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FilterPromptSuspicionResponse]:
        return FilterPromptSuspicionResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class PutNewFilterRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Create a new filter.

    Represents a PUT request to the /v2/filters endpoint.

    v2 API Model: `PutNewFilter`
    """

    description: str = Field(default="")
    """The description of the filter."""
    filter_type: int = Field(examples=[10], ge=10, le=29)
    """The type of filter to add."""
    regex: str = Field(examples=["ac.*"])
    """The regex for this filter."""
    replacement: str | None = Field(default="")
    """The replacement string for this regex."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PutNewFilter"

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PUT

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FilterDetails]:
        return FilterDetails

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponseTypes]]:
        return {
            HTTPStatusCode.CREATED: FilterDetails,
        }

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class FilterRegex(HordeAPIObjectBaseModel):
    """Details about a filter, including the regex and its type.

    v2 API Model: `FilterRegex`
    """

    filter_type: int = Field(examples=[10], ge=10, le=29)
    """The type of filter."""
    regex: str = Field(examples=["ac.*"])
    """The regex for this filter."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FilterRegex"


@Unhashable
@Unequatable
class FilterRegexResponse(HordeResponseRootModel[list[FilterRegex]]):
    """A list of filters.

    Represents the data returned from the /v2/filters/regex endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    root: list[FilterRegex]
    """The underlying list of filters."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class FilterRegexRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to get a list of regex filters.

    Represents a GET request to the /v2/filters/regex endpoint.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters_regex

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FilterRegexResponse]:
        return FilterRegexResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class SingleFilterRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request details about a single filter.

    Represents a GET request to the /v2/filters/{filter_id} endpoint.
    """

    filter_id: str
    """The ID of the filter to retrieve."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters_regex_single

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FilterDetails]:
        return FilterDetails

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["filter_id"]

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteFilterResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    """Response to deleting a filter, with a message.

    Represents the data returned from the /v2/filters/{filter_id} endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class DeleteFilterRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to delete a filter by its filter_id.

    Represents a DELETE request to the /v2/filters/{filter_id} endpoint.
    """

    filter_id: str
    """The ID of the filter to delete."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters_regex_single

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteFilterResponse]:
        return DeleteFilterResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class PatchExistingFilter(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Update an existing filter by its filter_id.

    Represents a PATCH request to the /v2/filters/{filter_id} endpoint.

    v2 API Model: `PatchExistingFilter`
    """

    description: str | None = Field(default=None)
    """The description of the filter."""
    regex: str | None = Field(default=None)
    """The regex for this filter."""
    replacement: str | None = Field(default=None)
    """The replacement string for this regex."""
    filter_type: int | None = Field(examples=[10], ge=10, le=29)
    """The type of filter to add."""

    filter_id: str
    """The ID of the filter to update."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PatchExistingFilter"

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_filters_regex_single

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FilterDetails]:
        return FilterDetails

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
