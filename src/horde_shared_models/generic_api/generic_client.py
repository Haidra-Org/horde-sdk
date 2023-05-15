"""The API client which can perform arbitrary horde API requests."""
from enum import Enum

import pydantic
import requests

from .apimodels import BaseRequest
from .metadata import GenericAcceptTypes, GenericHeaderData, GenericPathData


class GenericHordeAPIClient:
    """Interfaces with any flask API the horde provides, intended to be fairly dynamic/flexible."""

    _headerDataKeys: list[str]
    """A list of all keys which would appear in the API request header."""
    _acceptTypes: list[str]
    """A list of all valid values for the header key 'accept'."""
    _pathDataKeys: list[str]
    """A list of all keys which would appear in any API action path (appearing before the '?')"""

    def __init__(
        self,
        *,
        headerData: type[GenericHeaderData] = GenericHeaderData,
        pathData: type[GenericPathData] = GenericPathData,
        acceptTypes: type[GenericAcceptTypes] = GenericAcceptTypes,
    ) -> None:
        """Instantiate a new Ratings API client."""
        if not issubclass(headerData, GenericHeaderData):
            raise TypeError("`headerData` must be of type `GenericHeaderData` or a subclass of it!")
        if not issubclass(pathData, GenericPathData):
            raise TypeError("`pathData` must be of type `GenericPathData` or a subclass of it!")
        if not issubclass(acceptTypes, GenericAcceptTypes):
            raise TypeError("`acceptTypes` must be of type `GenericAcceptTypes` or a subclass of it!")

        self._headerDataKeys = list(headerData.__members__.keys())
        self._pathDataKeys = list(pathData.__members__.keys())
        self._acceptTypes = list(acceptTypes.__members__.keys())

    def submitRequest(self, request: BaseRequest) -> pydantic.BaseModel:
        """Handles making any horde related API request.."""
        if not issubclass(request.__class__, BaseRequest):
            raise TypeError("`request` must be of type `BaseRequest` or a subclass of it!")

        def removeAttrsNotSpecified(request: BaseRequest, attributes: list[str]) -> list[str]:
            """Returns a copy of `attributes` with members removed if `request` doesn't define it, or it is `None`."""
            attrsToUse: list[str] = list(attributes)
            for attr in attributes:
                if not hasattr(request, attr) or getattr(request, attr) is None:
                    attrsToUse.remove(attr)
            return attrsToUse

        # We only want to craft a payload with values which have been explicitly given.
        specifiedHeaderKeys = removeAttrsNotSpecified(request, self._headerDataKeys)
        specifiedPathKeys = removeAttrsNotSpecified(request, self._pathDataKeys)

        endpointNoQuery: str = request.getEndpointURL()

        for pathKey in specifiedPathKeys:
            endpointNoQuery = endpointNoQuery.format_map({pathKey: str(getattr(request, pathKey))})

        requestParams = {}
        requestHeaders = {}
        for key, value in request.__dict__.items():
            if key in specifiedPathKeys:
                continue
            if key in specifiedHeaderKeys:
                # TODO
                # Requests doesn't handle Enum as header values gracefully?
                # see https://github.com/psf/requests/issues/6159
                if isinstance(value, Enum):
                    requestHeaders[key] = str(value)
                else:
                    requestHeaders[key] = value
                continue

            requestParams[key] = value

        rawResponse = requests.get(endpointNoQuery, headers=requestHeaders, params=requestParams)
        # FIXME no timeout or network error handling
        rawResponseJson = rawResponse.json()
        expectedResponseType = request.getExpectedResponseType()

        # FIXME should be something resembling error handling here
        return expectedResponseType(**rawResponseJson)
