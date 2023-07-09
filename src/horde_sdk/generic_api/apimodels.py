"""API data model bases applicable across all (or many) horde APIs."""

import abc
import json

from pydantic import BaseModel, Field, field_validator
from typing_extensions import Self, override

from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api import GenericAcceptTypes
from horde_sdk.generic_api.endpoints import url_with_path


class HordeAPIModel(BaseModel, abc.ABC):
    """Base class for all Horde API data models, requests, or responses."""

    @classmethod
    @abc.abstractmethod
    def get_api_model_name(cls) -> str | None:
        """Return the name of the model as seen in the published swagger doc. If none, there is no payload,
        such as for a GET request.
        """

    def to_json_horde_sdk_safe(self):
        """Return the model as a JSON string, taking into account the paradigms of the horde_sdk.

        If you use the default json dumping behavior, you will find some rough edges, such as alias
        field names not being used, `None` values being included, and responses which return arrays
        not being handled correctly (returning `{}` instead of the object)
        """
        return self.model_dump_json(by_alias=True, exclude_none=True)


class HordeAPIMessage(HordeAPIModel):
    """Represents any request or response from any Horde API."""


class BaseResponse(HordeAPIMessage):
    """Represents any response from any Horde API."""

    model_config = {"frozen": True}

    @classmethod
    def is_array_response(cls) -> bool:
        """Return whether this response is an array of an internal type."""
        return False

    @classmethod
    def get_array_item_type(cls) -> type[BaseModel]:
        """If this is an array response, return the type of the internal array elements.

        Check `is_array_response` first if you are not sure if this is an array response.
        """
        raise NotImplementedError("This is not an array response")

    def set_array(self, list_: list[HordeAPIModel]) -> None:
        """Set this response's internal array to the passed value."""
        raise NotImplementedError("This is not an array response")

    def get_array(self) -> list[HordeAPIModel]:
        """Get this response's internal array."""
        raise NotImplementedError("This is not an array response")

    @classmethod
    def from_dict_or_array(cls, dict_or_array: dict | list) -> Self:
        if not isinstance(dict_or_array, dict):
            if not isinstance(dict_or_array, list):
                dict_or_array = [dict_or_array]

            new_instance = cls()
            new_instance.set_array(dict_or_array)
            return new_instance

        return cls(**dict_or_array)

    @override
    def to_json_horde_sdk_safe(self):
        # TODO: Is there a more pydantic way to do this?
        if self.is_array_response():
            self_array = self.get_array()

            if not self_array:
                return "{}"

            return json.dumps(self_array, default=lambda o: o.model_dump(by_alias=True, exclude_none=True), indent=4)

        return super().to_json_horde_sdk_safe()


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
    def get_success_response_type(cls) -> type[BaseResponse]:
        """Return the `type` of the response expected in the ordinary case of success."""

    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[BaseResponse]]:
        """Return a dict of HTTP status codes and the expected `BaseResponse`.

        Defaults to `{HTTPStatusCode.OK: cls.get_expected_response_type()}`, but may be overridden to support other
        status codes.
        """
        return {HTTPStatusCode.OK: cls.get_success_response_type()}

    @classmethod
    def get_header_fields(cls) -> list[str]:
        """Return a dict of field names from this request that should be sent as header fields.

        This is in addition to `GenericHeaderFields`'s values, and possibly the API specific class
        which inherits from `GenericHeaderFields`, typically found in `horde_sdk.<api_name>_api.metadata`.
        """
        return []


class BaseRequestAuthenticated(BaseModel):
    """Mix-in class to describe an endpoint which may require authentication."""

    apikey: str | None = None  # TODO validator
    """A horde API key."""


class BaseRequestUserSpecific(BaseModel):
    """Mix-in class to describe an endpoint for which you can specify a user.""" ""

    user_id: str
    """The user's ID, as a `str`, but only containing numeric values."""

    @field_validator("user_id")
    def user_id_is_numeric(cls, value: str) -> str:
        """The API endpoint expects a string, but the only valid values would be numbers only."""
        if not value.isnumeric():
            raise ValueError("user_id must only contain numeric values")
        return value


class BaseRequestWorkerDriven(BaseModel):
    """ "Mix-in class to describe an endpoint for which you can specify workers."""

    trusted_workers: bool = False
    slow_workers: bool = False
    workers: list[str] = Field(default_factory=list)
    worker_blacklist: list[str] = Field(default_factory=list)

    models: list[str]

    dry_run: bool = False
