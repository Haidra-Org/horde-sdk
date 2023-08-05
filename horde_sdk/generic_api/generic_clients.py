"""The API client which can perform arbitrary horde API requests."""

from __future__ import annotations

import asyncio
from typing import TypeVar

import aiohttp
import requests
from loguru import logger
from pydantic import BaseModel, ValidationError
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    BaseRequest,
    BaseResponse,
    MayUseAPIKeyInRequestMixin,
    RequestErrorResponse,
    ResponseNeedingFollowUpMixin,
)
from horde_sdk.generic_api.consts import ANON_API_KEY
from horde_sdk.generic_api.metadata import (
    GenericAcceptTypes,
    GenericHeaderFields,
    GenericPathFields,
    GenericQueryFields,
)


class _ParsedRequest(BaseModel):
    endpoint_no_query: str
    """The endpoint URL without any query parameters."""
    request_headers: dict
    """The headers to be sent with the request."""
    request_queries: dict
    """The query parameters to be sent with the request."""
    request_params: dict
    """The path parameters to be sent with the request."""
    request_body: dict | None
    """The body to be sent with the request, or `None` if no body should be sent."""


HordeRequest = TypeVar("HordeRequest", bound=BaseRequest)
"""TypeVar for the request type."""
HordeResponse = TypeVar("HordeResponse", bound=BaseResponse)
"""TypeVar for the response type."""


class GenericHordeAPIManualClient:
    """Interfaces with any flask API the horde provides, but provides little error handling.

    This is the no-frills, simple version of the client if you want to have more control over the request process.
    """

    # region
    _aiohttp_session: aiohttp.ClientSession | None
    _session_create_lock: asyncio.Lock = asyncio.Lock()
    """A lock to ensure that only one session is created"""

    _apikey: str | None

    _header_data_keys: type[GenericHeaderFields] = GenericHeaderFields
    """A list of all fields which would appear in the API request header."""
    _path_data_keys: type[GenericPathFields] = GenericPathFields
    """A list of all fields which would appear in any API action path (appearing before the '?' as part of the URL)"""
    _query_data_keys: type[GenericQueryFields] = GenericQueryFields
    """A list of all fields which would appear in any API action query (appearing after the '?')"""

    _accept_types: type[GenericAcceptTypes] = GenericAcceptTypes
    """A list of all valid values for the header key 'accept'."""

    # endregion

    def __init__(
        self,
        *,
        apikey: str | None = None,
        aiohttp_session: aiohttp.ClientSession | None = None,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Initializes a new `GenericHordeAPIClient` instance.

        Args:
            apikey (str, optional): The API key to use for authenticated requests. Defaults to None, which will use the
            anonymous API key.
            aiohttp_session (aiohttp.ClientSession, optional): Pass this to use an existing aiohttp session.

            header_fields (type[GenericHeaderFields], optional): Pass this to define the API's Header fields.
            Defaults to GenericHeaderFields.

            path_fields (type[GenericPathFields], optional): Pass this to define the API's URL path fields.
            Defaults to GenericPathFields.

            query_fields (type[GenericQueryFields], optional): Pass this to define the API's URL query fields.
            Defaults to GenericQueryFields.

            accept_types (type[GenericAcceptTypes], optional): Pass this to define the API's accept types.
            Defaults to GenericAcceptTypes.

        Raises:
            TypeError: If any of the passed types are not subclasses of their respective `Generic*` class.
        """
        self._aiohttp_session = aiohttp_session

        self._apikey = apikey

        if not self._apikey:
            self._apikey = ANON_API_KEY

        if not issubclass(header_fields, GenericHeaderFields):
            raise TypeError("`headerData` must be of type `GenericHeaderData` or a subclass of it!")
        if not issubclass(path_fields, GenericPathFields):
            raise TypeError("`pathData` must be of type `GenericPathData` or a subclass of it!")
        if not issubclass(accept_types, GenericAcceptTypes):
            raise TypeError("`acceptTypes` must be of type `GenericAcceptTypes` or a subclass of it!")
        if not issubclass(query_fields, GenericQueryFields):
            raise TypeError("`queryData` must be of type `GenericQueryData` or a subclass of it!")

        self._header_data_keys = header_fields
        self._path_data_keys = path_fields
        self._query_data_keys = query_fields
        self._accept_types = accept_types

    def _validate_and_prepare_request(self, api_request: BaseRequest) -> _ParsedRequest:
        """Validates the given `api_request` and returns a `_ParsedRequest` instance with the data to be sent.

        This method converts a `BaseRequest` instance into the data needed to make a request with `requests`. It
        validates the request and extracts the specified headers, paths, and queries from the request. It also extracts
        any extra header fields and the request body data from the request. Finally, it returns a `_ParsedRequest`
        instance with the extracted data.

        Args:
            api_request (BaseRequest): The `BaseRequest` instance to be validated and prepared.

        Returns:
            _ParsedRequest: A `_ParsedRequest` instance with the extracted data to be sent in the request.

        Raises:
            TypeError: If `api_request` is not of type `BaseRequest` or a subclass of it.
        """
        if not issubclass(api_request.__class__, BaseRequest):
            raise TypeError("`request` must be of type `BaseRequest` or a subclass of it!")

        # Define a helper function to extract specified data keys from the request
        def get_specified_data_keys(data_keys: type[StrEnum], api_request: BaseRequest) -> dict[str, str]:
            """Extracts the specified data keys from the request and returns them as a dictionary."""
            return {
                py_field_name: str(api_field_name)
                for py_field_name, api_field_name in data_keys._member_map_.items()
                if hasattr(api_request, py_field_name) and getattr(api_request, py_field_name) is not None
            }

        # Extract the specified headers, paths, and queries from the request, so they don't end up in
        # a request (payload) body
        specified_headers = get_specified_data_keys(self._header_data_keys, api_request)
        specified_paths = get_specified_data_keys(self._path_data_keys, api_request)
        specified_queries = get_specified_data_keys(self._query_data_keys, api_request)

        # Get the endpoint URL from the request and replace any path keys with their corresponding values
        endpoint_url: str = api_request.get_api_endpoint_url()

        for py_field_name, api_field_name in specified_paths.items():
            # Replace the path key with the value from the request
            # IE: /v2/ratings/{id} -> /v2/ratings/123
            endpoint_url = endpoint_url.format_map({api_field_name: str(getattr(api_request, py_field_name))})

        # Extract any extra header fields and the request body data from the request
        extra_header_keys: list[str] = api_request.get_header_fields()

        request_params_dict: dict[str, object] = {}
        request_headers_dict: dict[str, object] = {}
        request_queries_dict: dict[str, object] = {}

        # Extract all fields from the request which are not specified headers, paths, or queries
        # Note: __dict__ allows access to all attributes of an instance
        for request_key, request_value in api_request.__dict__.items():
            if request_key in specified_paths:
                continue
            if request_key in specified_headers:
                request_headers_dict[request_key] = request_value
                continue
            if request_key in extra_header_keys:
                # Remove any trailing underscores from the key as they are used to avoid python keyword conflicts
                api_name = request_key if not request_key.endswith("_") else request_key[:-1]
                specified_headers[request_key] = api_name
                request_headers_dict[request_key] = request_value

                continue
            if request_key in specified_queries:
                request_queries_dict[request_key] = request_value
                continue

            request_params_dict[request_key] = request_value

        # Exclude specified fields from the request (payload) body data
        all_fields_to_exclude_from_body = set(
            list(specified_headers.keys())
            + list(specified_paths.keys())
            + list(specified_queries.keys())
            + extra_header_keys,
        )

        # Convert the request body data to a dictionary
        request_body_data_dict: dict | None = api_request.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude=all_fields_to_exclude_from_body,
        )

        if request_body_data_dict == {}:
            request_body_data_dict = None

        # Add the API key to the request headers if the request is authenticated and an API key is provided
        if isinstance(api_request, MayUseAPIKeyInRequestMixin) and self._apikey:
            request_headers_dict["apikey"] = self._apikey
            logger.debug("No API key was provided, using the anonymous API key.")

        return _ParsedRequest(
            endpoint_no_query=endpoint_url,
            request_headers=request_headers_dict,
            request_queries=request_queries_dict,
            request_params=request_params_dict,
            request_body=request_body_data_dict,
        )

    def _after_request_handling(
        self,
        *,
        api_request: BaseRequest,
        raw_response_json: dict,
        returned_status_code: int,
        expected_response_type: type[HordeResponse],
    ) -> HordeResponse | RequestErrorResponse:
        # If requests response is a failure code, see if a `message` key exists in the response.
        # If so, return a RequestErrorResponse
        if returned_status_code >= 400:
            if len(raw_response_json) == 1 and "message" in raw_response_json:
                return RequestErrorResponse(**raw_response_json)

            raise RuntimeError(
                (
                    "Received a non-200 response code, but no `message` key was found "
                    f"in the response: {raw_response_json}. Something may be wrong with the API itself."
                ),
            )

        handled_response: HordeResponse | RequestErrorResponse | None = None
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
            if not isinstance(handled_response, expected_response_type):
                error_response = RequestErrorResponse(
                    message="The response type doesn't match expected one! See `object_data` for the raw response.",
                    object_data={"exception": e, "raw_response": raw_response_json},
                )
                handled_response = error_response

        return handled_response

    def submit_request(
        self,
        api_request: BaseRequest,
        expected_response_type: type[HordeResponse],
    ) -> HordeResponse | RequestErrorResponse:
        """Submit a request to the API and return the response.

        If you are wondering why `expected_response_type` is a parameter, it is because the API may return different
        responses depending on the payload or other factors. It is up to you to determine which response type you
        expect, and pass it in here.

        Args:
            api_request (BaseRequest): The request to submit.
            expected_response_type (type[HordeResponse]): The expected response type.

        Returns:
            HordeResponse | RequestErrorResponse: The response from the API.
        """
        http_method_name = api_request.get_http_method()

        parsed_request = self._validate_and_prepare_request(api_request)

        raw_response: requests.Response | None = None

        if http_method_name == HTTPMethod.GET:
            if parsed_request.request_body is not None:
                raise RuntimeError(
                    "GET requests cannot have a body! This may mean you forgot to override `get_header_fields()`",
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
            api_request=api_request,
            raw_response_json=raw_response.json(),
            returned_status_code=raw_response.status_code,
            expected_response_type=expected_response_type,
        )

    async def async_submit_request(
        self,
        api_request: BaseRequest,
        expected_response_type: type[HordeResponse],
    ) -> HordeResponse | RequestErrorResponse:
        """Submit a request to the API asynchronously and return the response.

        If you are wondering why `expected_response_type` is a parameter, it is because the API may return different
        responses depending on the payload or other factors. It is up to you to determine which response type you
        expect, and pass it in here.

        Args:
            api_request (BaseRequest): The request to submit.
            expected_response_type (type[HordeResponse]): The expected response type.

        Returns:
            HordeResponse | RequestErrorResponse: The response from the API.

        Raises:
            ClientResponseError: If a network problem occurred.
        """
        http_method_name = api_request.get_http_method()

        parsed_request = self._validate_and_prepare_request(api_request)

        raw_response_json: dict = {}
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
            ) as response,
        ):
            raw_response_json = await response.json()
            response_status = response.status

        return self._after_request_handling(
            api_request=api_request,
            raw_response_json=raw_response_json,
            returned_status_code=response_status,
            expected_response_type=expected_response_type,
        )


class GenericHordeAPISession(GenericHordeAPIManualClient):
    """A client which can perform arbitrary horde API requests, but also keeps track of reponses requiring follow up.

    Use `submit_request` for synchronous requests, and `async_submit_request` for asynchronous
    requests.

    This typically is the better class if you do not want to worry about handling any outstanding requests
    if your program crashes. This would be the case with most non-atomic requests, such as generation requests
    or anything labeled as `async` on the API.
    """

    _awaiting_requests: list[BaseRequest]
    """A `list` of `BaseRequest` instances which are being `await`ed on asynchronously."""
    _awaiting_requests_lock: asyncio.Lock = asyncio.Lock()

    _pending_follow_ups: list[tuple[BaseRequest, BaseResponse, BaseRequest | None]]
    """A `list` of 3-tuples containing the request, response, and a clean-up request for any requests which might need
    it."""
    _pending_follow_ups_lock: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        *,
        aiohttp_session: aiohttp.ClientSession | None,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Initializes a new `GenericHordeAPISession` instance."""
        super().__init__(
            aiohttp_session=aiohttp_session,
            header_fields=header_fields,
            path_fields=path_fields,
            query_fields=query_fields,
            accept_types=accept_types,
        )
        self._awaiting_requests = []
        self._pending_follow_ups = []

    @override
    def submit_request(
        self,
        api_request: BaseRequest,
        expected_response_type: type[HordeResponse],
    ) -> HordeResponse | RequestErrorResponse:
        response = super().submit_request(api_request, expected_response_type)

        for index, (_, _, cleanup_request) in enumerate(self._pending_follow_ups):
            # The response stores the reference to this cleanup request internally, so we can match by identity
            if api_request is cleanup_request:
                self._pending_follow_ups.pop(index)
                break

        if isinstance(response, ResponseNeedingFollowUpMixin):
            # Check if this request is a cleanup request for another request in self._pending_follow_ups
            # If so, remove the request from self._pending_follow_ups as its been handled

            self._pending_follow_ups.append((api_request, response, response.get_follow_up_failure_cleanup_request()))

        return response

    @override
    async def async_submit_request(
        self,
        api_request: BaseRequest,
        expected_response_type: type[HordeResponse],
    ) -> HordeResponse | RequestErrorResponse:
        async with self._awaiting_requests_lock:
            self._awaiting_requests.append(api_request)

        response = await super().async_submit_request(api_request, expected_response_type)

        async with self._awaiting_requests_lock, self._pending_follow_ups_lock:
            self._awaiting_requests.remove(api_request)

            for index, (_, _, cleanup_request) in enumerate(self._pending_follow_ups):
                # The response stores the reference to this cleanup request internally, so we can match by identity
                if api_request is cleanup_request:
                    self._pending_follow_ups.pop(index)
                    break

            if isinstance(response, ResponseNeedingFollowUpMixin):
                self._pending_follow_ups.append(
                    (api_request, response, response.get_follow_up_failure_cleanup_request()),
                )

        return response

    def __enter__(self) -> GenericHordeAPISession:
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: object) -> bool:
        """Exit the context manager."""
        if exc_type is None:
            return True

        logger.error(f"Error: {exc_val}, Type: {exc_type}, Traceback: {exc_tb}")

        if not self._pending_follow_ups:
            return exc_type is asyncio.CancelledError

        all_handled = True
        for request_to_follow_up, response_to_follow_up, cleanup_request in self._pending_follow_ups:
            handled = self._handle_exit(request_to_follow_up, response_to_follow_up, cleanup_request)
            all_handled = all_handled and handled

        is_cancelled = exc_type is asyncio.CancelledError

        # If we cancelled the task and everything cleaned up ok, we don't want to raise an exception
        return all_handled and is_cancelled  # Returns True if everything was handled and we cancelled the task

    def _handle_exit(
        self,
        request_to_follow_up: BaseRequest,
        response_to_follow_up: BaseResponse,
        cleanup_request: BaseRequest | None,
    ) -> bool:
        """Sends any follow up requests needed to clean up after a request which is ending prematurely.

        Args:
            request_to_follow_up (BaseRequest): The request which is ending prematurely.
            response_to_follow_up (BaseResponse): The response to the request which is ending prematurely.

        Returns:
            bool: True if the request was handled successfully, False otherwise.
        """
        if isinstance(response_to_follow_up, RequestErrorResponse):
            return True
        if not isinstance(response_to_follow_up, ResponseNeedingFollowUpMixin):
            return True

        message = (
            "An exception occurred while trying to create a recovery request! "
            "This is a bug in the SDK, please report it!"
        )
        try:
            if cleanup_request is None:
                logger.debug("No recovery request was provided, but the class said it needed one!")
                return True

            logger.debug("Recovery request created!")
            logger.debug(f"{cleanup_request}")
            recovery_response = self.submit_request(
                cleanup_request,
                cleanup_request.get_success_response_type(),
            )
            logger.debug("Recovery request submitted!")
            logger.debug(f"Recovery response: {recovery_response}")

            return True

        except Exception:  # If we don't blanket catch here, other requests could end up dangling
            logger.critical(message)
            logger.critical(f"{request_to_follow_up}")
            return False

    async def __aenter__(self) -> GenericHordeAPISession:
        """Enter the context manager asynchronously."""
        return self

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: object) -> bool:
        """Exit the context manager asynchronously."""

        if self._awaiting_requests:
            logger.warning(
                (
                    "This session was used to submit asynchronous requests, but the context manager was exited "
                    "before all requests were returned! This may result in requests not being handled properly."
                ),
            )
            for request in self._awaiting_requests:
                logger.warning(f"Request Unhandled: {request}")

        if exc_type is not None:
            logger.debug(f"Error: {exc_val}, Type: {exc_type}, Traceback: {exc_tb}")

        if not self._pending_follow_ups:
            return exc_type is asyncio.CancelledError

        try:
            await asyncio.gather(
                *[
                    self._handle_exit_async(request_to_follow_up, response_to_follow_up, cleanup_request)
                    for request_to_follow_up, response_to_follow_up, cleanup_request in self._pending_follow_ups
                ],
            )

            # Return True if everything was handled and the task was cancelled deliberately,
            # False otherwise (which will reraise the exception)
            return exc_type is asyncio.CancelledError
        except Exception as e:
            logger.exception(e)
            return False

    async def _handle_exit_async(
        self,
        request_to_follow_up: BaseRequest,
        response_to_follow_up: BaseResponse,
        cleanup_request: BaseRequest | None,
    ) -> bool:
        if isinstance(response_to_follow_up, RequestErrorResponse):
            return True
        if not isinstance(response_to_follow_up, ResponseNeedingFollowUpMixin):
            return True

        message = (
            "An exception occurred while trying to create a recovery request! "
            "This is a bug in the SDK, please report it!"
        )
        try:
            if cleanup_request is None:
                return True

            recovery_response = await self.async_submit_request(
                cleanup_request,
                cleanup_request.get_success_response_type(),
            )
            logger.info("Recovery request submitted!")
            logger.debug(f"Recovery response: {recovery_response}")

            return True

        except Exception as e:  # If we don't blanket catch here, other requests could end up dangling
            logger.exception(e)
            logger.critical(message)
            logger.critical(f"{request_to_follow_up}")

            return False
