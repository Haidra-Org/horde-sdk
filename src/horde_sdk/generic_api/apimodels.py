"""API data model bases applicable across all (or many) horde APIs."""

import abc
from collections.abc import Callable

from pydantic import BaseModel, Field, field_validator

from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.endpoints import url_with_path
from horde_sdk.generic_api.metadata import GenericAcceptTypes


class HordeAPIMessage(BaseModel, abc.ABC):
    """Represents any request or response from any Horde API."""

    @classmethod
    @abc.abstractmethod
    def get_api_model_name(cls) -> str | None:
        """Return the name of the model as seen in the published swagger doc. If none, there is no payload for
        this message.

        Note that GET request should have this set to `None` as they do not have a payload.
        """


class BaseResponse(HordeAPIMessage):
    """Represents any response from any Horde API."""

    model_config = {"frozen": True}

    @classmethod
    # @abc.abstractmethod
    def get_expected_http_status_codes(cls) -> dict[HTTPStatusCode, Callable]:
        """Return a dict of HTTP status codes to functions which will be used to determine if the response is valid."""
        return {HTTPStatusCode.OK: lambda x: x}


class BaseRequest(HordeAPIMessage):
    """Represents any request to any Horde API."""

    model_config = {"frozen": True}

    @classmethod
    @abc.abstractmethod
    def get_http_method(cls) -> HTTPMethod:
        """Return the HTTP method (verb) this request uses."""

    accept: GenericAcceptTypes = GenericAcceptTypes.json
    """The 'accept' header field."""
    # X_Fields # TODO

    @classmethod
    def get_endpoint_url(cls) -> str:
        """Return the endpoint URL, including the path to the specific API action defined by this object"""
        return url_with_path(base_url=cls.get_api_url(), path=cls.get_endpoint_subpath())

    @classmethod
    @abc.abstractmethod
    def get_api_url(cls) -> str:
        """Return the base URL for the API this request is for."""

    @classmethod
    @abc.abstractmethod
    def get_endpoint_subpath(cls) -> str:
        """Return the subpath to the specific API action defined by this object"""

    @classmethod
    @abc.abstractmethod
    def get_expected_response_type(cls) -> type[BaseResponse]:
        """Return the `type` of the response expected."""


class BaseRequestAuthenticated(BaseRequest):
    """Represents abstractly a authenticated request, IE, using an API key."""

    apikey: str  # TODO validator
    """A horde API key."""


class BaseRequestUserSpecific(BaseRequestAuthenticated):
    """Represents the minimum for any request specifying a specific user to the API."""

    user_id: str
    """The user's ID, as a `str`, but only containing numeric values."""

    @field_validator("user_id")
    def user_id_is_numeric(cls, value: str) -> str:
        """The API endpoint expects a string, but the only valid values would be numbers only."""
        if not value.isnumeric():
            raise ValueError("user_id must only contain numeric values")
        return value


class BaseRequestWorkerDriven(BaseRequestAuthenticated):
    """Represents the minimum for any request which is ultimately backed by a worker (Such as on AI-Horde)."""

    trusted_workers: bool = False
    slow_workers: bool = False
    workers: list[str] = Field(default_factory=list)
    worker_blacklist: list[str] = Field(default_factory=list)

    models: list[str]

    dry_run: bool = False
