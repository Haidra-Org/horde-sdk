from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, BaseResponse


class AlchemyJobSubmitResponse(BaseResponse):
    result: float


class AlchemyJobSubmitRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    pass
