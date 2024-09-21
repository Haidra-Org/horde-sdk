from collections.abc import Iterator

from pydantic import AliasChoices, Field, RootModel
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, WorkerRequestMixin, WorkerRequestNameMixin
from horde_sdk.ai_horde_api.consts import WORKER_TYPE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import TeamID, WorkerID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObject,
    HordeResponse,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class TeamDetailsLite(HordeAPIObject):
    name: str | None = None
    """The Name given to this team."""
    id_: str | TeamID | None = Field(default=None, alias="id")
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
    """The type of worker."""
    name: str
    """The Name given to this worker."""
    id_: str | WorkerID = Field(alias="id")
    """The UUID of this worker."""
    online: bool | None = None
    """True if the worker has checked-in the past 5 minutes."""
    requests_fulfilled: int | None = None
    """How many images this worker has generated."""
    kudos_rewards: float | None = None
    """How many Kudos this worker has been rewarded in total."""
    kudos_details: WorkerKudosDetails | None = None
    """How much Kudos this worker has accumulated or used for generating images."""
    performance: str | None = None
    """The average performance of this worker in human readable form."""
    threads: int | None = None
    """How many threads this worker is running."""
    uptime: int | None = None
    """The amount of seconds this worker has been online for this AI Horde."""
    maintenance_mode: bool
    """When True, this worker will not pick up any new requests."""
    paused: bool | None = None
    """When True, this worker not be given any new requests."""
    info: str | None = None
    """Extra information or comments about this worker provided by its owner."""
    nsfw: bool | None = None
    """Whether this worker can generate NSFW requests or not."""
    owner: str | None = None
    """Privileged or public if the owner has allowed it. The alias of the owner of this worker."""
    ipaddr: str | None = None
    """Privileged. The last known IP this worker has connected from."""
    trusted: bool | None = None
    """The worker is trusted to return valid generations."""
    flagged: bool | None = None
    """The worker's owner has been flagged for suspicious activity.
    This worker will not be given any jobs to process."""
    suspicious: int | None = None
    """(Privileged) How much suspicion this worker has accumulated."""
    uncompleted_jobs: int | None = None
    """How many jobs this worker has left uncompleted after it started them."""
    models: list[str] | None = None
    """The models this worker supports."""
    forms: list[str] | None = None
    """The forms this worker supports."""
    team: TeamDetailsLite | None = None
    """The team this worker belongs to."""
    contact: str | None = Field(default=None, min_length=4, max_length=500)
    """(Privileged) Contact details for the horde admins to reach the owner of this worker in emergencies."""
    bridge_agent: str = Field(max_length=1000, examples=["AI Horde Worker reGen:4.1.0:"])
    """The bridge agent name, version and website. Example: AI Horde Worker reGen:4.1.0:"""
    max_pixels: int | None = Field(default=None, examples=[262144])
    """The maximum pixels in resolution this worker can generate. Example: 262144"""
    megapixelsteps_generated: int | None = None
    """How many megapixelsteps this worker has generated until now."""
    img2img: bool | None = None
    """If True, this worker supports and allows img2img requests."""
    painting: bool | None = None
    """If True, this worker supports and allows inpainting requests."""
    post_processing: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("post_processing", "post-processing"),
        serialization_alias="post-processing",
    )
    """If True, this worker supports and allows post-processing requests."""
    lora: bool | None = None
    """If True, this worker supports and allows lora requests."""
    max_length: int | None = Field(default=None, examples=[80])
    """The maximum tokens this worker can generate."""
    max_context_length: int | None = Field(default=None, examples=[80])
    """The maximum tokens this worker can read."""
    tokens_generated: int | None = Field(default=None, examples=[0])
    """How many tokens this worker has generated until now. """

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
@Unequatable
class AllWorkersDetailsResponse(HordeResponse, RootModel[list[WorkerDetailItem]]):
    # @tazlin: The typing of __iter__ in BaseModel seems to assume that RootModel wouldn't also be a parent class.
    # without a `type: ignore``, mypy feels that this is a bad override. This is probably a sub-optimal solution
    # on my part with me hoping to come up with a more elegant path in the future.
    # TODO: fix this?

    root: list[WorkerDetailItem]
    """The underlying list of worker details."""

    def __iter__(self) -> Iterator[WorkerDetailItem]:  # type: ignore
        return iter(self.root)

    def __getitem__(self, item: int) -> WorkerDetailItem:
        return self.root[item]

    def __len__(self) -> int:
        return len(self.root)

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetails"


class AllWorkersDetailsRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Returns information on all workers.

    If a moderator API key is specified, it will return additional information.
    """

    type_: WORKER_TYPE = Field(WORKER_TYPE.all, alias="type")
    """Filter workers by type. Default is 'all' which returns all workers."""
    name: str | None = Field(default=None)
    """Returns a worker matching the exact name provided. Case insensitive."""

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
        return ["type_", "name"]

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return False


@Unhashable
@Unequatable
class SingleWorkerDetailsResponse(HordeResponse, WorkerDetailItem):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetails"


class SingleWorkerNameDetailsRequest(BaseAIHordeRequest, WorkerRequestNameMixin, APIKeyAllowedInRequestMixin):
    """Returns information on a single worker.

    If a moderator API key is specified, additional information is returned.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_single_name

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SingleWorkerDetailsResponse]:
        return SingleWorkerDetailsResponse

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return False


class SingleWorkerDetailsRequest(BaseAIHordeRequest, WorkerRequestMixin, APIKeyAllowedInRequestMixin):
    """Returns information on a single worker.

    If a moderator API key is specified, additional information is returned.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_single

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SingleWorkerDetailsResponse]:
        return SingleWorkerDetailsResponse

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return False


class ModifyWorkerResponse(HordeResponse):
    info: str | None = Field(default=None)
    """The new state of the 'info' var for this worker."""
    maintenance: bool | None = Field(default=None)
    """The new state of the 'maintenance' var for this worker. When True, this worker will not pick up any new
    requests."""
    name: str | None = Field(default=None)
    """The new name for this this worker. No profanity allowed!"""
    paused: bool | None = Field(default=None)
    """The new state of the 'paused' var for this worker. When True, this worker will not be given any new requests."""
    team: str | None = Field(default=None, examples=["Direct Action"])
    """The new team of this worker."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModifyWorker"


class ModifyWorkerRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    WorkerRequestMixin,
):
    info: str | None = Field(default=None, max_length=1000)
    """You can optionally provide a server note which will be seen in the server details. No profanity allowed!"""
    maintenance: bool | None = Field(default=None)
    """Set to true to put this worker into maintenance."""
    maintenance_msg: str | None = Field(default=None)
    """If maintenance is True, you can optionally provide a message to be used instead of the default maintenance
    message, so that the owner is informed."""
    name: str | None = Field(default=None, max_length=100, min_length=5)
    """When this is set, it will change the worker's name. No profanity allowed!"""
    paused: bool | None = Field(default=None)
    """(Mods only) Set to true to pause this worker."""
    team: str | None = Field(default=None, examples=["0bed257b-e57c-4327-ac64-40cdfb1ac5e6"], max_length=36)
    """The team towards which this worker contributes kudos.  It an empty string ('') is passed, it will leave the"""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModifyWorkerInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PUT

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyWorkerResponse]:
        return ModifyWorkerResponse


class DeleteWorkerResponse(HordeResponse):
    deleted_id_: str | None = None
    """The ID of the deleted worker."""
    deleted_name: str | None = None
    """The Name of the deleted worker."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "DeletedWorker"


class DeleteWorkerRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    WorkerRequestMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteWorkerResponse]:
        return DeleteWorkerResponse

    @classmethod
    def is_api_key_required(cls) -> bool:
        """Return whether this endpoint requires an API key."""
        return True
