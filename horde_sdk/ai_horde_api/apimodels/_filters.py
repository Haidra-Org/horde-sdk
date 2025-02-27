from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)


class FilterDetails(HordeResponseBaseModel):
    description: str | None = Field(default=None, description="Description about this regex.")
    """The description of this filter."""
    filter_type: int = Field(examples=[10], ge=10, le=29)
    """The type of this filter."""
    id_: str
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


class FiltersListResponse(HordeResponseRootModel[list[FilterDetails]]):
    """Response model for the filters endpoint."""

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
    """Request model for the filters endpoint."""

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


class FilterPromptSuspicionResponse(HordeResponseBaseModel):
    """Response model for the filter prompt suspicion endpoint."""

    matches: list[str] | None = None
    """The sections of the prompt that matched the filter."""

    suspicion: str
    """Rates how suspicious the provided prompt is. A suspicion over 2 means it would be blocked."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FilterPromptSuspicion"


class FilterPromptSuspicionRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request model for the filter prompt suspicion endpoint."""

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
    """Request model for the put new filter endpoint."""

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
    def is_api_key_required(cls) -> bool:
        return True


class FilterRegex(HordeAPIObjectBaseModel):
    filter_type: int = Field(examples=[10], ge=10, le=29)
    """The type of filter."""
    regex: str = Field(examples=["ac.*"])
    """The regex for this filter."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "FilterRegex"


class FilterRegexResponse(HordeResponseRootModel[list[FilterRegex]]):
    """Response model for the filter regex endpoint."""

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
    """Request model for the filter regex endpoint."""

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
    """Request model for the single filter endpoint."""

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
    """Response model for the delete filter endpoint."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class DeleteFilterRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request model for the delete filter endpoint."""

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
    """Request model for the patch existing filter endpoint."""

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
