from datetime import datetime

from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeAPIDataObject, HordeResponseBaseModel
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class ContributionsDetails(HordeAPIDataObject):
    """How many images and megapixelsteps this user has generated."""

    fulfillments: int | None = Field(
        default=None,
    )
    megapixelsteps: float | None = Field(
        default=None,
    )


class UserKudosDetails(HordeAPIDataObject):
    """The details of the kudos this user has accumulated, used, sent and received."""

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


class MonthlyKudos(HordeAPIDataObject):
    amount: int | None = Field(default=None)
    """How much recurring Kudos this user receives monthly."""

    last_received: datetime | None = Field(default=None)
    """Last date this user received monthly Kudos."""


class UserThingRecords(HordeAPIDataObject):
    megapixelsteps: float | None = Field(0)
    """How many megapixelsteps this user has generated or requested."""

    tokens: int | None = Field(0)
    """How many token this user has generated or requested."""


class UserAmountRecords(HordeAPIDataObject):
    image: int | None = Field(0)
    """How many images this user has generated or requested."""

    interrogation: int | None = Field(0)
    """How many texts this user has generated or requested."""

    text: int | None = Field(0)
    """How many texts this user has generated or requested."""


class UserRecords(HordeAPIDataObject):
    contribution: UserThingRecords | None = None
    fulfillment: UserAmountRecords | None = None
    request: UserAmountRecords | None = None
    usage: UserThingRecords | None = None


class UsageDetails(HordeAPIDataObject):
    megapixelsteps: float | None = Field(default=None)
    """How many megapixelsteps this user has requested."""

    requests: int | None = Field(default=None)
    """How many images this user has requested."""


@Unhashable
@Unequatable
class FindUserResponse(HordeResponseBaseModel):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserDetails"

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


class FindUserRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_find_user

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[FindUserResponse]:
        return FindUserResponse
