from datetime import datetime

from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._styles import ResponseModelStylesUser
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import UUID_Identifier
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
    MessageSpecifiesUserIDMixin,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class ContributionsDetails(HordeAPIObjectBaseModel):
    """How many images and megapixelsteps this user has generated.

    v2 API Model: ContributionsDetails
    """

    fulfillments: int | None = Field(
        default=None,
    )
    """How many images this user has generated."""
    megapixelsteps: float | None = Field(
        default=None,
    )
    """How many megapixelsteps this user has generated."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ContributionsDetails"


class UserKudosDetails(HordeAPIObjectBaseModel):
    """The details of the kudos this user has accumulated, used, sent and received.

    v2 API Model: UserKudosDetails
    """

    accumulated: float | None = Field(0)
    """The amount of Kudos accumulated or used for generating images."""

    admin: float | None = Field(0)
    """The amount of Kudos this user has been given by the Horde admins."""

    awarded: float | None = Field(0)
    """The amount of Kudos this user has been awarded from things like rating images."""

    gifted: float | None = Field(0)
    """The amount of Kudos this user has given to other users."""

    received: float | None = Field(0)
    """The amount of Kudos this user has been given by other users."""

    donated: float | None = Field(0)
    """The amount of Kudos this user has donated to support education accounts."""

    recurring: float | None = Field(0)
    """The amount of Kudos this user has received from recurring rewards."""

    styled: float | None = Field(0)
    """The amount of Kudos this user has received from styling images."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserKudosDetails"


class MonthlyKudos(HordeAPIObjectBaseModel):
    """The details of the monthly kudos this user receives.

    v2 API Model: MonthlyKudos
    """

    amount: int | None = Field(default=None)
    """How much recurring Kudos this user receives monthly."""

    last_received: datetime | None = Field(default=None)
    """Last date this user received monthly Kudos."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "MonthlyKudos"


class UserThingRecords(HordeAPIObjectBaseModel):
    """How many images, texts, megapixelsteps and tokens this user has generated or requested.

    v2 API Model: UserThingRecords
    """

    megapixelsteps: float | None = Field(0)
    """How many megapixelsteps this user has generated or requested."""

    tokens: int | None = Field(0)
    """How many token this user has generated or requested."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserThingRecords"


class UserAmountRecords(HordeAPIObjectBaseModel):
    """How many images, texts, megapixelsteps and tokens this user has generated or requested.

    v2 API Model: UserAmountRecords
    """

    image: int | None = Field(0)
    """How many images this user has generated or requested."""

    interrogation: int | None = Field(0)
    """How many texts this user has generated or requested."""

    text: int | None = Field(0)
    """How many texts this user has generated or requested."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserAmountRecords"


class UserRecords(HordeAPIObjectBaseModel):
    """How many images, texts, megapixelsteps, tokens and styles this user has generated, requested or has had used.

    v2 API Model: UserRecords
    """

    contribution: UserThingRecords | None = None
    """How much this user has contributed."""
    fulfillment: UserAmountRecords | None = None
    """How much this user has fulfilled."""
    request: UserAmountRecords | None = None
    """How much this user has requested."""
    usage: UserThingRecords | None = None
    """How much this user has used."""
    style: UserAmountRecords | None = None
    """How much this user's styles have been used."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserRecords"


class UsageDetails(HordeAPIObjectBaseModel):
    """How many images and megapixelsteps this user has requested.

    v2 API Model: UsageDetails
    """

    megapixelsteps: float | None = Field(default=None)
    """How many megapixelsteps this user has requested."""

    requests: int | None = Field(default=None)
    """How many images this user has requested."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UsageDetails"


@Unhashable
@Unequatable
class ActiveGenerations(HordeAPIObjectBaseModel):
    """A list of generations that are currently active for this user.

    v2 API Model: ActiveGenerations
    """

    """A list of generations that are currently active for this user."""

    text: list[UUID_Identifier] | None = None
    """The IDs of the text generations that are currently active for this user."""

    image: list[UUID_Identifier] | None = None
    """The IDs of the image generations that are currently active for this user."""

    alchemy: list[UUID_Identifier] | None = None
    """The IDs of the alchemy generations that are currently active for this user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ActiveGenerations"


@Unhashable
@Unequatable
class UserDetailsResponse(HordeResponseBaseModel):
    """The details of a user.

    v2 API Model: UserDetails
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserDetails"

    active_generations: ActiveGenerations | None = None
    """The active generations this user has requested."""

    admin_comment: str | None = Field(
        default=None,
    )
    """(Privileged) Comments from the horde admins about this user."""

    account_age: int | None = Field(
        default=None,
        examples=[60],
    )
    """How many seconds since this account was created."""

    concurrency: int | None = Field(
        default=None,
    )
    """How many concurrent generations this user may request."""

    contact: str | None = Field(
        default=None,
        examples=["email@examples.com"],
    )
    """(Privileged) Contact details for the horde admins to reach the user in case of emergency."""

    contributions: ContributionsDetails | None = None
    """How many images and megapixelsteps this user has generated."""

    customizer: bool | None = Field(
        default=None,
        examples=[False],
    )
    """If this user can run custom models."""

    evaluating_kudos: float | None = Field(
        default=None,
        description=(
            "(Privileged) The amount of Evaluating Kudos this untrusted user has from generations and uptime. When"
            " this number reaches a pre-specified threshold, they automatically become trusted."
        ),
    )
    """(Privileged) The amount of Evaluating Kudos this untrusted user has from generations and uptime.
    When this number reaches a pre-specified threshold, they automatically become trusted."""

    flagged: bool | None = Field(
        default=None,
        examples=[False],
    )
    """This user has been flagged for suspicious activity."""

    id_: int | None = Field(default=None, alias="id")
    """The user unique ID. It is always an integer."""

    kudos: float | None = Field(
        default=None,
        description=(
            "The amount of Kudos this user has. The amount of Kudos determines the priority when requesting image"
            " generations."
        ),
    )
    """The amount of Kudos this user has. The amount of Kudos determines the priority when requesting image
    generations."""

    kudos_details: UserKudosDetails | None = None
    """How much Kudos this user has accumulated or used for generating images."""

    moderator: bool | None = Field(default=None, examples=[False])
    """This user is a Horde moderator."""

    monthly_kudos: MonthlyKudos | None = None
    """How much recurring Kudos this user receives monthly."""

    pseudonymous: bool | None = Field(
        default=None,
        examples=[False],
    )
    """If true, this user has not registered using an oauth service."""

    records: UserRecords | None = None
    """How many images, texts, megapixelsteps and tokens this user has generated or requested."""

    sharedkey_ids: list[str] | None = None
    """The IDs of the shared keys this user has access to."""

    service: bool | None = Field(
        default=None,
        examples=[False],
    )
    """This user is a Horde service account and can provide the `proxied_user` field."""

    special: bool | None = Field(
        default=None,
        examples=[False],
    )
    """(Privileged) This user has been given the Special role."""

    suspicious: int | None = Field(
        default=None,
        examples=[0],
    )
    """(Privileged) How much suspicion this user has accumulated."""

    trusted: bool | None = Field(
        default=None,
        examples=[False],
    )
    """This user is a trusted member of the Horde."""

    usage: UsageDetails | None = None
    """How many images and megapixelsteps this user has requested."""

    username: str | None = Field(
        default=None,
    )
    """The user's unique Username. It is a combination of their chosen alias plus their ID."""

    vpn: bool | None = Field(
        default=None,
        examples=[False],
    )
    """(Privileged) This user has been given the VPN role."""

    education: bool | None = Field(
        default=None,
        examples=[False],
    )
    """(This user has been given the education role."""

    worker_count: int | None = Field(
        default=None,
    )
    """How many workers this user has created (active or inactive)."""

    worker_ids: list[str] | None = None
    """The IDs of the workers this user has created (active or inactive)."""

    worker_invited: int | None = Field(
        default=None,
        description=(
            "Whether this user has been invited to join a worker to the horde and how many of them. When 0, this user"
            " cannot add (new) workers to the horde."
        ),
    )
    """Whether this user has been invited to join a worker to the horde and how many of them.
    When 0, this user cannot add (new) workers to the horde."""

    styles: list[ResponseModelStylesUser] | None = None
    """The styles this user has created."""


@Unhashable
@Unequatable
class ListUsersDetailsResponse(HordeResponseRootModel[list[UserDetailsResponse]]):
    """The response for a list of user details.

    v2 API Model: _ANONYMOUS_MODEL
    """

    root: list[UserDetailsResponse]
    """The underlying list of user details."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class ListUsersDetailsRequest(BaseAIHordeRequest):
    """Represents a request to list all users."""

    page: int
    """The page number to request. There are up to 25 users per page."""

    sort: str = "kudos"
    """The field to sort the users by. The default is by kudos."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_users_all

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ListUsersDetailsResponse]:
        return ListUsersDetailsResponse

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["page", "sort"]


class SingleUserDetailsRequest(BaseAIHordeRequest, MessageSpecifiesUserIDMixin):

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_users_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[UserDetailsResponse]:
        return UserDetailsResponse


class _ModifyUserBase(HordeAPIObjectBaseModel):
    admin_comment: str | None = Field(
        default=None,
        max_length=500,
        min_length=5,
    )
    """Add further information about this user for the other admins."""

    concurrency: int | None = Field(
        default=None,
        ge=0,
        le=500,
    )
    """The amount of concurrent request this user can have."""

    contact: str | None = Field(
        default=None,
        examples=["email@example.com"],
        max_length=500,
        min_length=5,
    )
    """Contact details for the horde admins to reach the user in case of emergency. This is only visible to horde
    moderators."""

    customizer: bool | None = Field(
        default=None,
    )
    """When set to true, the user will be able to serve custom Stable Diffusion models which do not exist in the
    Official AI Horde Model Reference."""

    education: bool | None = Field(
        default=None,
    )
    """When set to true, the user is considered an education account and some options become more restrictive."""

    filtered: bool | None = Field(
        default=None,
    )
    """When set to true, the replacement filter will always be applied against this user"""

    flagged: bool | None = Field(
        default=None,
    )
    """When set to true, the user cannot transfer kudos and all their workers are put into permanent maintenance."""

    moderator: bool | None = Field(
        default=None,
    )
    """Set to true to make this user a horde moderator."""

    monthly_kudos: int | None = Field(
        default=None,
    )
    """When specified, will start assigning the user monthly kudos, starting now!"""

    public_workers: bool | None = Field(
        default=None,
    )
    """Set to true to make this user display their worker IDs."""

    service: bool | None = Field(
        default=None,
    )
    """When set to true, the user is considered a service account proxying the requests for other users."""

    special: bool | None = Field(
        default=None,
    )
    """When set to true, The user can send special payloads."""

    trusted: bool | None = Field(
        default=None,
    )
    """When set to true,the user and their servers will not be affected by suspicion."""

    usage_multiplier: float | None = Field(
        default=None,
        ge=0.1,
        le=10.0,
    )
    """The amount by which to multiply the users kudos consumption."""

    username: str | None = Field(
        default=None,
        max_length=100,
        min_length=3,
    )
    """When specified, will change the username. No profanity allowed!"""

    vpn: bool | None = Field(
        default=None,
    )
    """When set to true, the user will be able to onboard workers behind a VPN. This should be used as a temporary
    solution until the user is trusted."""

    worker_invited: int | None = Field(
        default=None,
    )
    """Set to the amount of workers this user is allowed to join to the horde when in worker invite-only mode."""


class ModifyUser(_ModifyUserBase):
    kudos: float | None = Field(default=None)
    """The amount of kudos to modify (can be negative)."""

    reset_suspicion: bool | None = Field(default=None)
    """Set the user's suspicion back to 0."""


class ModifyUserReply(_ModifyUserBase):
    new_kudos: float | None = Field(default=None)
    """The new amount of kudos this user has."""
    new_suspicion: int | None = Field(default=None)
    """The new amount of suspicion this user has."""


class ModifyUserResponse(HordeResponseBaseModel, ModifyUserReply):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModifyUser"


class ModifyUserRequest(
    BaseAIHordeRequest,
    MessageSpecifiesUserIDMixin,
    ModifyUser,
    APIKeyAllowedInRequestMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModifyUserInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PUT

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_users_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyUserResponse]:
        return ModifyUserResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
