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
    """An IP address that is blocked and the number of seconds left in the timeout.

    v2 API Model: `IPTimeout`
    """

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
    """A list of IP addresses that are blocked.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/operations/ipaddr | SingleIPTimeoutsRequest [GET] -> 200
        - /v2/operations/ipaddr | AllIPTimeoutsRequest [GET] -> 200

    v2 API Model: `_ANONYMOUS_MODEL`
    """

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
    """A request to get all IP addresses that are blocked.

    Represents a GET request to the /v2/operations/ipaddr endpoint.
    """

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
    """A request to get a single IP address that is blocked.

    Represents a GET request to the /v2/operations/ipaddr endpoint.
    """

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
    """Indicates that an IP address was successfully blocked.

    Represents the data returned from the /v2/operations/ipaddr endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class BlockIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Establish a timeout for an IP address for a specified number of hours.

    Represents a POST request to the /v2/operations/ipaddr endpoint.

    v2 API Model: `AddTimeoutIPInput`
    """

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
    """Indicates that an IP address was successfully unblocked.

    Represents the data returned from the /v2/operations/ipaddr endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Remove a timeout for an IP address.

    Represents a DELETE request to the /v2/operations/ipaddr endpoint.

    v2 API Model: `DeleteTimeoutIPInput`
    """

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
    """Indicates that a worker's IP address was successfully blocked.

    Represents the data returned from the /v2/operations/block_worker_ipaddr/{worker_id} endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class BlockWorkerIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to block a worker's IP address for a specified number of days.

    Represents a PUT request to the /v2/operations/block_worker_ipaddr/{worker_id} endpoint.

    v2 API Model: `AddWorkerTimeout`
    """

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
    """Indicates that a worker's IP address was successfully unblocked.

    Represents the data returned from the /v2/operations/block_worker_ipaddr/{worker_id} endpoint with http status
    code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteWorkerIPAddressRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to unblock a worker's IP address.

    Represents a DELETE request to the /v2/operations/block_worker_ipaddr/{worker_id} endpoint.
    """

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
