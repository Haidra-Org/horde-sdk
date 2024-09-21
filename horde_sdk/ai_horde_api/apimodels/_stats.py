from enum import auto

from loguru import logger
from pydantic import ConfigDict, Field, field_validator
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.consts import MODEL_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import HordeAPIDataObject, HordeResponseBaseModel
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class StatsModelsTimeframe(StrEnum):
    day = auto()
    month = auto()
    total = auto()


@Unequatable
@Unhashable
class ImageStatsModelsResponse(HordeResponseBaseModel):
    """Represents the data returned from the `/v2/stats/img/models` endpoint.

    v2 API Model: `ImgModelStats`
    """

    day: dict[str, int]
    """The stats for the past day."""
    month: dict[str, int]
    """The stats for the past month."""
    total: dict[str, int]
    """The total stats for all time."""

    @field_validator("day", "month", "total", mode="before")
    @classmethod
    def validate_timeframe_data(cls, v: dict[str, int | None]) -> dict[str, int]:
        """Validate the data for a timeframe.

        Args:
            v (dict[str, int | None]): The data for a timeframe.

        Raises:
            ValueError: If the data is invalid.

        Returns:
            dict[str, int]: The data for a timeframe.
        """
        if v is None:
            return {}

        if "additionalProp1" in v:
            logger.warning("Found `additionalProp` in stats data, this is a dummy result. Ignoring.")
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
        """Return the data for the given timeframe.

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


class ImageStatsModelsRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/stats/img/models` endpoint."""

    model_config = ConfigDict(
        protected_namespaces=(),  # Allows the "model_" prefix on attrs
    )

    model_state: MODEL_STATE = Field(
        default=MODEL_STATE.all,
    )
    """The state of the models to get stats for. Known models are models that are known to the system."""

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
    def get_default_success_response_type(cls) -> type[ImageStatsModelsResponse]:
        return ImageStatsModelsResponse


class SinglePeriodImgStat(HordeAPIDataObject):
    images: int | None = Field(
        default=None,
    )
    """The amount of images generated during this period."""
    ps: int | None = Field(
        default=None,
    )
    """The amount of pixelsteps generated during this period."""

    @property
    def mps(self) -> int | None:
        """The amount of megapixelsteps generated during this period."""
        if self.ps is None:
            return None

        return self.ps // 1_000_000


class ImageStatsModelsTotalResponse(HordeResponseBaseModel):
    """Represents the data returned from the `/v2/stats/img/totals` endpoint."""

    day: SinglePeriodImgStat | None = None
    """The total stats for the past day."""
    hour: SinglePeriodImgStat | None = None
    """The total stats for the past hour."""
    minute: SinglePeriodImgStat | None = None
    """The total stats for the past minute."""
    month: SinglePeriodImgStat | None = None
    """The total stats for the past month."""
    total: SinglePeriodImgStat | None = None
    """The total stats for all time."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "StatsImgTotals"


class ImageStatsModelsTotalRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/stats/img/totals` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_stats_img_totals

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageStatsModelsTotalResponse]:
        return ImageStatsModelsTotalResponse


@Unhashable
class TextStatsModelResponse(HordeResponseBaseModel):
    """Represents the data returned from the `/v2/stats/text/models` endpoint."""

    day: dict[str, int]
    """The stats for the past day."""
    month: dict[str, int]
    """The stats for the past month."""
    total: dict[str, int]
    """The total stats for all time."""

    @field_validator("day", "month", "total", mode="before")
    @classmethod
    def validate_timeframe_data(cls, v: dict[str, int | None]) -> dict[str, int]:
        """Validate the data for a timeframe.

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
        return "TxtModelStats"


class TextStatsModelsRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/stats/text/models` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_stats_text_models

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextStatsModelResponse]:
        return TextStatsModelResponse


class SinglePeriodTxtStat(HordeAPIDataObject):
    requests: int | None = Field(
        default=None,
    )
    """The number of requests made during this period."""
    tokens: int | None = Field(
        default=None,
    )
    """The number of tokens generated during this period."""


@Unhashable
class TextStatsModelsTotalResponse(HordeResponseBaseModel):
    """Represents the data returned from the `/v2/stats/text/totals` endpoint."""

    minute: dict[str, int]
    """The total stats for the past minute."""
    hour: dict[str, int]
    """The total stats for the past hour."""
    day: dict[str, int]
    """The total stats for the past day."""
    month: dict[str, int]
    """The total stats for the past month."""
    total: dict[str, int]
    """The total stats for all time."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "StatsTxtTotals"


class TextStatsModelsTotalRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/stats/text/totals` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_stats_text_totals

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextStatsModelsTotalResponse]:
        return TextStatsModelsTotalResponse
