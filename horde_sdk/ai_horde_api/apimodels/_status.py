from collections.abc import Iterator

from pydantic import ConfigDict, Field, RootModel
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.consts import MODEL_STATE, MODEL_TYPE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    ContainsMessageResponseMixin,
    HordeAPIObject,
    HordeResponse,
    HordeResponseBaseModel,
)
from horde_sdk.generic_api.decoration import Unhashable


class AIHordeHeartbeatResponse(HordeResponseBaseModel, ContainsMessageResponseMixin):
    version: str
    """The version of the AI Horde API that this node is running."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None


class AIHordeHeartbeatRequest(BaseAIHordeRequest):
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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_status_heartbeat

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AIHordeHeartbeatResponse]:
        return AIHordeHeartbeatResponse


class HordePerformanceResponse(HordeResponseBaseModel):
    interrogator_count: int | None = Field(
        default=None,
        description=(
            "How many workers are actively processing image interrogations in this {horde_noun} in the past 5 minutes."
        ),
    )
    """How many workers are actively processing image interrogations in this {horde_noun} in the past 5 minutes."""
    interrogator_thread_count: int | None = Field(
        default=None,
        description=(
            "How many worker threads are actively processing image interrogation in this {horde_noun} in the past 5"
            " minutes."
        ),
    )
    """How many worker threads are actively processing image interrogation in this {horde_noun} in the past 5
    minutes."""
    past_minute_megapixelsteps: float | None = Field(
        default=None,
    )
    """How many megapixelsteps this horde generated in the last minute."""
    past_minute_tokens: float | None = Field(
        default=None,
    )
    """How many tokens this horde generated in the last minute."""
    queued_forms: float | None = Field(
        default=None,
    )
    """The amount of image interrogations waiting and processing currently in this horde."""
    queued_megapixelsteps: float | None = Field(
        default=None,
    )
    """The amount of megapixelsteps in waiting and processing requests currently in this horde."""
    queued_requests: int | None = Field(
        default=None,
    )
    """The amount of waiting and processing image requests currently in this horde."""
    queued_text_requests: int | None = Field(
        default=None,
    )
    """The amount of waiting and processing text requests currently in this horde."""
    queued_tokens: float | None = Field(
        default=None,
    )
    """The amount of tokens in waiting and processing requests currently in this horde."""
    text_thread_count: int | None = Field(
        default=None,
        description=(
            "How many worker threads are actively processing prompt generations in this {horde_noun} in the past 5"
            " minutes."
        ),
    )
    """How many worker threads are actively processing prompt generations in this {horde_noun} in the past 5
    minutes."""
    text_worker_count: int | None = Field(
        default=None,
    )
    """How many workers are actively processing prompt generations in this horde in the past 5 minutes."""
    thread_count: int | None = Field(
        default=None,
        description=(
            "How many worker threads are actively processing prompt generations in this {horde_noun} in the past 5"
            " minutes."
        ),
    )
    """How many worker threads are actively processing prompt generations in this {horde_noun} in the past 5
    minutes."""
    worker_count: int | None = Field(
        default=None,
    )
    """How many workers are actively processing prompt generations in this horde in the past 5 minutes."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "HordePerformance"


class HordePerformanceRequest(BaseAIHordeRequest):
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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_status_performance

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordePerformanceResponse]:
        return HordePerformanceResponse


class Newspiece(HordeAPIObject):
    date_published: str | None = Field(
        default=None,
    )
    """The date this newspiece was published."""
    importance: str | None = Field(default=None, examples=["Information"])
    """How critical this piece of news is."""
    newspiece: str | None = Field(
        default=None,
    )
    """The actual piece of news."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "Newspiece"


@Unhashable
class NewsResponse(HordeResponse, RootModel[list[Newspiece]]):
    root: list[Newspiece]
    """The underlying list of newspieces."""

    def __iter__(self) -> Iterator[Newspiece]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, index: int) -> Newspiece:
        return self.root[index]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None  # FIXME

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NewsResponse):
            return False
        return all(newspiece in other.root for newspiece in self.root)


class NewsRequest(BaseAIHordeRequest):
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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_status_news

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[NewsResponse]:
        return NewsResponse


class ActiveModelLite(HordeAPIObject):
    count: int | None = Field(
        default=None,
    )
    """How many of workers in this horde are running this model."""
    name: str | None = Field(
        default=None,
    )
    """The Name of a model available by workers in this horde."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ActiveModelLite"


class ActiveModel(ActiveModelLite):
    eta: int | None = Field(
        default=None,
    )
    """Estimated time in seconds for this model's queue to be cleared."""
    jobs: float | None = Field(
        default=None,
    )
    """The job count waiting to be generated by this model."""
    performance: float | None = Field(
        default=None,
    )
    """The average speed of generation for this model."""
    queued: float | None = Field(
        default=None,
    )
    """The amount waiting to be generated by this model."""
    type_: MODEL_TYPE | None = Field(
        examples=[MODEL_TYPE.image, MODEL_TYPE.text],
        alias="type",
    )
    """The model type (text or image)."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ActiveModel"


@Unhashable
class HordeStatusModelsAllResponse(HordeResponse, RootModel[list[ActiveModel]]):
    root: list[ActiveModel]
    """The underlying list of models."""

    def __iter__(self) -> Iterator[ActiveModel]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, index: int) -> ActiveModel:
        return self.root[index]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None  # FIXME

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HordeStatusModelsAllResponse):
            return False
        return all(model in other.root for model in self.root)


class HordeStatusModelsAllRequest(BaseAIHordeRequest):
    model_config = ConfigDict(
        protected_namespaces=(),  # Allows the "model_" prefix on attrs
    )

    type_: MODEL_TYPE = Field(
        default=MODEL_TYPE.image,
        examples=[MODEL_TYPE.image, MODEL_TYPE.text],
        alias="type",
    )
    """The type of model to filter by."""

    min_count: int | None = None
    """Filter only models that have at least this amount of threads serving."""
    max_count: int | None = None
    """Filter only models that have at most this amount of threads serving."""

    model_state: MODEL_STATE = MODEL_STATE.all
    """If 'known', only show stats for known models in the model reference. If 'custom' only show stats for custom
    models. If 'all' shows stats for all models."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_status_models_all

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeStatusModelsAllResponse]:
        return HordeStatusModelsAllResponse

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["type_", "min_count", "max_count"]


@Unhashable
class HordeStatusModelsSingleResponse(HordeResponse, RootModel[list[ActiveModel]]):
    # This is a list because of an oversight in the structure of the API response. # FIXME

    root: list[ActiveModel]
    """The underlying list of models."""

    def __iter__(self) -> Iterator[ActiveModel]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, index: int) -> ActiveModel:
        return self.root[index]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HordeStatusModelsSingleResponse):
            return False
        return all(model in other.root for model in self.root)


class HordeStatusModelsSingleRequest(BaseAIHordeRequest):
    model_config = ConfigDict(
        protected_namespaces=(),  # Allows the "model_" prefix on attrs
    )

    model_name: str
    """The name of the model to request."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_status_models_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeStatusModelsSingleResponse]:
        return HordeStatusModelsSingleResponse


class HordeModes(HordeAPIObject):
    maintenance_mode: bool = Field(
        default=False,
    )
    """Whether the horde is in maintenance mode."""

    invite_only_mode: bool = Field(
        default=False,
    )
    """Whether the horde is in invite-only mode."""

    raid_mode: bool = Field(
        default=False,
    )
    """Whether the horde is in raid mode."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "HordeModes"
