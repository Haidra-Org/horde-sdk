from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponse


class KudosTransferResponse(HordeResponse):
    transferred: float | None = None
    """The amount of Kudos transferred."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "KudosTransferred"


class KudosTransferRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    username: str
    """The username of the user to transfer Kudos to."""
    amount: float
    """The amount of Kudos to transfer."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_kudos_transfer

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[KudosTransferResponse]:
        return KudosTransferResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
