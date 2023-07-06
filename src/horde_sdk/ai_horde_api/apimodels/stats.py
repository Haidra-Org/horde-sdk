from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._shared import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse


class StatsModelsResponse(BaseResponse):
    model_config = {"frozen": True}

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ImgModelStats"


class StatsImageModels(BaseAIHordeRequest):
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
    def get_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_URL_Literals.v2_stats_img_models

    @override
    @classmethod
    def get_expected_response_type(cls) -> type[StatsModelsResponse]:
        return StatsModelsResponse
