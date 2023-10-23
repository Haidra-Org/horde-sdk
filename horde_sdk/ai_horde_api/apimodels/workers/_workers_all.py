from collections.abc import Iterator
from typing import ClassVar

from pydantic import AliasChoices, ConfigDict, Field, RootModel
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.consts import WORKER_TYPE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import TeamID, WorkerID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObject,
    HordeResponse,
)


class TeamDetailsLite(HordeAPIObject):
    name: str | None = None
    """The Name given to this team."""
    id_: str | TeamID | None = Field(None, alias="id")
    """The UUID of this team."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "TeamDetailsLite"


class WorkerKudosDetails(HordeAPIObject):
    generated: float | None = None
    """How much Kudos this worker has received for generating images."""
    uptime: int | None = None
    """How much Kudos this worker has received for staying online longer."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerKudosDetails"


class WorkerDetailItem(HordeAPIObject):
    type_: WORKER_TYPE = Field(alias="type")
    name: str
    id_: str | WorkerID = Field(alias="id")
    online: bool | None = None
    requests_fulfilled: int | None = None
    kudos_rewards: float | None = None
    kudos_details: WorkerKudosDetails | None = None
    performance: str | None = None
    threads: int | None = None
    uptime: int | None = None
    maintenance_mode: bool
    paused: bool | None = None
    info: str | None = None
    nsfw: bool | None = None
    owner: str | None = None
    ipaddr: str | None = None
    trusted: bool | None = None
    flagged: bool | None = None
    suspicious: int | None = None
    uncompleted_jobs: int | None = None
    models: list[str] | None = None
    forms: list[str] | None = None
    team: TeamDetailsLite | None = None
    contact: str | None = Field(None, min_length=4, max_length=500)
    bridge_agent: str = Field(max_length=1000)
    max_pixels: int | None = None
    megapixelsteps_generated: int | None = None
    img2img: bool | None = None
    painting: bool | None = None
    post_processing: bool | None = Field(
        None,
        validation_alias=AliasChoices("post_processing", "post-processing"),
        serialization_alias="post-processing",
    )
    lora: bool | None = None
    max_length: int | None = None
    max_context_length: int | None = None
    tokens_generated: int | None = None

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetailItem"


class AllWorkersDetailsResponse(HordeResponse, RootModel[list[WorkerDetailItem]]):
    model_config: ClassVar[ConfigDict] = {}

    # @tazlin: The typing of __iter__ in BaseModel seems to assume that RootModel wouldn't also be a parent class.
    # without a `type: ignore``, mypy feels that this is a bad override. This is probably a sub-optimal solution
    # on my part with me hoping to come up with a more elegant path in the future.
    # TODO: fix this?
    def __iter__(self) -> Iterator[WorkerDetailItem]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, item: int) -> WorkerDetailItem:
        return self.root[item]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetails"


class AllWorkersDetailsRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Returns information on all works. If a moderator API key is specified, it will return additional information."""

    type_: WORKER_TYPE = Field(alias="type")

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_all

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeResponse]:
        return AllWorkersDetailsResponse

    @override
    @classmethod
    def get_header_fields(cls) -> list[str]:
        return ["type_"]

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return False
