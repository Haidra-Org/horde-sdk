from collections.abc import Iterator

from pydantic import AliasChoices, Field, RootModel
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
from horde_sdk.generic_api.decoration import Unhashable


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


@Unhashable
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkerDetailItem):
            return False
        return (
            self.type_ == other.type_
            and self.name == other.name
            and self.id_ == other.id_
            and self.online == other.online
            and self.requests_fulfilled == other.requests_fulfilled
            and self.kudos_rewards == other.kudos_rewards
            and self.kudos_details == other.kudos_details
            and self.performance == other.performance
            and self.threads == other.threads
            and self.uptime == other.uptime
            and self.maintenance_mode == other.maintenance_mode
            and self.paused == other.paused
            and self.info == other.info
            and self.nsfw == other.nsfw
            and self.owner == other.owner
            and self.ipaddr == other.ipaddr
            and self.trusted == other.trusted
            and self.flagged == other.flagged
            and self.suspicious == other.suspicious
            and self.uncompleted_jobs == other.uncompleted_jobs
            and (all(model in other.models for model in self.models) if self.models and other.models else True)
            and (all(form in other.forms for form in self.forms) if self.forms and other.forms else True)
            and self.team == other.team
            and self.contact == other.contact
            and self.bridge_agent == other.bridge_agent
            and self.max_pixels == other.max_pixels
            and self.megapixelsteps_generated == other.megapixelsteps_generated
            and self.img2img == other.img2img
            and self.painting == other.painting
            and self.post_processing == other.post_processing
            and self.lora == other.lora
            and self.max_length == other.max_length
            and self.max_context_length == other.max_context_length
            and self.tokens_generated == other.tokens_generated
        )


@Unhashable
class AllWorkersDetailsResponse(HordeResponse, RootModel[list[WorkerDetailItem]]):
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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AllWorkersDetailsResponse):
            return False
        return all(worker in other.root for worker in self.root)


class AllWorkersDetailsRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Returns information on all works. If a moderator API key is specified, it will return additional information."""

    type_: WORKER_TYPE = Field(WORKER_TYPE.all, alias="type")

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
    def get_default_success_response_type(cls) -> type[AllWorkersDetailsResponse]:
        return AllWorkersDetailsResponse

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["type_"]

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return False
