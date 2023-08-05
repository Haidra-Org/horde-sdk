from pydantic import BaseModel, RootModel
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    BaseResponse,
    MayUseAPIKeyInRequestMixin,
    RequestUsesImageWorkerMixin,
    ResponseNeedingFollowUpMixin,
)


class AlchemyUpscaleResult(RootModel[str]):
    url: str

    def __str__(self) -> str:
        return self.url


class AlchemyCaptionResult(BaseModel):
    caption: str


class AlchemyNSFWResult(BaseModel):
    nsfw: bool


class InterrogationResultItem(BaseModel):
    text: str
    confidence: float


class InterrogationDetails(BaseModel):
    tags: list[InterrogationResultItem]
    sites: list[InterrogationResultItem]
    artists: list[InterrogationResultItem]
    flavors: list[InterrogationResultItem]
    mediums: list[InterrogationResultItem]
    movements: list[InterrogationResultItem]
    techniques: list[InterrogationResultItem]


class AlchemyInterrogationResult(BaseModel):
    interrogation: InterrogationDetails


class AlchemyFormStatus(BaseModel):
    form: str
    state: str
    result: InterrogationDetails | AlchemyNSFWResult | AlchemyCaptionResult | AlchemyUpscaleResult


class AlchemyStatusResponse(BaseResponse, ResponseNeedingFollowUpMixin):
    state: str
    forms: list[AlchemyFormStatus]


class AlchemyStatusRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
    MayUseAPIKeyInRequestMixin,
    RequestUsesImageWorkerMixin,
):
    """Represents the data needed to make a request to the `/v2/interrogate/status/{id}` endpoint."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_interrogate_async

    @override
    @classmethod
    def get_success_response_type(cls) -> type[AlchemyStatusResponse]:
        return AlchemyStatusResponse
