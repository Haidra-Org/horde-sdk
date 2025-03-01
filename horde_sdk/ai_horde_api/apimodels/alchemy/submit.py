from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel


class AlchemyJobSubmitResponse(HordeResponseBaseModel):
    """The reward for submitting an alchemy job. Receipt of this response means the job was successfully submitted.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/interrogate/submit | AlchemyJobSubmitRequest [POST] -> 200
        - /v2/interrogate/submit | AlchemyJobSubmitRequest [POST] -> 200

    v2 API Model: `GenerationSubmitted`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"

    reward: float
    """The kudos reward for this job."""


class AlchemyJobSubmitRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    """Request to submit an alchemy job once a worker has completed it.

    Represents a POST request to the /v2/interrogate/submit endpoint.

    v2 API Model: `SubmitInputStable`
    """

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
