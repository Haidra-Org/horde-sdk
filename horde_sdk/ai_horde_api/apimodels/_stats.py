from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse


class StatsModelsResponse(BaseResponse):
    """Represents the data returned from the `/v2/stats/img/models` endpoint.

    v2 API Model: `ImgModelStats`
    """

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ImgModelStats"


class StatsImageModelsRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/stats/img/models` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_stats_img_models

    @override
    @classmethod
    def get_success_response_type(cls) -> type[StatsModelsResponse]:
        return StatsModelsResponse
