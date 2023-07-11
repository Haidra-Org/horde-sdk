from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.consts import WORKER_TYPE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import TeamID, WorkerID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseRequestAuthenticated, BaseResponse, HordeAPIModel
from pydantic import BaseModel, Field
from typing_extensions import override


class TeamDetailsLite(HordeAPIModel):
    name: str | None = None
    """The Name given to this team."""
    id_: str | TeamID | None = Field(None, alias="id")
    """The UUID of this team."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "TeamDetailsLite"


class WorkerKudosDetails(HordeAPIModel):
    generated: float | None = None
    """How much Kudos this worker has received for generating images."""
    uptime: int | None = None
    """How much Kudos this worker has received for staying online longer."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerKudosDetails"


class WorkerDetailItem(HordeAPIModel):
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
    post_processing: bool | None = None
    lora: bool | None = None
    max_length: int | None = None
    max_context_length: int | None = None
    tokens_generated: int | None = None

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetailItem"


class AllWorkersDetailsResponse(BaseResponse):
    _workers: list[WorkerDetailItem]

    @property
    def workers(self) -> list[WorkerDetailItem]:
        return self._workers

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "WorkerDetails"

    @override
    @classmethod
    def is_array_response(cls) -> bool:
        return True

    @override
    @classmethod
    def get_array_item_type(cls) -> type[BaseModel]:
        return WorkerDetailItem

    @override
    def set_array(self, list_: list) -> None:
        if not isinstance(list_, list):
            raise ValueError("list_ must be a list")

        parsed_list = []
        for item in list_:
            parsed_list.append(WorkerDetailItem(**item))

        self._workers = parsed_list

    @override
    def get_array(self) -> list:
        return self._workers.copy()


class AllWorkersDetailsRequest(BaseAIHordeRequest, BaseRequestAuthenticated):
    type_: WORKER_TYPE = Field(alias="type")

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_URL_Literals.v2_workers_all

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_success_response_type(cls) -> type[BaseResponse]:
        return AllWorkersDetailsResponse

    @override
    @classmethod
    def get_header_fields(cls) -> list[str]:
        return ["type_"]
