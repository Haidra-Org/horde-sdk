import pydantic
from typing_extensions import override

from ...generic_api.apimodels import BaseRequest
from ...generic_api.endpoints import URLWithPath
from ..endpoints import AI_HORDE_BASE_URL, AI_HORDE_API_URL_Literals


class StatsImageModels(BaseRequest):
    @override
    @staticmethod
    def getEndpointURL() -> str:
        return URLWithPath(baseURL=AI_HORDE_BASE_URL, path=AI_HORDE_API_URL_Literals.v1_stats_img_models)

    @override
    @staticmethod
    def getExpectedResponseType() -> type[pydantic.BaseModel]:
        return StatsModelsResponse


class StatsModelsResponse(pydantic.BaseModel):
    class Config:
        """Pydantic config class."""

        allow_mutation = False

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]
