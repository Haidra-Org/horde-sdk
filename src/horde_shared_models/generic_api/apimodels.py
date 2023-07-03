"""API data model bases applicable across all (or many) horde APIs."""

import abc

import pydantic

from .metadata import GenericAcceptTypes


class BaseRequest(pydantic.BaseModel, abc.ABC):
    """Represents any request to any Horde API."""

    class Config:
        """Pydantic config class."""

        allow_mutation = False

    accept: GenericAcceptTypes = GenericAcceptTypes.json
    """The 'accept' header field."""
    # X_Fields # TODO

    @staticmethod
    @abc.abstractmethod
    def get_endpoint_url() -> str:
        """Return the endpoint URL, including the path to the specific API action defined by this object."""

    @staticmethod
    @abc.abstractmethod
    def get_expected_response_type() -> type[pydantic.BaseModel]:
        """Return the `type` of the response expected."""


class BaseRequestAuthenticated(BaseRequest):
    """Represents abstractly a authenticated request, IE, using an API key."""

    apikey: str  # TODO validator
    """A horde API key."""


class BaseRequestUserSpecific(BaseRequestAuthenticated):
    """Represents the minimum for any request specifying a specific user to the API."""

    user_id: str
    """The user's ID, as a `str`, but only containing numeric values."""

    @pydantic.validator("user_id")
    def user_id_is_numeric(cls, value: str) -> str:
        """The API endpoint expects a string, but the only valid values would be numbers only."""
        if not value.isnumeric():
            raise ValueError("user_id must only contain numeric values")
        return value


class BaseRequestWorkerDriven(BaseRequestAuthenticated):
    trusted_workers: bool = False
    slow_workers: bool = False
    workers: list[str] = pydantic.Field(default_factory=list)
    worker_blacklist: list[str] = pydantic.Field(default_factory=list)

    models: list[str]

    dry_run: bool = False
