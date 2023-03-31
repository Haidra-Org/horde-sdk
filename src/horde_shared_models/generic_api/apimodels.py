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
