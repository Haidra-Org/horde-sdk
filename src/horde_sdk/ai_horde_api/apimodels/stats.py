from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._shared import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse


class StatsImageModels(BaseAIHordeRequest):
    __api_model_name__ = "ImgModelStats"
    __http_method__ = HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return AI_HORDE_API_URL_Literals.v2_stats_img_models

    @override
    @staticmethod
    def get_expected_response_type() -> type[BaseResponse]:
        return StatsModelsResponse


class StatsModelsResponse(BaseResponse):
    model_config = {"frozen": True}

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]
