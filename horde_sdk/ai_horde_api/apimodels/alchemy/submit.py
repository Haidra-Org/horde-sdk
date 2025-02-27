from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel


class AlchemyJobSubmitResponse(HordeResponseBaseModel):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"

    reward: float
    """The kudos reward for this job."""


class AlchemyJobSubmitRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    result: str  # FIXME
    """The result of the alchemy job."""
    state: GENERATION_STATE
    """The state of this generation. See `GENERATION_STATE` for more information."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SubmitInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_submit

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyJobSubmitResponse]:
        return AlchemyJobSubmitResponse
