from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import ActiveModelLite, BaseAIHordeRequest
from horde_sdk.ai_horde_api.apimodels.workers.workers import TeamDetailsLite
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


@Unhashable
@Unequatable
class TeamDetails(HordeResponseBaseModel, TeamDetailsLite):
    """Details about a team, including the models and workers that are part of it.

    Represents the data returned from the /v2/teams/{team_id} endpoint with http status code 200.

    v2 API Model: `TeamDetails`
    """

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
    """Details about all teams, including the models and workers that are part of them.

    Represents the data returned from the /v2/teams endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    root: list[TeamDetails]
    """The underlying list of teams."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class AllTeamDetailsRequest(
    BaseAIHordeRequest,
):
    """Request to get details about all teams.

    Represents a GET request to the /v2/teams endpoint.
    """

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
    """Request to get details about a single team by ID.

    Represents a GET request to the /v2/teams/{team_id} endpoint.
    """

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
    """Details about a team that has been modified.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/teams/{team_id} | ModifyTeamRequest [PATCH] -> 200
        - /v2/teams | CreateTeamRequest [POST] -> 200

    v2 API Model: `ModifyTeam`
    """

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
    """Input data for modifying a team.

    v2 API Model: `ModifyTeamInput`
    """

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
    """Request to create a new team.

    Represents a POST request to the /v2/teams endpoint.

    v2 API Model: `CreateTeamInput`
    """

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
    """Request to modify a team by ID.

    Represents a PATCH request to the /v2/teams/{team_id} endpoint.

    v2 API Model: `ModifyTeamInput`
    """

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
    """The team id and name that was just deleted.

    Represents the data returned from the /v2/teams/{team_id} endpoint with http status code 200.

    v2 API Model: `DeletedTeam`
    """

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
    """Request to delete a team by ID.

    Represents a DELETE request to the /v2/teams/{team_id} endpoint.
    """

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
