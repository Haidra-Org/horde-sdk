"""The API client which can perform arbitrary horde API requests."""
from enum import Enum

import pydantic
import requests

from .apimodels import BaseRequest
from .metadata import GenericAcceptTypes, GenericHeaderData, GenericPathData


class GenericHordeAPIClient:
    """Interfaces with any flask API the horde provides, intended to be fairly dynamic/flexible."""

    _header_data_keys: list[str]
    """A list of all keys which would appear in the API request header."""
    _accept_types: list[str]
    """A list of all valid values for the header key 'accept'."""
    _path_data_keys: list[str]
    """A list of all keys which would appear in any API action path (appearing before the '?')"""

    def __init__(
        self,
        *,
        header_data: type[GenericHeaderData] = GenericHeaderData,
        path_data: type[GenericPathData] = GenericPathData,
        accept_types: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Instantiate a new Ratings API client."""
        if not issubclass(header_data, GenericHeaderData):
            raise TypeError("`headerData` must be of type `GenericHeaderData` or a subclass of it!")
        if not issubclass(path_data, GenericPathData):
            raise TypeError("`pathData` must be of type `GenericPathData` or a subclass of it!")
        if not issubclass(accept_types, GenericAcceptTypes):
            raise TypeError("`acceptTypes` must be of type `GenericAcceptTypes` or a subclass of it!")

        self._header_data_keys = list(header_data.__members__.keys())
        self._path_data_keys = list(path_data.__members__.keys())
        self._accept_types = list(accept_types.__members__.keys())

    def submit_request(self, api_request: BaseRequest) -> pydantic.BaseModel:
        """Handles making any horde related API request.."""
        if not issubclass(api_request.__class__, BaseRequest):
            raise TypeError("`request` must be of type `BaseRequest` or a subclass of it!")

        def remove_attrs_missing(request: BaseRequest, attributes: list[str]) -> list[str]:
            """Returns a copy of `attributes` with members removed if `request` doesn't define it, or it is `None`."""
            attrs_to_use: list[str] = list(attributes)
            for attr in attributes:
                if not hasattr(request, attr) or getattr(request, attr) is None:
                    attrs_to_use.remove(attr)
            return attrs_to_use

        # We only want to craft a payload with values which have been explicitly given.
        specified_header_keys = remove_attrs_missing(api_request, self._header_data_keys)
        specified_path_keys = remove_attrs_missing(api_request, self._path_data_keys)

        endpoint_no_query: str = api_request.get_endpoint_url()

        for pathKey in specified_path_keys:
            endpoint_no_query = endpoint_no_query.format_map({pathKey: str(getattr(api_request, pathKey))})

        request_params = {}
        request_headers = {}
        for key, value in api_request.__dict__.items():
            if key in specified_path_keys:
                continue
            if key in specified_header_keys:
                # TODO
                # Requests doesn't handle Enum as header values gracefully?
                # see https://github.com/psf/requests/issues/6159
                if isinstance(value, Enum):
                    request_headers[key] = str(value)
                else:
                    request_headers[key] = value
                continue

            request_params[key] = value

        raw_response = requests.get(endpoint_no_query, headers=request_headers, params=request_params)
        # FIXME no timeout or network error handling
        raw_response_json = raw_response.json()
        expected_response_type = api_request.get_expected_response_type()

        # FIXME should be something resembling error handling here
        return expected_response_type(**raw_response_json)
