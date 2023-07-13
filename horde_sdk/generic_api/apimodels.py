"""API data model bases applicable across all (or many) horde APIs."""
from __future__ import annotations

import abc
import json

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Self, override

from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.endpoints import url_with_path
from horde_sdk.generic_api.metadata import GenericAcceptTypes


class HordeAPIModel(BaseModel, abc.ABC):
    """Base class for all Horde API data models, requests, or responses."""

    model_config = ConfigDict(frozen=True)

    @classmethod
    @abc.abstractmethod
    def get_api_model_name(cls) -> str | None:
        """Return the name of the model as seen in the published swagger doc. If none, there is no payload,
        such as for a GET request.
        """

    def to_json_horde_sdk_safe(self) -> str:
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

    @classmethod
    def is_requiring_follow_up(cls) -> bool:
        """Return whether this response requires a follow up request of some kind."""
        return False

    def get_follow_up_data(self) -> dict[str, object]:
        """Return the information required from this response to submit a follow up request.

        Note that this dict uses the alias field names (as seen on the API), not the python field names.
        GenerationIDs will be returned as `{"id": "00000000-0000-0000-0000-000000000000"}` instead of
        `{"id_": "00000000-0000-0000-0000-000000000000"}`.

        This means it is suitable for passing directly
        to a constructor, such as `ImageGenerateStatusRequest(**response.get_follow_up_required_info())`.
        """
        raise NotImplementedError("This response does not require a follow up request")

    @classmethod
    def get_follow_up_default_request(cls) -> type[BaseRequest]:
        raise NotImplementedError("This response does not require a follow up request")

    @classmethod
    def get_follow_up_request_types(cls) -> list[type]:  # TODO type hint???
        """Return a list of all the possible follow up request types for this response"""
        return [cls.get_follow_up_default_request()]

    _follow_up_handled: bool = False

    def set_follow_up_handled(self) -> None:
        """Set this response as having had its follow up request handled.

        This is used for context management.
        """
        self._follow_up_handled = True

    def is_follow_up_handled(self) -> bool:
        """Return whether this response has had its follow up request handled.

        This is used for context management.
        """
        return self._follow_up_handled

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
        """Create a new pydantic BaseModel as normal if the passed value is a dict, otherwise, use the 'array' method.

        This is useful for handling responses which return a json array instead of a json object.
        See also `is_array_response` and `get_array_item_type`.

        Args:
            dict_or_array (dict | list): The dict or array to create the model from.

        Returns:
            `Self`: The new model instance, of the type which called this method.
        """
        if not isinstance(dict_or_array, dict):
            if not isinstance(dict_or_array, list):
                dict_or_array = [dict_or_array]

            new_instance = cls()
            new_instance.set_array(dict_or_array)
            return new_instance

        return cls(**dict_or_array)

    @override
    def to_json_horde_sdk_safe(self) -> str:
        # TODO: Is there a more pydantic way to do this?
        if self.is_array_response():
            self_array = self.get_array()

            if not self_array:
                return "{}"

            return json.dumps(self_array, default=lambda o: o.model_dump(by_alias=True, exclude_none=True), indent=4)

        return super().to_json_horde_sdk_safe()


class RequestErrorResponse(BaseResponse):
    """The catch all error response for any request to any Horde API.

    v2 API Model: `RequestError`
    """

    message: str = ""

    object_data: object = None
    """This is a catch all for any additional data that may be returned by the API relevant to the error."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestError"


class BaseRequest(HordeAPIMessage):
    """Represents any request to any Horde API."""

    @classmethod
    @abc.abstractmethod
    def get_http_method(cls) -> HTTPMethod:
        """Return the HTTP method (verb) this request uses."""

    accept: GenericAcceptTypes = GenericAcceptTypes.json
    """The 'accept' header field."""
    # X_Fields # TODO

    client_agent: str = Field(
        default="horde_sdk:0.2.0:https://githib.com/haidra-org/horde-sdk",
        alias="Client-Agent",
    )

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
        """Return a list of field names from this request object that should be sent as header fields.

        This is in addition to `GenericHeaderFields`'s values, and possibly the API specific class
        which inherits from `GenericHeaderFields`, typically found in `horde_sdk.<api_name>_api.metadata`.
        """
        return []

    @classmethod
    def is_recovery_enabled(cls) -> bool:
        """Return whether this request should attempt to recover from a client failure by submitting a request
        specified by `get_recovery_request_type`.

        This is used in for context management.
        """
        return False

    def get_recovery_request_type(self) -> type[BaseRequest]:
        """Return an instance of the request that should be submitted to clean up after a client failure."""
        if self.is_recovery_enabled():
            raise NotImplementedError(
                (
                    "This request is configured to support recovery with `is_recovery_enabled`, but does not "
                    "implement `get_recovery_request`."
                ),
            )
        raise NotImplementedError(
            "This request does not support recovery. Use `.is_recovery_enabled` to determine this.",
        )


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


__all__ = [
    "HordeAPIModel",
    "HordeAPIMessage",
    "BaseResponse",
    "BaseRequest",
    "BaseRequestAuthenticated",
    "BaseRequestUserSpecific",
    "BaseRequestWorkerDriven",
    "RequestErrorResponse",
]
