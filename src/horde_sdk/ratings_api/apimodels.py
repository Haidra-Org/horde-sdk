"""Model definitions for AI Horde Ratings API."""
import uuid
from enum import auto

from pydantic import BaseModel, Field
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.consts import _UNDEFINED_MODEL, HTTPMethod
from horde_sdk.generic_api import BaseRequestAuthenticated, BaseRequestUserSpecific
from horde_sdk.generic_api.apimodels import BaseRequest, BaseResponse
from horde_sdk.ratings_api.endpoints import RATING_API_BASE_URL, Rating_API_URL_Literals


class BaseRatingsAPIRequest(BaseRequest):
    @override
    @classmethod
    def get_api_url(cls) -> str:
        return RATING_API_BASE_URL


# region Responses
class BaseImageRatingRecord(BaseModel):
    """The information about any image rating result."""

    model_config = {"frozen": True}

    image: str
    """The URL to the image."""
    rating: int
    """The aesthetic rating the user gave."""
    artifacts: int | None
    """The quality ('artifact') rating the user gave."""
    average: float
    """The average rating that all users have given this image."""
    times_rated: int
    """The number of total ratings this image has received."""


class ImageRatingResponseSubRecord(BaseModel):
    """A single sub-record in a response from the `/v1/image/ratings` endpoint."""

    model_config = {"frozen": True}

    username: str
    rating: int
    artifacts: int | None


class ImageRatingsResponse(BaseResponse):
    """The representation of the full response from `/v1/image/ratings`."""

    model_config = {"frozen": True}

    total: int
    image: str
    image_id: uuid.UUID
    average: float
    times_rated: int
    ratings: list[ImageRatingResponseSubRecord]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _UNDEFINED_MODEL


class UserRatingsResponseSubRecord(BaseImageRatingRecord):
    """A single sub-record in a response from the `/v1/user/ratings` endpoint."""

    username: str
    """The name of the user in format `name#1234`."""


class UserRatingsResponse(BaseResponse):
    """The representation of the full response from `/v1/user/ratings`."""

    model_config = {"frozen": True}

    total: int
    """The total number of records in this response."""
    ratings: list[UserRatingsResponseSubRecord]
    """A `list` of all records returned."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _UNDEFINED_MODEL


class UserValidateResponseRecord(BaseImageRatingRecord):
    """A single sub-record in a response from the `/v1/validate/{user_id}` endpoint."""


class UserValidateResponse(BaseResponse):
    """The representation of the full response from `/v1/validate/{user_id}`."""

    model_config = {"frozen": True}

    total: int
    """The total number of records in this response."""
    ratings: list[UserValidateResponseRecord]
    """A `list` of all records returned."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _UNDEFINED_MODEL


class UserCheckResponse(BaseResponse):
    """A single record from the `/v1/user/check/` endpoint."""

    model_config = {"frozen": True}
    ratings_in_timeframe: int
    """The number of ratings this user submitted in the timeframe."""
    ratings_per_minute_in_timeframe: float
    """The average number of ratings per minute."""
    ratings_past_three_hours: int
    """The average number of ratings in the three hours prior to the request."""
    ratings_per_minute_for_past_three_hours: float
    """The average number of ratings per minute in the three hours prior to the request."""
    suspect_divergences: int
    """The number of instances of this user's rating not being within the criteria."""
    captchas_failed: int
    """The number of captchas failed by this user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _UNDEFINED_MODEL


# endregion

# region Requests


class BaseRequestImageSpecific(BaseModel):
    """Represents the minimum for any request specifying a specific user to the API."""

    image_id: uuid.UUID
    """The UUID of the image."""


class SelectableReturnFormats(StrEnum):
    """Formats the API supports returning data."""

    html = auto()
    json = auto()


class BaseSelectableReturnTypeRequest(BaseModel):
    """Mix-in class to describe an endpoint for which you can select the return data format."""

    format: SelectableReturnFormats  # noqa: A003
    """The format to request the response payload in, typically json."""


class ImageRatingsRequest(BaseRatingsAPIRequest, BaseRequestAuthenticated, BaseSelectableReturnTypeRequest):
    """Represents the data needed to make a request to the `/v1/image/ratings/{image_id}` endpoint."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return Rating_API_URL_Literals.v1_image_ratings

    @override
    @staticmethod
    def get_expected_response_type() -> type[ImageRatingsResponse]:
        return ImageRatingsResponse


class ImageRatingsComparisonTypes(StrEnum):
    """Ways the API supports selecting a rating range."""

    greater_than_equal = "ge"
    less_than_equal = "le"
    equal = "eq"


class ImageRatingsFilterableRequestBase(BaseSelectableReturnTypeRequest):
    """Generically, data the API requires to filter results prior and how to return them."""

    rating: int | None
    """The target rating, which will be compared by `rating_comparison`."""
    rating_comparison: ImageRatingsComparisonTypes | None
    """The way the `rating` will be compared. See `ImageRatingsComparisonTypes`."""
    artifacts: int | None = None
    """The target artifact rating, which will be compared by `artifacts_comparison`."""
    artifacts_comparison: ImageRatingsComparisonTypes | None = None
    """The way the `artifacts` will be compared. See `ImageRatingsComparisonTypes`."""
    min_ratings: int | None


class UserValidateRequest(BaseRatingsAPIRequest, BaseRequestUserSpecific, ImageRatingsFilterableRequestBase):
    """Represents the data needed to make a request to the `/v1/user/validate/{user_id}` endpoint."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return Rating_API_URL_Literals.v1_user_validate

    @override
    @staticmethod
    def get_expected_response_type() -> type[UserValidateResponse]:
        return UserValidateResponse


class UserCheckRequest(BaseRatingsAPIRequest, BaseRequestUserSpecific, BaseRequestAuthenticated):
    """Represents the data needed to make a request to the `/v1/user/check/` endpoint."""

    minutes: int = Field(ge=1)
    divergence: int = Field(ge=0)

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return Rating_API_URL_Literals.v1_user_check

    @override
    @staticmethod
    def get_expected_response_type() -> type[UserCheckResponse]:
        return UserCheckResponse


class UserRatingsRequest(BaseRatingsAPIRequest, BaseRequestAuthenticated, ImageRatingsFilterableRequestBase):
    """Represents the data needed to make a request to the `/v1/user/ratings/` endpoint."""

    limit: int
    offset: int = 0
    diverge: int | None
    client_agent: str | None

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return Rating_API_URL_Literals.v1_user_ratings

    @override
    @staticmethod
    def get_expected_response_type() -> type[UserRatingsResponse]:
        return UserRatingsResponse


# endregion
