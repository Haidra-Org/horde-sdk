from typing import Literal

from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import ActiveModelLite, BaseAIHordeRequest
from horde_sdk.ai_horde_api.apimodels.workers.workers import TeamDetailsLite
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


@Unhashable
@Unequatable
class TeamDetails(HordeResponseBaseModel, TeamDetailsLite):
    info: str | None = Field(
        default=None,
        examples=[
            "Anarchy is emergent order.",
        ],
    )
    """Extra information or comments about this team provided by its owner."""
    creator: str | None = Field(
        default=None,
        examples=["db0#1"],
    )
    """The alias of the user which created this team."""
    kudos: float | None = Field(
        default=None,
    )
    """How many Kudos the workers in this team have been rewarded while part of this team."""
    models: list[ActiveModelLite] | None = None
    """The models that this team has run."""
    requests_fulfilled: int | None = Field(
        default=None,
    )
    """How many images this team's workers have generated."""
    uptime: int | None = Field(
        default=None,
    )
    """The total amount of time workers have stayed online while on this team."""
    worker_count: int | None = Field(
        default=None,
        examples=[10],
    )
    """How many workers have been dedicated to this team."""
    workers: list[ActiveModelLite] | None = None
    """The workers that have been dedicated to this team."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "TeamDetails"


@Unhashable
@Unequatable
class AllTeamDetailsResponse(HordeResponseRootModel[list[TeamDetails]]):

    root: list[TeamDetails]
    """The underlying list of teams."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class AllTeamDetailsRequest(
    BaseAIHordeRequest,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_teams_all

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AllTeamDetailsResponse]:
        return AllTeamDetailsResponse


class SingleTeamDetailsRequest(
    BaseAIHordeRequest,
):
    team_id: str
    """The ID of the team to get details for."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_teams_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TeamDetails]:
        return TeamDetails


class ModifyTeam(HordeResponseBaseModel):
    id_: str = Field(alias="id")
    """The ID of the team."""
    name: str
    """The name of the team."""
    info: str | None = Field(
        default=None,
        examples=[
            "Anarchy is emergent order.",
        ],
    )

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModifyTeam"


class ModifyTeamInput(HordeAPIObjectBaseModel):
    name: str
    """The name of the team."""
    info: str | None = Field(
        default=None,
        examples=[
            "Anarchy is emergent order.",
        ],
    )
    """Extra information or comments about this team provided by its owner."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModifyTeamInput"


class CreateTeamRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    ModifyTeamInput,
):

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "CreateTeamInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_teams_all

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyTeam]:
        return ModifyTeam


class ModifyTeamRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    ModifyTeamInput,
):
    team_id: str

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModifyTeamInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_teams_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyTeam]:
        return ModifyTeam

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteTeamResponse(HordeResponseBaseModel):

    deleted_id: str
    """The ID of the team that was deleted."""
    deleted_name: str
    """The name of the team that was deleted."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "DeletedTeam"


class DeleteTeamRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    team_id: str
    """The ID of the team to delete."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_teams_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteTeamResponse]:
        return DeleteTeamResponse
