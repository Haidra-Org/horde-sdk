"""Definitions for the admin operations."""

from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class IPTimeout(HordeAPIObjectBaseModel):
    ipaddr: str
    """The IP address of the user to block."""
    seconds: int
    """How many more seconds this IP block is in timeout."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "IPTimeout"


@Unhashable
@Unequatable
class IPTimeoutListResponse(HordeResponseRootModel[list[IPTimeout]]):
    """A response containing a list of IP addresses that are blocked."""

    root: list[IPTimeout]
    """The underlying list of IP addresses that are blocked."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class AllIPTimeoutsRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """A request to get all IP addresses that are blocked."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_ipaddr

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[IPTimeoutListResponse]:
        return IPTimeoutListResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class SingleIPTimeoutsRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """A request to get all IP addresses that are blocked."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_ipaddr

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[IPTimeoutListResponse]:
        return IPTimeoutListResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class BlockIPAddressResponse(HordeResponseBaseModel, ContainsMessageResponseMixin):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class BlockIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """A request to block an IP address."""

    ipaddr: str
    """The IP address of the user to block."""

    hours: int
    """The number of hours to block the IP address for."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "AddTimeoutIPInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_ipaddr

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[BlockIPAddressResponse]:
        return BlockIPAddressResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteIPAddressResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """A request to delete an IP address from the block list."""

    ipaddr: str
    """The IP address of the user to unblock."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "DeleteTimeoutIPInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_ipaddr

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteIPAddressResponse]:
        return DeleteIPAddressResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class BlockWorkerIPAddressResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class BlockWorkerIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """A request to block a worker IP address."""

    worker_id: str
    """The ID of the worker to block."""

    days: int
    """The number of days to block the worker IP address for."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "AddWorkerTimeout"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PUT

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_block_worker_ipaddr_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[BlockWorkerIPAddressResponse]:
        return BlockWorkerIPAddressResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteWorkerIPAddressResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteWorkerIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):

    worker_id: str
    """The ID of the worker to unblock."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_block_worker_ipaddr_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteWorkerIPAddressResponse]:
        return DeleteWorkerIPAddressResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


__all__ = [
    "IPTimeout",
    "IPTimeoutListResponse",
    "AllIPTimeoutsRequest",
    "SingleIPTimeoutsRequest",
    "BlockIPAddressResponse",
    "BlockIPAddressRequest",
    "DeleteIPAddressResponse",
    "DeleteIPAddressRequest",
    "BlockWorkerIPAddressResponse",
    "BlockWorkerIPAddressRequest",
    "DeleteWorkerIPAddressResponse",
    "DeleteWorkerIPAddressRequest",
]
