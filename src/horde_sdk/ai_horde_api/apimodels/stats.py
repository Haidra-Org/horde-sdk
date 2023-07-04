import pydantic
from typing_extensions import override

from ...generic_api.apimodels import BaseRequest
from ...generic_api.endpoints import url_with_path
from ..endpoints import AI_HORDE_BASE_URL, AI_HORDE_API_URL_Literals


class StatsImageModels(BaseRequest):
    @override
    @staticmethod
    def get_endpoint_url() -> str:
        return url_with_path(base_url=AI_HORDE_BASE_URL, path=AI_HORDE_API_URL_Literals.v2_stats_img_models)

    @override
    @staticmethod
    def get_expected_response_type() -> type[pydantic.BaseModel]:
        return StatsModelsResponse


class StatsModelsResponse(pydantic.BaseModel):
    model_config = {"frozen": True}

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]
