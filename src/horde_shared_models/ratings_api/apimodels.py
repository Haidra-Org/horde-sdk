"""Model definitions for AI Horde Ratings API."""
import inspect
import sys
import uuid
from enum import Enum

import pydantic
import typing_extensions
from typing_extensions import override

from ..generic_api import BaseRequest, BaseRequestAuthenticated
from .endpoints import Rating_API_URL_Literals, URLWithPath

# region Requests


class BaseRequestUserSpecific(BaseRequestAuthenticated):
    """Represents the minimum for any request specifying a specific user to the API."""

    user_id: str
    """The user's ID, as a `str`, but only containing numeric values."""

    @pydantic.validator("user_id")
    def user_idNumeric(cls, value: str) -> str:
        """The API endpoint expects a string, but the only valid values would be numbers only."""
        try:
            int(value)
        except ValueError as valueError:
            raise ValueError(
                f"user_id must be a str, but only numeric values are allowed!\n  Value: {value}"
            ) from valueError
        return value


class BaseRequestImageSpecific(BaseRequestAuthenticated):
    """Represents the minimum for any request specifying a specific user to the API."""

    image_id: uuid.UUID
    """The UUID of the image."""


class SelectableReturnFormats(str, Enum):
    """Formats the API supports returning data."""

    html = "html"
    json = "json"


class BaseSelectableReturnTypeRequest(pydantic.BaseModel):
    """Mix-in class to describe an endpoint for which you can select the return data format."""

    format: SelectableReturnFormats  # noqa: A003
    """The format to request the response payload in, typically json."""


class ImageRatingsRequest(BaseRequestAuthenticated, BaseSelectableReturnTypeRequest):
    """Represents the data needed to make a request to the `/v1/image/ratings/{image_id}` endpoint."""

    @override
    @staticmethod
    def getEndpointURL() -> str:
        return URLWithPath(path=Rating_API_URL_Literals.v1_image_ratings)

    @override
    @staticmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
        return ImageRatingsResponse


class ImageRatingsComparisonTypes(str, Enum):
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


class UserValidateRequest(BaseRequestUserSpecific, ImageRatingsFilterableRequestBase):
    """Represents the data needed to make a request to the `/v1/user/validate/{user_id}` endpoint."""

    @override
    @staticmethod
    def getEndpointURL() -> str:
        return URLWithPath(path=Rating_API_URL_Literals.v1_user_validate)

    @override
    @staticmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
        return UserValidateResponse


class UserCheckRequest(BaseRequestUserSpecific):
    """Represents the data needed to make a request to the `/v1/user/check/` endpoint."""

    minutes: int
    divergence: int

    @pydantic.validator("minutes")
    def minutesIsPositive(cls, value: int) -> int:
        """Endpoint expects a positive integer."""
        if value <= 0:
            raise ValueError("minutes is required, and must be > 0!")
        return value

    @pydantic.validator("divergence")
    def divergenceIsNotNegative(cls, value: int) -> int:
        """Negative values are meaningless in this context."""
        if value < 0:
            raise ValueError("divergence must be >= 0!")
        return value

    @override
    @staticmethod
    def getEndpointURL() -> str:
        return URLWithPath(path=Rating_API_URL_Literals.v1_user_check)

    @override
    @staticmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
        return UserCheckResponse


class UserRatingsRequest(BaseRequestAuthenticated, ImageRatingsFilterableRequestBase):
    """Represents the data needed to make a request to the `/v1/user/ratings/` endpoint."""

    limit: int
    offset: int = 0
    diverge: int | None
    client_agent: str | None

    @override
    @staticmethod
    def getEndpointURL() -> str:
        return URLWithPath(path=Rating_API_URL_Literals.v1_user_ratings)

    @override
    @staticmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
        return UserRatingsResponse


# endregion


# region Responses
class BaseImageRatingRecord(pydantic.BaseModel):
    """The information about any image rating result."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    image: str
    """The URL to the image."""
    rating: int
    """The aesthetic rating the user gave."""
    artifacts: int | None
    """The quality ('artifact') rating the user gave."""
    average: int
    """The integer-rounded average rating that all users have given this image."""
    times_rated: int
    """The number of total ratings this image has received."""


class ImageRatingResponseSubRecord(pydantic.BaseModel):
    """A single sub-record in a response from the `/v1/image/ratings` endpoint."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    username: str
    rating: int
    artifacts: int | None


class ImageRatingsResponse(pydantic.BaseModel):
    """The representation of the full response from `/v1/image/ratings`."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    total: int
    image: str
    image_id: uuid.UUID
    average: float
    times_rated: int
    ratings: list[ImageRatingResponseSubRecord]


class UserRatingsResponseSubRecord(BaseImageRatingRecord):
    """A single sub-record in a response from the `/v1/user/ratings` endpoint."""

    username: str
    """The name of the user in format `name#1234`."""


class UserRatingsResponse(pydantic.BaseModel):
    """The representation of the full response from `/v1/user/ratings`."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    total: int
    """The total number of records in this response."""
    ratings: list[UserRatingsResponseSubRecord]
    """A `list` of all records returned."""


class UserValidateResponseRecord(BaseImageRatingRecord):
    """A single sub-record in a response from the `/v1/validate/{user_id}` endpoint."""


class UserValidateResponse(pydantic.BaseModel):
    """The representation of the full response from `/v1/validate/{user_id}`."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    total: int
    """The total number of records in this response."""
    ratings: list[UserValidateResponseRecord]
    """A `list` of all records returned."""


class UserCheckResponse(pydantic.BaseModel):
    """A single record from the `/v1/user/check/` endpoint."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    ratings_in_timeframe: int
    """The number of ratings this user submitted in the timeframe."""
    ratings_per_minute_in_timeframe: int
    """The average number of ratings per minute."""
    ratings_past_three_hours: int
    """The average number of ratings in the three hours prior to the request."""
    ratings_per_minute_for_past_three_hours: int
    """The average number of ratings per minute in the three hours prior to the request."""
    suspect_divergences: int
    """The number of instances of this user's rating not being within the criteria."""
    captchas_failed: int
    """The number of captchas failed by this user."""


# endregion


class Rating_API_Reflection:
    """Uses reflection to dynamically get all subclasses of `BaseRequest` defined in module `ratings_api.apimodels`."""

    _instance = None
    _listOfTypes: list[type[BaseRequest]] = []  # default mutable ok because this class is a singleton

    def __new__(cls) -> typing_extensions.Self:  # noqa: ANN204, ANN101
        """Create an instance if no instance already exists, otherwise returns the already created instance."""
        # Prevents reflection from happening more than once.
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def getAllRequestTypes(self) -> list[type[BaseRequest]]:
        """Returns all non-abstract classes inheriting from `BaseRequest`."""
        if len(self._listOfTypes) > 0:
            return self._listOfTypes

        for value in sys.modules[__name__].__dict__.values():
            if isinstance(value, type) and issubclass(value, BaseRequest) and not inspect.isabstract(value):
                self._listOfTypes.append(value)

        return self._listOfTypes.copy()
