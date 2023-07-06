"""The API client which can perform arbitrary horde API requests."""

import requests
from pydantic import BaseModel

from horde_sdk.generic_api._error import RequestErrorResponse
from horde_sdk.generic_api.apimodels import BaseRequest, BaseResponse
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


class GenericHordeAPIClient:
    """Interfaces with any flask API the horde provides, intended to be fairly dynamic/flexible."""

    _header_data_keys: list[str]
    """A list of all fields which would appear in the API request header."""
    _path_data_keys: list[str]
    """A list of all fields which would appear in any API action path (appearing before the '?' as part of the URL)"""
    _query_data_keys: list[str]
    """A list of all fields which would appear in any API action query (appearing after the '?')"""

    _accept_types: list[str]
    """A list of all valid values for the header key 'accept'."""

    def __init__(
        self,
        *,
        header_fields: type[GenericHeaderFields] = GenericHeaderFields,
        path_fields: type[GenericPathFields] = GenericPathFields,
        query_fields: type[GenericQueryFields] = GenericQueryFields,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Initializes a new `GenericHordeAPIClient` instance.

        Args:
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
        """ """"""
        if not issubclass(header_fields, GenericHeaderFields):
            raise TypeError("`headerData` must be of type `GenericHeaderData` or a subclass of it!")
        if not issubclass(path_fields, GenericPathFields):
            raise TypeError("`pathData` must be of type `GenericPathData` or a subclass of it!")
        if not issubclass(accept_types, GenericAcceptTypes):
            raise TypeError("`acceptTypes` must be of type `GenericAcceptTypes` or a subclass of it!")
        if not issubclass(query_fields, GenericQueryFields):
            raise TypeError("`queryData` must be of type `GenericQueryData` or a subclass of it!")

        self._header_data_keys = list(header_fields.__members__.keys())
        self._path_data_keys = list(path_fields.__members__.keys())
        self._accept_types = list(accept_types.__members__.keys())
        self._query_data_keys = list(query_fields.__members__.keys())

    def _validate_and_prepare_request(self, api_request: BaseRequest) -> _ParsedRequest:
        """Validates the given `api_request` and returns a `_ParsedRequest` instance with the data to be sent.

        The thrust of the method is to convert a `BaseRequest` instance into the data needed to make a request with
        `requests`.
        """
        if not issubclass(api_request.__class__, BaseRequest):
            raise TypeError("`request` must be of type `BaseRequest` or a subclass of it!")

        specified_header_keys = [
            attr
            for attr in self._header_data_keys
            if hasattr(api_request, attr) and getattr(api_request, attr) is not None
        ]
        specified_path_keys = [
            attr
            for attr in self._path_data_keys
            if hasattr(api_request, attr) and getattr(api_request, attr) is not None
        ]
        specified_query_keys = [
            attr
            for attr in self._query_data_keys
            if hasattr(api_request, attr) and getattr(api_request, attr) is not None
        ]

        endpoint_no_query: str = api_request.get_endpoint_url()

        for pathKey in specified_path_keys:
            endpoint_no_query = endpoint_no_query.format_map({pathKey: str(getattr(api_request, pathKey))})

        request_params_dict = {}
        request_headers_dict = {}
        request_queries_dict = {}
        for key, value in api_request.__dict__.items():
            if key in specified_path_keys:
                continue
            if key in specified_header_keys:
                request_headers_dict[key] = value
                continue
            if key in specified_query_keys:
                request_queries_dict[key] = value
                continue

            request_params_dict[key] = value

        all_fields_to_exclude_from_body = set(specified_header_keys + specified_path_keys + specified_query_keys)
        request_body_data_dict: dict | None = api_request.model_dump(
            exclude_none=True,
            exclude_unset=True,
            exclude=all_fields_to_exclude_from_body,
        )

        if request_body_data_dict == {}:
            request_body_data_dict = None

        return _ParsedRequest(
            endpoint_no_query=endpoint_no_query,
            request_headers=request_headers_dict,
            request_queries=request_queries_dict,
            request_params=request_params_dict,
            request_body=request_body_data_dict,
        )

    def _after_request_handling(
        self,
        api_request: BaseRequest,
        raw_response: requests.Response,
    ) -> BaseResponse | RequestErrorResponse:
        expected_response_type = api_request.get_expected_response_type()
        raw_response_json = raw_response.json()

        # If requests response is a failure code, see if a `message` key exists in the response.
        # If so, return a RequestErrorResponse
        if raw_response.status_code >= 400:
            if len(raw_response_json) == 1 and "message" in raw_response_json:
                return RequestErrorResponse(**raw_response_json)

            raise RuntimeError(
                "Received a non-200 response code, but no `message` key was found "
                f"in the response: {raw_response_json}"
            )

        # FIXME should be something resembling error handling here
        return expected_response_type(**raw_response_json)

    def submit_request(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Submit a request to the API and return the response.

        Automatically determines the correct method to call based on calling `.get_http_method()` on the request.
        """
        http_method_name = api_request.get_http_method()._value_.lower()
        api_client_method = getattr(self, http_method_name)
        return api_client_method(api_request)

    def get(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Perform a GET request to the API."""
        parsed_request = self._validate_and_prepare_request(api_request)
        if parsed_request.request_body is not None:
            raise RuntimeError("GET requests cannot have a body!")
        raw_response = requests.get(
            parsed_request.endpoint_no_query,
            headers=parsed_request.request_headers,
            params=parsed_request.request_queries,
            allow_redirects=True,
        )

        return self._after_request_handling(api_request, raw_response)

    def post(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Perform a POST request to the API."""
        parsed_request = self._validate_and_prepare_request(api_request)
        raw_response = requests.post(
            parsed_request.endpoint_no_query,
            headers=parsed_request.request_headers,
            params=parsed_request.request_queries,
            json=parsed_request.request_body,
            allow_redirects=True,
        )

        return self._after_request_handling(api_request, raw_response)

    def put(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Perform a PUT request to the API."""
        parsed_request = self._validate_and_prepare_request(api_request)
        raw_response = requests.put(
            parsed_request.endpoint_no_query,
            headers=parsed_request.request_headers,
            params=parsed_request.request_queries,
            json=parsed_request.request_body,
            allow_redirects=True,
        )

        return self._after_request_handling(api_request, raw_response)

    def patch(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Perform a PATCH request to the API."""
        parsed_request = self._validate_and_prepare_request(api_request)
        raw_response = requests.patch(
            parsed_request.endpoint_no_query,
            headers=parsed_request.request_headers,
            params=parsed_request.request_queries,
            json=parsed_request.request_body,
            allow_redirects=True,
        )

        return self._after_request_handling(api_request, raw_response)

    def delete(self, api_request: BaseRequest) -> BaseResponse | RequestErrorResponse:
        """Perform a DELETE request to the API."""
        parsed_request = self._validate_and_prepare_request(api_request)
        raw_response = requests.delete(
            parsed_request.endpoint_no_query,
            headers=parsed_request.request_headers,
            params=parsed_request.request_queries,
            json=parsed_request.request_body,
            allow_redirects=True,
        )

        return self._after_request_handling(api_request, raw_response)
