"""API data model bases applicable across all (or many) horde APIs."""

from __future__ import annotations

import abc
import base64
import os
import uuid
from typing import Any

import aiohttp
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import override

from horde_sdk import _default_sslcontext
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.consts import ANON_API_KEY
from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH, url_with_path
from horde_sdk.generic_api.metadata import GenericAcceptTypes

try:
    from horde_sdk._version import __version__
except ImportError:
    __version__ = "0.0.0"
    logger.warning(
        "Could not import version from _version.py. If this is a development environment, this is normal."
        " You can fix this by building the package with `python -m build`.",
    )


class HordeAPIObject(BaseModel, abc.ABC):
    """Base class for all Horde API data models, requests, or responses."""

    @classmethod
    @abc.abstractmethod
    def get_api_model_name(cls) -> str | None:
        """Return the name of the model as seen in the published swagger doc.

        If none, there is no payload, such as for a GET request.
        """

    model_config = ConfigDict(
        frozen=True,
        use_attribute_docstrings=True,
    )


class HordeAPIDataObject(BaseModel):
    """Base class for all Horde API data models which appear as objects within other data models.

    These are objects which are not specifically defined by the API docs, but (logically or otherwise) are
    returned by the API. Occasionally, objects derived from this class may also be used as a mixin to compose other
    models.
    """

    model_config = (
        ConfigDict(
            frozen=True,
            use_attribute_docstrings=True,
        )
        if not os.getenv("TESTS_ONGOING")
        else ConfigDict(
            frozen=True,
            use_attribute_docstrings=True,
            extra="forbid",
        )
    )


class HordeAPIMessage(HordeAPIObject):
    """Represents any request or response from any Horde API."""

    @classmethod
    def get_sensitive_fields(cls) -> set[str]:
        """Return a set of fields which should be redacted from logs."""
        return {"apikey"}

    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        """Return an additional set of fields to exclude from the log_safe_model_dump method."""
        return set()

    def log_safe_model_dump(self, extra_exclude: set[str] | None = None) -> dict[Any, Any]:
        """Return a dict of the model's fields, with any sensitive fields redacted."""
        if extra_exclude is None:
            extra_exclude = set()

        return self.model_dump(
            exclude=self.get_sensitive_fields() | self.get_extra_fields_to_exclude_from_log() | extra_exclude,
        )


class HordeResponse(HordeAPIMessage):
    """Represents any response from any Horde API."""


class HordeResponseBaseModel(HordeResponse, BaseModel):
    """Base class for all Horde API response data models (leveraging pydantic)."""

    model_config = (
        ConfigDict(frozen=True) if not os.getenv("TESTS_ONGOING") else ConfigDict(frozen=True, extra="forbid")
    )


class ResponseRequiringFollowUpMixin(abc.ABC):
    """Represents any response from any Horde API which requires a follow up request of some kind."""

    @abc.abstractmethod
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        """Return the information required from this response to submit a follow up request.

        Note that this dict uses the alias field names (as seen on the API), not the python field names.
        JobIDs will be returned as `{"id": "00000000-0000-0000-0000-000000000000"}` instead of
        `{"id_": "00000000-0000-0000-0000-000000000000"}`.

        Returns:
            list[dict[str, object]]: A list of dicts of parameter names and values for each follow up request.
        """

    def get_follow_up_extra_params(self) -> dict[str, object]:
        """Return any additional information required from this response to submit a follow up request."""
        logger.warning("This method may be deprecated in the future.")
        return {}  # TODO: Would extra params need to come into play for a list of follow up requests?

    def get_follow_up_all_params(self) -> list[dict[str, object]]:
        """Return the required inf from this response to submit any follow up requests warranted from this response.

        Note that this dict uses the alias field names (as seen on the API), not the python field names.

        `get_follow_up_failure_cleanup_params` is **not** included.

        This is used for context management.

        Returns:
            list[dict[str, object]]: A list of dicts of parameter names and values for each follow up request.
        """
        follow_up_params = self.get_follow_up_returned_params()

        if isinstance(follow_up_params, list):
            return follow_up_params  # FIXME: Would extra params need to come into play?

        return [{**follow_up_params, **self.get_follow_up_extra_params()}]

    @classmethod
    @abc.abstractmethod
    def get_follow_up_default_request_type(cls) -> type[HordeRequest]:
        """Return the default request type for this response."""

    @classmethod
    @abc.abstractmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[HordeRequest]:
        """Return the request type for this response to clean up after a failed follow up request.

        Defaults to `None`, meaning no cleanup request is needed.
        """

    _cleanup_requests: list[HordeRequest] | None = None

    def get_follow_up_failure_cleanup_params(self) -> dict[str, object]:
        """Return any extra information required from this response to clean up after a failed follow up request.

        Note that this dict uses the alias field names (as seen on the API), not the python field names.

        This is used for context management.
        """
        return {}

    def get_follow_up_failure_cleanup_request(self) -> list[HordeRequest]:
        """Return the request for this response to clean up after a failed follow up request."""
        if self.ignore_failure():
            return []

        if self._cleanup_requests is not None:
            return self._cleanup_requests

        cleanup_request_type = self.get_follow_up_failure_cleanup_request_type()
        if not cleanup_request_type:
            raise ValueError("No cleanup request type defined")

        self._cleanup_requests = []

        all_cleanup_params: list[dict[str, object]] = self.get_follow_up_all_params()
        for cleanup_params in all_cleanup_params:
            cleanup_params.update(self.get_follow_up_failure_cleanup_params())
            self._cleanup_requests.append(cleanup_request_type.model_validate(cleanup_params))

        return self._cleanup_requests

    @classmethod
    def get_follow_up_request_types(cls) -> list[type[HordeRequest]]:
        """Return a list of all the possible follow up request types for this response."""
        return [cls.get_follow_up_default_request_type()]

    def ignore_failure(self) -> bool:
        """Return if the object is in a state which doesn't require failure follow up."""
        # ImageGenerateJobPopResponse was the use case at the time of writing
        return False

    def does_target_request_follow_up(self, target_request: HordeRequest) -> bool:
        """Return whether the `target_request` would follow up on this request.

        Args:
            target_request (HordeRequest): The request to check if it would follow up on this request.

        Returns:
            bool: Whether the `target_request` would follow up on this request.
        """
        follow_up_returned_params = self.get_follow_up_returned_params(as_python_field_name=True)

        if len(follow_up_returned_params) == 0:
            logger.warning("No follow up returned params defined for this request")
            return False
        all_match = True
        for param_set in follow_up_returned_params:
            for key, value in param_set.items():
                if hasattr(target_request, key) and getattr(target_request, key) != value:
                    all_match = False
                    break
        return all_match


class ResponseWithProgressMixin(HordeAPIDataObject):
    """Represents any response from any Horde API which contains progress information."""

    @abc.abstractmethod
    def is_job_complete(self, number_of_result_expected: int) -> bool:
        """Return whether the job is complete.

        Args:
            number_of_result_expected (int): The number of results expected from the job.

        Returns:
            bool: Whether the job is complete.
        """

    @abc.abstractmethod
    def is_job_possible(self) -> bool:
        """Return whether the job is possible.

        Returns:
            bool: Whether the job is possible.
        """

    @classmethod
    def is_final_follow_up(cls) -> bool:
        """Return whether this response is the final follow up response."""
        return False

    @classmethod
    @abc.abstractmethod
    def get_finalize_success_request_type(cls) -> type[HordeRequest] | None:
        """Return the request type for this response to finalize the job on success, or `None` if not needed."""


class ResponseRequiringDownloadMixin(HordeAPIDataObject):
    """Represents any response which may require downloading additional data."""

    async def download_file_as_base64(self, client_session: aiohttp.ClientSession, url: str) -> str:
        """Download a file and return the value as a base64 string."""
        async with client_session.get(url, ssl=_default_sslcontext) as response:
            response.raise_for_status()
            return base64.b64encode(await response.read()).decode("utf-8")

    async def download_file_to_field_as_base64(
        self,
        client_session: aiohttp.ClientSession,
        url: str,
        field_name: str,
    ) -> None:
        """Download a file from a URL and save it to the field.

        Args:
            client_session (aiohttp.ClientSession): The aiohttp client session to use for the download.
            url (str): The URL to download the file from.
            field_name (str): The name of the field to save the file to.
        """
        async with client_session.get(url, ssl=_default_sslcontext) as response:
            response.raise_for_status()
            setattr(self, field_name, base64.b64encode(await response.read()).decode("utf-8"))

    @abc.abstractmethod
    async def async_download_additional_data(self, client_session: aiohttp.ClientSession) -> None:
        """Asynchronously download any additional data required for this response."""

    @abc.abstractmethod
    def download_additional_data(self) -> None:
        """Download any additional data required for this response."""


class ContainsMessageResponseMixin(HordeAPIDataObject):
    """Represents any response from any Horde API which contains a message."""

    message: str = ""
    """A message from the API. This is typically an error or warning message, but may also be informational."""


class RequestErrorResponse(HordeResponseBaseModel, ContainsMessageResponseMixin):
    """The catch all error response for any request to any Horde API.

    v2 API Model: `RequestError`
    """

    object_data: object = None
    """This is a catch all for any additional data that may be returned by the API relevant to the error."""

    rc: str = "RC_MISSING"

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestError"


class HordeRequest(HordeAPIMessage, BaseModel):
    """Represents any request to any Horde API."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    @classmethod
    @abc.abstractmethod
    def get_http_method(cls) -> HTTPMethod:
        """Return the HTTP method (verb) this request uses."""

    accept: GenericAcceptTypes = GenericAcceptTypes.json
    """The 'accept' header field."""
    # X_Fields # TODO

    client_agent: str = Field(
        default=f"horde_sdk:{__version__}:https://github.com/haidra-org/horde-sdk",
        alias="Client-Agent",
    )
    """The requesting client's agent. You should set this to reflect the name, version and contact information
    for your client."""

    @classmethod
    def get_api_endpoint_url(cls) -> str:
        """Return the endpoint URL, including the path to the specific API action defined by this object."""
        return url_with_path(base_url=cls.get_api_url(), path=cls.get_api_endpoint_subpath())

    @classmethod
    @abc.abstractmethod
    def get_api_url(cls) -> str:
        """Return the base URL for the API this request is for."""

    @classmethod
    @abc.abstractmethod
    def get_api_endpoint_subpath(cls) -> GENERIC_API_ENDPOINT_SUBPATH:
        """Return the subpath to the specific API action defined by this object."""

    @classmethod
    @abc.abstractmethod
    def get_default_success_response_type(cls) -> type[HordeResponse]:
        """Return the `type` of the response expected in the ordinary case of success."""

    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponse]]:
        """Return a dict of HTTP status codes and the expected `HordeResponse`.

        Defaults to `{HTTPStatusCode.OK: cls.get_expected_response_type()}`, but may be overridden to support other
        status codes.
        """
        return {HTTPStatusCode.OK: cls.get_default_success_response_type()}

    @classmethod
    def get_header_fields(cls) -> list[str]:
        """Return a list of field names from this request object that should be sent as header fields.

        This is in addition to `GenericHeaderFields`'s values, and possibly the API specific class
        which inherits from `GenericHeaderFields`, typically found in the `horde_sdk.<api_name>_api.metadata` module.
        """
        return []

    @classmethod
    def get_query_fields(cls) -> list[str]:
        """Return a list of field names from this request object that should be sent as query parameters.

        This is in addition to `GenericQueryFields`'s values, and possibly the API specific class
        which inherits from `GenericQueryFields`, typically found in the `horde_sdk.<api_name>_api.metadata` module.
        """
        return []

    def get_number_of_results_expected(self) -> int:
        """Return the number of (job) results expected from this request.

        Defaults to `1`, but may be overridden to dynamically change the number of results expected.

        This is factored into context management; if the number of results expected is not met, the job is considered
        unhandled on an exception and followed up on to attempt to close it.
        """
        return 1

    def get_requires_follow_up(self) -> bool:
        """Return whether this request requires a follow up request(s).

        Returns:
            bool: Whether this request requires a follow up request to close the job on the server.
        """
        for response_type in self.get_success_status_response_pairs().values():
            if issubclass(response_type, ResponseRequiringFollowUpMixin):
                return True
        return False

    @override
    @classmethod
    def get_sensitive_fields(cls) -> set[str]:
        return {"apikey"}


class APIKeyAllowedInRequestMixin(HordeAPIDataObject):
    """Mix-in class to describe an endpoint which may require authentication."""

    apikey: str | None = None
    """Defaults to `ANON_API_KEY`. See also `.is_api_key_required()`"""

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return True

    @field_validator("apikey", mode="before")
    def validate_api_key_length(cls, v: str) -> str:
        """Validate that the API key is the correct length, or is the special ANON_API_KEY."""
        if v is None:
            return ANON_API_KEY
        if v == ANON_API_KEY:
            return v
        if len(v) == 36:
            try:
                uuid.UUID(v)
                return v
            except ValueError as e:
                raise ValueError("API key must be a valid UUID") from e
            return v
        if len(v) != 22:
            raise ValueError("API key must be 22 characters long")
        return v


class RequestSpecifiesUserIDMixin(HordeAPIDataObject):
    """Mix-in class to describe an endpoint for which you can specify a user."""

    user_id: str
    """The user's ID, as a `str`, but only containing numeric values."""

    @field_validator("user_id")
    def user_id_is_numeric(cls, value: str) -> str:
        """Check if the ID is a numeric string.

        The API endpoint expects a string, but the only valid values would be numbers only.
        """
        if not value.isnumeric():
            raise ValueError("user_id must only contain numeric values")
        return value


class RequestUsesWorkerMixin(HordeAPIDataObject):
    """Mix-in class to describe an endpoint for which you can specify workers."""

    trusted_workers: bool = False
    """When true, only trusted workers will serve this request. When False, Evaluating workers will also be used
     which can increase speed but adds more risk!"""
    slow_workers: bool = True
    """When True, allows slower workers to pick up this request. Disabling this incurs an extra kudos cost."""
    extra_slow_workers: bool = False
    """When True, allows extra slow workers to pick up this request."""
    workers: list[str] = Field(default_factory=list)
    """A list of worker IDs to use for this request. If empty, any worker can pick up the request. Using this incurs
    and extra kudos cost."""
    worker_blacklist: list[str] = Field(default_factory=list)
    """If true, the worker list will be treated as a blacklist instead of a whitelist."""
    models: list[str]
    """The generative models to use for this request."""

    dry_run: bool = False
    """If true, the request will not be processed, but will return a response with the estimated kudos cost."""


__all__ = [
    "APIKeyAllowedInRequestMixin",
    "HordeRequest",
    "HordeResponse",
    "HordeResponseBaseModel",
    "ContainsMessageResponseMixin",
    "HordeAPIObject",
    "HordeAPIMessage",
    "RequestErrorResponse",
    "RequestSpecifiesUserIDMixin",
    "RequestUsesWorkerMixin",
    "ResponseRequiringFollowUpMixin",
    "ResponseWithProgressMixin",
]
