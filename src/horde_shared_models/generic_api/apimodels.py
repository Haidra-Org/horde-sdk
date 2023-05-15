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
    def getEndpointURL() -> str:
        """Return the endpoint URL, including the path to the specific API action defined by this object."""

    @staticmethod
    @abc.abstractmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
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
    def user_idNumeric(cls, value: str) -> str:
        """The API endpoint expects a string, but the only valid values would be numbers only."""
        try:
            int(value)
        except ValueError as valueError:
            raise ValueError(
                f"user_id must be a str, but only numeric values are allowed!\n  Value: {value}"
            ) from valueError
        return value
