from enum import auto

from pydantic import field_validator
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import HordeResponseBaseModel


class StatsModelsTimeframe(StrEnum):
    day = auto()
    month = auto()
    total = auto()


class StatsModelsResponse(HordeResponseBaseModel):
    """Represents the data returned from the `/v2/stats/img/models` endpoint.

    v2 API Model: `ImgModelStats`
    """

    day: dict[str, int]
    month: dict[str, int]
    total: dict[str, int]

    @field_validator("day", "month", "total", mode="before")
    @classmethod
    def validate_timeframe_data(cls, v: dict[str, int | None]) -> dict[str, int]:
        """Validates the data for a timeframe.

        Args:
            v (dict[str, int | None]): The data for a timeframe.

        Raises:
            ValueError: If the data is invalid.

        Returns:
            dict[str, int]: The data for a timeframe.
        """
        if v is None:
            return {}

        return_v = {}
        # Replace all `None` values with 0
        for key, value in v.items():
            if value is None:
                return_v[key] = 0
            else:
                return_v[key] = value

        return return_v

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ImgModelStats"

    def get_timeframe(self, timeframe: StatsModelsTimeframe) -> dict[str, int]:
        """Returns the data for the given timeframe.

        Args:
            timeframe (StatsModelsTimeframe): The timeframe to get the data for.

        Returns:
            dict[str, int]: The data for the given timeframe.
        """
        if timeframe == StatsModelsTimeframe.day:
            return self.day
        if timeframe == StatsModelsTimeframe.month:
            return self.month
        if timeframe == StatsModelsTimeframe.total:
            return self.total

        raise ValueError(f"Invalid timeframe: {timeframe}")


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
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_stats_img_models

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StatsModelsResponse]:
        return StatsModelsResponse
