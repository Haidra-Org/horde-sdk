"""Tools for making or interacting with any horde APIs."""
from horde_sdk.generic_api._error import RequestErrorResponse
from horde_sdk.generic_api.apimodels import BaseRequest, BaseRequestAuthenticated, BaseRequestUserSpecific
from horde_sdk.generic_api.generic_client import GenericHordeAPIClient
from horde_sdk.generic_api.metadata import (
    GenericAcceptTypes,
    GenericHeaderFields,
    GenericPathFields,
    GenericQueryFields,
)

__all__ = [
    "RequestErrorResponse",
    "BaseRequest",
    "BaseRequestAuthenticated",
    "BaseRequestUserSpecific",
    "GenericHordeAPIClient",
    "GenericAcceptTypes",
    "GenericHeaderFields",
    "GenericPathFields",
    "GenericQueryFields",
]
