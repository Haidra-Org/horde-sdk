"""The API client which can perform arbitrary horde API requests."""

from __future__ import annotations

import asyncio
import os
from abc import ABC
from ssl import SSLContext
from typing import Any, TypeVar

import aiohttp
import requests
from loguru import logger
from pydantic import BaseModel, ValidationError
from strenum import StrEnum
from typing_extensions import override

from horde_sdk import _default_sslcontext
from horde_sdk.ai_horde_api.exceptions import AIHordePayloadValidationError
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeRequest,
    HordeResponse,
    RequestErrorResponse,
    ResponseRequiringFollowUpMixin,
    ResponseWithProgressMixin,
)
from horde_sdk.generic_api.consts import ANON_API_KEY
from horde_sdk.generic_api.metadata import (
    GenericAcceptTypes,
    GenericHeaderFields,
    GenericPathFields,
    GenericQueryFields,
)

"""The default SSL context to use for aiohttp requests."""


class ParsedRawRequest(BaseModel):
    """A helper class for passing around the data needed to make an actual web request."""

    endpoint_no_query: str
    """The endpoint URL without any query parameters."""
    request_headers: dict[str, Any]
    """The headers to be sent with the request."""
    request_queries: dict[str, Any]
    """The query parameters to be sent with the request."""
    request_params: dict[str, Any]
    """The path parameters to be sent with the request."""
    request_body: dict[str, Any] | None
    """The body to be sent with the request, or `None` if no body should be sent."""


HordeRequestTypeVar = TypeVar("HordeRequestTypeVar", bound=HordeRequest)
"""TypeVar for the horde request type."""
HordeResponseTypeVar = TypeVar("HordeResponseTypeVar", bound=HordeResponse)
"""TypeVar for the horde response type."""


class BaseHordeAPIClient(ABC):
    """An abstract class which is the base for all horde API clients."""

    # region Private Fields
    _aiohttp_session: aiohttp.ClientSession
    _ssl_context: SSLContext

    _apikey: str | None

    _header_field_keys: type[GenericHeaderFields] = GenericHeaderFields
    """A list of all fields which would appear in the API request header."""
    _path_field_keys: type[GenericPathFields] = GenericPathFields
    """A list of all fields which would appear in any API action path (appearing before the '?' as part of the URL)"""
    _query_field_keys: type[GenericQueryFields] = GenericQueryFields
    """A list of all fields which would appear in any API action query (appearing after the '?')"""

    _accept_types: type[GenericAcceptTypes] = GenericAcceptTypes
    """A list of all valid values for the header key 'accept'."""

    # endregion

    def __init__(
        self,
        *,
        apikey: str | None = None,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
        ssl_context: SSLContext = _default_sslcontext,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize a new `GenericHordeAPIClient` instance.

        Args:
            apikey (str, optional): The API key to use for authenticated requests. Defaults to None, which will use the
                anonymous API key.
            header_fields (type[GenericHeaderFields], optional): Pass this to define the API's Header fields.
                Defaults to GenericHeaderFields.
            path_fields (type[GenericPathFields], optional): Pass this to define the API's URL path fields.
                Defaults to GenericPathFields.
            query_fields (type[GenericQueryFields], optional): Pass this to define the API's URL query fields.
                Defaults to GenericQueryFields.
            accept_types (type[GenericAcceptTypes], optional): Pass this to define the API's accept types.
                Defaults to GenericAcceptTypes.
            ssl_context (SSLContext, optional): The SSL context to use for aiohttp requests.
                Defaults to using `certifi`.
            kwargs: Any additional keyword arguments are ignored.

        Raises:
            TypeError: If any of the passed types are not subclasses of their respective `Generic*` class.
        """
        self._apikey = apikey

        if not isinstance(ssl_context, SSLContext):
            raise TypeError("`ssl_context` must be of type `SSLContext`!")

        self._ssl_context = ssl_context

        if not self._apikey:
            self._apikey = ANON_API_KEY

        if os.getenv("AI_HORDE_DEV_APIKEY"):
            logger.warning("Using the AI Horde API key from the environment variable `AI_HORDE_DEV_APIKEY`.")
            self._apikey = os.getenv("AI_HORDE_DEV_APIKEY")

        if not issubclass(header_fields, GenericHeaderFields):  # pragma: no cover
            raise TypeError("`header_fields` must be of type `GenericHeaderData` or a subclass of it!")
        if not issubclass(path_fields, GenericPathFields):  # pragma: no cover
            raise TypeError("`path_fields` must be of type `GenericPathData` or a subclass of it!")
        if not issubclass(accept_types, GenericAcceptTypes):  # pragma: no cover
            raise TypeError("`accept_types` must be of type `GenericAcceptTypes` or a subclass of it!")
        if not issubclass(query_fields, GenericQueryFields):  # pragma: no cover
            raise TypeError("`query_fields` must be of type `GenericQueryData` or a subclass of it!")

        self._header_field_keys = header_fields
        self._path_field_keys = path_fields
        self._query_field_keys = query_fields
        self._accept_types = accept_types

    def _validate_and_prepare_request(self, api_request: HordeRequest) -> ParsedRawRequest:
        """Validate the given `api_request` and returns a `_ParsedRequest` instance with the data to be sent.

        This method converts a `HordeRequest` instance into the data needed to make a request with `requests`. It
        validates the request and extracts the specified headers, paths, and queries from the request. It also extracts
        any extra header fields and the request body data from the request. Finally, it returns a `_ParsedRequest`
        instance with the extracted data.

        Args:
            api_request (HordeRequest): The `HordeRequest` instance to be validated and prepared.
            expected_response_type (type[HordeResponse]): The expected response type.

        Returns:
            _ParsedRequest: A `_ParsedRequest` instance with the extracted data to be sent in the request.

        Raises:
            TypeError: If `api_request` is not of type `HordeRequest` or a subclass of it.
        """
        if not isinstance(api_request, HordeRequest):
            raise TypeError("`request` must be of type `HordeRequest` or a subclass of it!")

        # Define a helper function to extract specified data keys from the request
        def get_specified_data_keys(data_keys: type[StrEnum], api_request: HordeRequest) -> dict[str, str]:
            """Extract the specified data keys from the request and returns them as a dictionary."""
            return {
                # The key is the python field name.
                python_field_name:
                # The value is the API field name, converted to a string. The python name may not match
                # as is the case with `id`, which is reserved in python, and `id_` is used instead.
                api_field_name.value
                for python_field_name, api_field_name in data_keys._member_map_.items()
                if hasattr(api_request, python_field_name) and getattr(api_request, python_field_name) is not None
            }

        # Extract the specified headers, paths, and queries from the request, so they don't end up in
        # a request (payload) body
        specified_headers = get_specified_data_keys(self._header_field_keys, api_request)
        specified_paths = get_specified_data_keys(self._path_field_keys, api_request)
        specified_queries = get_specified_data_keys(self._query_field_keys, api_request)

        # Get the endpoint URL from the request and replace any path keys with their corresponding values
        endpoint_url: str = api_request.get_api_endpoint_url()

        for py_field_name, api_field_name in list(specified_paths.items()):
            # Replace the path key with the value from the request
            # IE: /v2/ratings/{id} -> /v2/ratings/123
            _endpoint_url = endpoint_url
            endpoint_url = endpoint_url.format_map({api_field_name: str(getattr(api_request, py_field_name))})
            if _endpoint_url == endpoint_url:
                specified_paths.pop(py_field_name)

        # Extract any extra header fields and the request body data from the request
        extra_header_keys: list[str] = api_request.get_header_fields()
        extra_query_keys: list[str] = api_request.get_query_fields()

        request_params_dict: dict[str, Any] = {}
        request_headers_dict: dict[str, Any] = {}
        request_queries_dict: dict[str, Any] = {}

        # Extract all fields from the request which are not specified headers, paths, or queries
        # Note: __dict__ allows access to *all* attributes of an instance
        for request_key, request_value in vars(api_request).items():
            if request_value is None:
                continue
            if request_key in specified_paths:
                continue
            if request_key in specified_headers:
                request_headers_dict[specified_headers[request_key]] = request_value
                continue
            if request_key in extra_header_keys:
                # Remove any trailing underscores from the key as they are used to avoid python keyword conflicts
                api_name = request_key if not request_key.endswith("_") else request_key[:-1]
                specified_headers[request_key] = api_name
                request_headers_dict[api_name] = request_value

                continue
            if request_key in specified_queries:
                request_queries_dict[specified_queries[request_key]] = request_value
                continue

            if request_key in extra_query_keys:
                # Remove any trailing underscores from the key as they are used to avoid python keyword conflicts
                api_name = request_key if not request_key.endswith("_") else request_key[:-1]
                specified_queries[request_key] = api_name
                request_queries_dict[api_name] = request_value
                continue

            request_params_dict[request_key] = request_value

        # Exclude specified fields from the request (payload) body data as they were used elsewhere
        all_fields_to_exclude_from_body = set(
            list(specified_headers.keys())
            + list(specified_paths.keys())
            + list(specified_queries.keys())
            + extra_header_keys,
        )

        # Convert the request body data to a dictionary
        request_body_data_dict: dict[str, Any] | None = api_request.model_dump(
            by_alias=True,
            exclude_none=True,
            exclude_unset=True,
            exclude=all_fields_to_exclude_from_body,
        )

        if not request_body_data_dict:
            # This is explicitly set to None for clarity that it is unspecified
            # i.e., and empty body is not the same as an unspecified body
            request_body_data_dict = None

        # Add the API key to the request headers if the request is authenticated and an API key is provided
        if isinstance(api_request, APIKeyAllowedInRequestMixin) and "apikey" not in request_headers_dict:
            request_headers_dict["apikey"] = self._apikey

        return ParsedRawRequest(
            endpoint_no_query=endpoint_url,
            request_headers=request_headers_dict,
            request_queries=request_queries_dict,
            request_params=request_params_dict,
            request_body=request_body_data_dict,
        )

    def _after_request_handling(
        self,
        *,
        raw_response_json: dict[str, Any],
        returned_status_code: int,
        expected_response_type: type[HordeResponseTypeVar],
    ) -> HordeResponseTypeVar | RequestErrorResponse:
        # If requests response is a failure code, see if a `message` key exists in the response.
        # If so, return a RequestErrorResponse
        if returned_status_code >= 400:
            if "errors" in raw_response_json:
                raise AIHordePayloadValidationError(
                    raw_response_json.get("errors", ""),
                    raw_response_json.get("message", ""),
                )

            try:
                return RequestErrorResponse(**raw_response_json)
            except ValidationError:
                return RequestErrorResponse(
                    message="The API returned an error we didn't recognize! See `object_data` for the raw response.",
                    rc=raw_response_json.get("rc", returned_status_code),
                    object_data={"raw_response": raw_response_json},
                )

        handled_response: HordeResponseTypeVar | RequestErrorResponse | None = None
        try:
            parsed_response = expected_response_type.model_validate(raw_response_json)
            if isinstance(parsed_response, expected_response_type):
                handled_response = parsed_response
            else:
                handled_response = RequestErrorResponse(
                    message="The response type doesn't match expected one! See `object_data` for the raw response.",
                    object_data={"raw_response": raw_response_json},
                )
        except ValidationError as e:
            if not isinstance(handled_response, expected_response_type):  # pragma: no cover
                error_response = RequestErrorResponse(
                    message="The response type doesn't match expected one! See `object_data` for the raw response.",
                    object_data={"exception": e, "raw_response": raw_response_json},
                )
                handled_response = error_response

        return handled_response


class GenericHordeAPIManualClient(BaseHordeAPIClient):
    """Interfaces with any flask API the horde provides, but provides little error handling.

    This is the no-frills version of the client if you want to have more control over the request process.
    """

    def submit_request(
        self,
        api_request: HordeRequest,
        expected_response_type: type[HordeResponseTypeVar],
    ) -> HordeResponseTypeVar | RequestErrorResponse:
        """Submit a request to the API and return the response.

        If you are wondering why `expected_response_type` is a parameter, it is because the API may return different
        responses depending on the payload or other factors. It is up to you to determine which response type you
        expect, and pass it in here.

        Args:
            api_request (HordeRequest): The request to submit.
            expected_response_type (type[HordeResponse]): The expected response type.

        Returns:
            HordeResponseTypeVar | RequestErrorResponse: The response from the API.
        """
        http_method_name = api_request.get_http_method()

        parsed_request = self._validate_and_prepare_request(api_request)

        raw_response: requests.Response | None = None

        if http_method_name == HTTPMethod.GET:
            if parsed_request.request_body is not None:
                raise RuntimeError(
                    "GET requests cannot have a body! This may mean you forgot to override `get_header_fields()` "
                    "or perhaps you may need to define a `metadata.py` module or entry in it for your API.",
                )
            raw_response = requests.get(
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                allow_redirects=True,
            )
        elif http_method_name == HTTPMethod.POST:
            raw_response = requests.post(
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                json=parsed_request.request_body,
                allow_redirects=True,
            )
        elif http_method_name == HTTPMethod.PUT:
            raw_response = requests.put(
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                json=parsed_request.request_body,
                allow_redirects=True,
            )
        elif http_method_name == HTTPMethod.PATCH:
            raw_response = requests.patch(
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                json=parsed_request.request_body,
                allow_redirects=True,
            )
        elif http_method_name == HTTPMethod.DELETE:
            raw_response = requests.delete(
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                json=parsed_request.request_body,
                allow_redirects=True,
            )
        else:
            raise RuntimeError(f"Unknown HTTP method: {http_method_name}")

        return self._after_request_handling(
            raw_response_json=raw_response.json(),
            returned_status_code=raw_response.status_code,
            expected_response_type=expected_response_type,
        )


class GenericAsyncHordeAPIManualClient(BaseHordeAPIClient):
    """Interfaces with any flask API the horde provides, but provides little error handling.

    See the official docs for examples and some words of warning.
    """

    _aiohttp_session: aiohttp.ClientSession

    def __init__(  # noqa: D107
        self,
        *,
        apikey: str | None = None,
        aiohttp_session: aiohttp.ClientSession,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
        ssl_context: SSLContext = _default_sslcontext,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        super().__init__(
            apikey=apikey,
            header_fields=header_fields,
            path_fields=path_fields,
            query_fields=query_fields,
            accept_types=accept_types,
            **kwargs,
        )
        self._aiohttp_session = aiohttp_session

    async def submit_request(
        self,
        api_request: HordeRequest,
        expected_response_type: type[HordeResponseTypeVar],
    ) -> HordeResponseTypeVar | RequestErrorResponse:
        """Submit a request to the API asynchronously and return the response.

        If you are wondering why `expected_response_type` is a parameter, it is because the API may return different
        responses depending on the payload or other factors. It is up to you to determine which response type you
        expect, and pass it in here.

        Args:
            api_request (HordeRequest): The request to submit.
            expected_response_type (type[HordeResponse]): The expected response type.

        Returns:
            HordeResponse | RequestErrorResponse: The response from the API.

        Raises:
            ClientResponseError: If a network problem occurred.
        """
        http_method_name = api_request.get_http_method()

        parsed_request = self._validate_and_prepare_request(api_request)

        raw_response_json: dict[str, Any] = {}
        response_status: int = 599

        if not self._aiohttp_session:
            raise RuntimeError("No aiohttp session was provided but an async method was called!")

        async with (
            self._aiohttp_session.request(
                http_method_name.value,
                parsed_request.endpoint_no_query,
                headers=parsed_request.request_headers,
                params=parsed_request.request_queries,
                json=parsed_request.request_body,
                allow_redirects=True,
                ssl=self._ssl_context,
            ) as response,
        ):
            raw_response_json = await response.json()
            response_status = response.status

        return self._after_request_handling(
            raw_response_json=raw_response_json,
            returned_status_code=response_status,
            expected_response_type=expected_response_type,
        )


class GenericHordeAPISession(GenericHordeAPIManualClient):
    """A client which can perform arbitrary horde API requests, but also keeps track of responses requiring follow up.

    Use `submit_request` for synchronous requests, and `submit_request` for asynchronous
    requests.

    This typically is the better class if you do not want to worry about handling any outstanding requests
    if your program crashes. This would be the case with most non-atomic requests, such as generation requests
    or anything labeled as `async` on the API.
    """

    _pending_follow_ups: list[tuple[HordeRequest, HordeResponse, list[HordeRequest] | None]]
    """A `list` of 3-tuples containing the request, response, and a clean-up request for any requests which might need
    it."""

    def __init__(
        self,
        *,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Initialize a new `GenericHordeAPISession` instance."""
        super().__init__(
            header_fields=header_fields,
            path_fields=path_fields,
            query_fields=query_fields,
            accept_types=accept_types,
        )
        self._pending_follow_ups = []

    def submit_request(  # noqa: D102
        self,
        api_request: HordeRequest,
        expected_response_type: type[HordeResponseTypeVar],
    ) -> HordeResponseTypeVar | RequestErrorResponse:
        response = super().submit_request(api_request, expected_response_type)

        if isinstance(response, ResponseRequiringFollowUpMixin):
            self._pending_follow_ups.append(
                (api_request, response, response.get_follow_up_failure_cleanup_request()),
            )
        else:  # TODO: This whole else is duplicated in the asyncio version of this class. Refactor it out.
            # Check if this request is a cleanup or follow up request for a prior request
            # Loop through each item in self._pending_follow_ups list
            for index, (prior_request, prior_response, cleanup_request) in enumerate(self._pending_follow_ups):
                if cleanup_request is not None and api_request in cleanup_request:
                    if not isinstance(response, RequestErrorResponse):
                        self._pending_follow_ups.pop(index)
                    else:
                        logger.error(
                            "This api request would have followed up on an operation which requires it, but it "
                            "failed!",
                        )
                        logger.error(f"Request: {api_request.log_safe_model_dump()}")
                        logger.error(f"Response: {response}")
                    break

                if not isinstance(prior_response, ResponseRequiringFollowUpMixin):
                    continue

                # If the response isn't a final follow-up, we don't need to do anything else.
                if isinstance(response, ResponseWithProgressMixin):
                    if not response.is_final_follow_up():
                        continue
                    if not prior_request.get_requires_follow_up():
                        continue

                    # See if the current api_request is a follow-up to the prior_request
                    if not prior_response.does_target_request_follow_up(api_request):
                        continue

                    # Check if the current response indicates that the job is complete
                    if response.is_job_complete(prior_request.get_number_of_results_expected()):
                        # Remove the current item from the _pending_follow_ups list
                        # This is for the benefit of the __exit__ method (context management)
                        self._pending_follow_ups.pop(index)
                        break
                else:
                    if not prior_response.does_target_request_follow_up(api_request):
                        continue

                    self._pending_follow_ups.pop(index)
                    break

        return response

    def __enter__(self) -> GenericHordeAPISession:
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type: type[BaseException], exc_val: Exception, exc_tb: object) -> bool:
        """Exit the context manager."""
        # If there was no exception, return True.
        if exc_type is None:
            return True

        # Log the error
        logger.error(f"Error: {exc_val}, Type: {exc_type}")

        # Show the traceback if there is one
        if exc_tb and hasattr(exc_tb, "print_exc"):
            exc_tb.print_exc()

        # If there are no pending follow-up requests, return True if the exception was a CancelledError.
        if not self._pending_follow_ups:
            return exc_type is asyncio.exceptions.CancelledError

        # Handle each pending follow-up request.
        all_handled = True
        for request_to_follow_up, response_to_follow_up, cleanup_request in self._pending_follow_ups:
            handled = self._handle_exit(request_to_follow_up, response_to_follow_up, cleanup_request)
            all_handled = all_handled and handled

        # Check if the exception was a CancelledError.
        is_cancelled = exc_type is asyncio.exceptions.CancelledError

        # If we cancelled the task and everything cleaned up ok, we don't want to raise an exception.
        return all_handled and is_cancelled  # Returns True if everything was handled and we cancelled the task.

    def _handle_exit(
        self,
        request_to_follow_up: HordeRequest,  # The request that is ending prematurely.
        response_to_follow_up: HordeResponse,  # The response to the request that is ending prematurely.
        cleanup_requests: list[HordeRequest] | None,  # The request to clean up after the premature ending, if any.
    ) -> bool:
        """Send any follow up requests needed to clean up after a request which is ending prematurely.

        Args:
            request_to_follow_up (HordeRequest): The request which is ending prematurely.
            response_to_follow_up (HordeResponse): The response to the request which is ending prematurely.
            cleanup_requests (HordeRequest | None): The request to clean up after the premature ending, if any.

        Returns:
            bool: True if the request was handled successfully, False otherwise.
        """
        # If the response doesn't need a follow-up request, we don't need to do anything.
        if not isinstance(response_to_follow_up, ResponseRequiringFollowUpMixin):
            return True

        if response_to_follow_up.ignore_failure():
            return True

        # The message to log if an exception occurs.
        message = (
            "An exception occurred while trying to create a recovery request! "
            "This is a bug in the SDK, please report it!"
        )

        # If we get here, we need to create a follow-up request to clean up after the premature ending.
        # If no cleanup request was provided, log a warning and return True, which means it was 'handled'.
        # in reality, the class was defined incorrectly, but we can't do anything about that.
        if cleanup_requests is None:
            logger.error("No recovery request(s) was/were provided, but the class said it needed them!")
            return True

        # Submit the cleanup request and log the results.
        logger.debug("Recovery request created!")
        logger.debug(f"{cleanup_requests}")

        for cleanup_request in cleanup_requests:
            try:
                recovery_response = self.submit_request(
                    cleanup_request,
                    cleanup_request.get_default_success_response_type(),
                )
                logger.debug("Recovery request submitted!")
                logger.debug(f"Recovery response: {recovery_response}")
            # If we don't blanket catch here, other requests could end up dangling
            except Exception as e:
                # If an exception occurred, log an error and return False.
                logger.exception(e)
                logger.critical(message)
                logger.critical(f"{request_to_follow_up.log_safe_model_dump()}")
                return False
        # Return True to indicate that the request was handled successfully.
        return True


class GenericAsyncHordeAPISession(GenericAsyncHordeAPIManualClient):
    """A client which can perform arbitrary horde API requests asynchronously, but also keeps track of responses."""

    _awaiting_requests: list[HordeRequest]
    """A `list` of `HordeRequest` instances which are being `await`ed on asynchronously."""
    _awaiting_requests_lock: asyncio.Lock = asyncio.Lock()

    _pending_follow_ups: list[tuple[HordeRequest, HordeResponse, list[HordeRequest] | None]]
    """A `list` of 3-tuples containing the request, response, and a clean-up request for any requests which might need
    it."""
    _pending_follow_ups_lock: asyncio.Lock = asyncio.Lock()

    def __init__(  # noqa: D107
        self,
        aiohttp_session: aiohttp.ClientSession,
        *,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
        ssl_context: SSLContext = _default_sslcontext,
    ) -> None:
        super().__init__(
            aiohttp_session=aiohttp_session,
            header_fields=header_fields,
            path_fields=path_fields,
            query_fields=query_fields,
            accept_types=accept_types,
            ssl_context=ssl_context,
        )
        self._pending_follow_ups = []
        self._awaiting_requests = []

    @override
    async def submit_request(
        self,
        api_request: HordeRequest,
        expected_response_type: type[HordeResponseTypeVar],
    ) -> HordeResponseTypeVar | RequestErrorResponse:
        # Add the request to the list of awaiting requests.

        async with self._awaiting_requests_lock:
            self._awaiting_requests.append(api_request)

        # Submit the request to the API and get the response.
        response = await super().submit_request(api_request, expected_response_type)

        # Remove the request from the list of awaiting requests.
        async with self._awaiting_requests_lock, self._pending_follow_ups_lock:
            self._awaiting_requests.remove(api_request)

            # Check if the response requires a follow-up request.
            if isinstance(response, ResponseRequiringFollowUpMixin):
                # Add the follow-up request to the list of pending follow-ups.
                if not response.ignore_failure():
                    self._pending_follow_ups.append(
                        (api_request, response, response.get_follow_up_failure_cleanup_request()),
                    )

            else:
                # Check if this request is a cleanup or follow up request for a prior request

                # Loop through each item in self._pending_follow_ups list
                for index, (prior_request, prior_response, cleanup_request) in enumerate(self._pending_follow_ups):
                    if cleanup_request is not None and api_request in cleanup_request:
                        if not isinstance(response, RequestErrorResponse):
                            self._pending_follow_ups.pop(index)
                            break

                        logger.error(
                            "This api request would have followed up on an operation which requires it, but it "
                            "failed!",
                        )
                        logger.error(f"Request: {api_request.log_safe_model_dump()}")
                        logger.error(f"Response: {response.log_safe_model_dump()}")
                        break

                    if not isinstance(prior_response, ResponseRequiringFollowUpMixin):
                        continue

                    # If the response isn't a final follow-up, we don't need to do anything else.
                    if isinstance(response, ResponseWithProgressMixin):
                        if not response.is_final_follow_up():
                            continue
                        if not prior_request.get_requires_follow_up():
                            continue

                        # See if the current api_request is a follow-up to the prior_request
                        if not prior_response.does_target_request_follow_up(api_request):
                            continue

                        # Check if the current response indicates that the job is complete
                        if response.is_job_complete(prior_request.get_number_of_results_expected()):
                            # Remove the current item from the _pending_follow_ups list
                            # This is for the benefit of the __exit__ method (context management)
                            self._pending_follow_ups.pop(index)
                            break
                    else:
                        if not prior_response.does_target_request_follow_up(api_request):
                            continue

                        self._pending_follow_ups.pop(index)
                        break

        # Return the response from the API.
        return response

    async def __aenter__(self) -> GenericAsyncHordeAPISession:
        """Enter the context manager asynchronously."""
        return self

    async def __aexit__(self, exc_type: type[BaseException], exc_val: Exception, exc_tb: object) -> bool:
        """Exit the context manager asynchronously."""
        # If there are any requests that haven't been returned yet, log a warning.
        if self._awaiting_requests:
            logger.warning(
                "This session was used to submit asynchronous requests, but the context manager was exited "
                "before all requests were returned! This may result in requests not being handled properly.",
            )
            # Log each unhandled request.
            for request in self._awaiting_requests:
                logger.warning(f"Request Unhandled: {request.log_safe_model_dump()}")

        # Log the error if there was one.
        if exc_type:
            logger.error(f"Error: {exc_val}, Type: {exc_type}")

        # Show the traceback if there is one
        if exc_tb and hasattr(exc_tb, "print_exc"):
            exc_tb.print_exc()

        # If there are no pending follow-up requests, return True if the exception was a CancelledError.
        if not self._pending_follow_ups:
            return exc_type is asyncio.exceptions.CancelledError

        try:
            # Handle each pending follow-up request asynchronously.
            await asyncio.gather(
                *[
                    self._handle_exit_async(request_to_follow_up, response_to_follow_up, cleanup_request)
                    for request_to_follow_up, response_to_follow_up, cleanup_request in self._pending_follow_ups
                ],
            )

            # Return True if everything was handled and the task was cancelled deliberately,
            # False otherwise (which will reraise the exception)
            return exc_type is asyncio.exceptions.CancelledError
        except Exception as e:
            # If an exception occurred while handling the follow-up requests, log an error and return False.
            logger.exception(e)
            return False

    async def _handle_exit_async(
        self,
        request_to_follow_up: HordeRequest,  # The request that is ending prematurely.
        response_to_follow_up: HordeResponse,  # The response to the request that is ending prematurely.
        cleanup_requests: list[HordeRequest] | None,  # The request to clean up after the premature ending, if any.
    ) -> bool:
        """Send any follow up requests needed to clean up after a request which is ending prematurely.

        Args:
            request_to_follow_up (HordeRequest): The request which is ending prematurely.
            response_to_follow_up (HordeResponse): The response to the request which is ending prematurely.
            cleanup_requests (HordeRequest | None): The request to clean up after the premature ending, if any.

        Returns:
            bool: True if the request was handled successfully, False otherwise.
        """
        # If the response doesn't need a follow-up request, we don't need to do anything.
        if not isinstance(response_to_follow_up, ResponseRequiringFollowUpMixin):
            return True

        if response_to_follow_up.ignore_failure():
            return True

        # If we get here, we need to create a follow-up request to clean up after the premature ending.
        message = (
            "An exception occurred while trying to create a recovery request! "
            "This is a bug in the SDK, please report it!"
        )
        # If we get here, we need to create a follow-up request to clean up after the premature ending.
        # If no cleanup request was provided, log a warning and return True, which means it was 'handled'.
        # in reality, the class was defined incorrectly, but we can't do anything about that.
        if cleanup_requests is None:
            logger.debug("No recovery request(s) was/were provided, but the class said it needed one!")
            return True

        # Submit the cleanup request and log the results.

        try:
            # Submit all cleanup requests concurrently using asyncio.gather.
            cleanup_responses = await asyncio.gather(
                *[
                    self.submit_request(
                        cleanup_request,
                        cleanup_request.get_default_success_response_type(),
                    )
                    for cleanup_request in cleanup_requests
                ],
                return_exceptions=True,
            )

            # Log the results of each cleanup request.
            for i, cleanup_response in enumerate(cleanup_responses):
                if isinstance(cleanup_response, Exception):
                    logger.error(f"Recovery request {i+1} failed!")

                logger.info(f"Recovery request {i+1} submitted!")
                logger.debug(f"Recovery request {i+1}: {cleanup_requests[i].log_safe_model_dump()}")
                logger.debug(f"Recovery response {i+1}: {cleanup_response}")

            # Return True to indicate that all requests were handled successfully.
            return True

        except Exception as e:  # If we don't blanket catch here, other requests could end up dangling
            # If an exception occurred, log an error and return False.
            logger.exception(e)
            logger.critical(message)
            logger.critical(f"{request_to_follow_up.log_safe_model_dump()}")
            return False
