"""API data model bases applicable across all (or many) horde APIs."""

import abc
from collections.abc import Callable

from pydantic import BaseModel, Field, field_validator

from horde_sdk.generic_api.metadata import GenericAcceptTypes


class HordeAPIMessage(BaseModel):
    """Represents any request or response from any Horde API."""

    __api_model_name__: str | None
    """The name of the model as seen in the published swagger doc. If none, there is no payload for this message."""


class BaseResponse(HordeAPIMessage):
    """Represents any response from any Horde API."""

    model_config = {"frozen": True}

    __http_status_codes__: dict[int, Callable]  # TODO: type for Callable
    """A mapping of HTTP status codes to functions which will be used to determine if the response is valid."""


class BaseRequest(HordeAPIMessage, abc.ABC):
    """Represents any request to any Horde API."""

    model_config = {"frozen": True}

    __http_method__: str

    accept: GenericAcceptTypes = GenericAcceptTypes.json
    """The 'accept' header field."""
    # X_Fields # TODO

    @staticmethod
    @abc.abstractmethod
    def get_endpoint_url() -> str:
        """Return the endpoint URL, including the path to the specific API action defined by this object"""

    @staticmethod
    @abc.abstractmethod
    def get_expected_response_type() -> type[BaseResponse]:
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
