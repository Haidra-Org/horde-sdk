from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel


class KudosTransferResponse(HordeResponseBaseModel):
    """The transferred amount of Kudos.

    Represents the data returned from the /v2/kudos/transfer endpoint with http status code 200.

    v2 API Model: `KudosTransferred`
    """

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
    """Request to transfer Kudos to another user. Be sure to use their entire username (e.g., db0#1).

    Represents a POST request to the /v2/kudos/transfer endpoint.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    username: str
    """The username of the user to transfer Kudos to, including the '#'. For example, 'db0#1'."""
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


class KudosAwardResponse(HordeResponseBaseModel):
    """The awarded amount of Kudos.

    Represents the data returned from the /v2/kudos/award endpoint with http status code 200.

    v2 API Model: `KudosAwarded`
    """

    awarded: float | None = None
    """The amount of Kudos awarded."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "KudosAwarded"


class KudosAwardRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to award Kudos to another user. Be sure to use their entire username (e.g., db0#1).

    This is a privileged endpoint that requires an admin API key.

    Represents a POST request to the /v2/kudos/award endpoint.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    username: str
    """The username of the user to award Kudos to."""
    amount: float
    """The amount of Kudos to award."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_kudos_award

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[KudosAwardResponse]:
        return KudosAwardResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
