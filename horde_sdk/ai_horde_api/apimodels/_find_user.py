from datetime import datetime

from pydantic import BaseModel, Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin, HordeResponseBaseModel


class ContributionsDetails(BaseModel):
    fulfillments: int | None = Field(default=None, description="How many images this user has generated.")
    megapixelsteps: float | None = Field(default=None, description="How many megapixelsteps this user has generated.")


class UserKudosDetails(BaseModel):
    accumulated: float | None = Field(0, description="The amount of Kudos accumulated or used for generating images.")
    admin: float | None = Field(0, description="The amount of Kudos this user has been given by the Horde admins.")
    awarded: float | None = Field(
        0,
        description="The amount of Kudos this user has been awarded from things like rating images.",
    )
    gifted: float | None = Field(0, description="The amount of Kudos this user has given to other users.")
    received: float | None = Field(0, description="The amount of Kudos this user has been given by other users.")
    recurring: float | None = Field(
        0,
        description="The amount of Kudos this user has received from recurring rewards.",
    )


class MonthlyKudos(BaseModel):
    amount: int | None = Field(default=None, description="How much recurring Kudos this user receives monthly.")
    last_received: datetime | None = Field(default=None, description="Last date this user received monthly Kudos.")


class UserThingRecords(BaseModel):
    megapixelsteps: float | None = Field(
        0,
        description="How many megapixelsteps this user has generated or requested.",
    )
    tokens: int | None = Field(0, description="How many token this user has generated or requested.")


class UserAmountRecords(BaseModel):
    image: int | None = Field(0, description="How many images this user has generated or requested.")
    interrogation: int | None = Field(0, description="How many texts this user has generated or requested.")
    text: int | None = Field(0, description="How many texts this user has generated or requested.")


class UserRecords(BaseModel):
    contribution: UserThingRecords | None = None
    fulfillment: UserAmountRecords | None = None
    request: UserAmountRecords | None = None
    usage: UserThingRecords | None = None


class UsageDetails(BaseModel):
    megapixelsteps: float | None = Field(default=None, description="How many megapixelsteps this user has requested.")
    requests: int | None = Field(default=None, description="How many images this user has requested.")


class FindUserResponse(HordeResponseBaseModel):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UserDetails"

    account_age: int | None = Field(
        default=None,
        description="How many seconds since this account was created.",
        examples=[60],
    )
    """How many seconds since this account was created."""
    concurrency: int | None = Field(default=None, description="How many concurrent generations this user may request.")
    """How many concurrent generations this user may request."""

    contact: str | None = Field(
        default=None,
        description="(Privileged) Contact details for the horde admins to reach the user in case of emergency.",
        examples=["email@examples.com"],
    )
    """(Privileged) Contact details for the horde admins to reach the user in case of emergency."""
    contributions: ContributionsDetails | None = None
    """How many images and megapixelsteps this user has generated."""

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
        description="This user has been flagged for suspicious activity.",
        examples=[False],
    )
    """This user has been flagged for suspicious activity."""
    id_: int | None = Field(default=None, description="The user unique ID. It is always an integer.", alias="id")
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
    moderator: bool | None = Field(default=None, description="This user is a Horde moderator.", examples=[False])
    """This user is a Horde moderator."""
    monthly_kudos: MonthlyKudos | None = None
    """How much recurring Kudos this user receives monthly."""
    pseudonymous: bool | None = Field(
        default=None,
        description="If true, this user has not registered using an oauth service.",
        examples=[False],
    )
    """If true, this user has not registered using an oauth service."""
    records: UserRecords | None = None
    """How many images, texts, megapixelsteps and tokens this user has generated or requested."""
    sharedkey_ids: list[str] | None = None
    """The IDs of the shared keys this user has access to."""
    special: bool | None = Field(
        default=None,
        description="(Privileged) This user has been given the Special role.",
        examples=[False],
    )
    """(Privileged) This user has been given the Special role."""
    suspicious: int | None = Field(
        default=None,
        description="(Privileged) How much suspicion this user has accumulated.",
        examples=[0],
    )
    """(Privileged) How much suspicion this user has accumulated."""
    trusted: bool | None = Field(
        default=None,
        description="This user is a trusted member of the Horde.",
        examples=[False],
    )
    """This user is a trusted member of the Horde."""
    usage: UsageDetails | None = None
    """How many images and megapixelsteps this user has requested."""
    username: str | None = Field(
        default=None,
        description="The user's unique Username. It is a combination of their chosen alias plus their ID.",
    )
    """The user's unique Username. It is a combination of their chosen alias plus their ID."""
    vpn: bool | None = Field(
        default=None,
        description="(Privileged) This user has been given the VPN role.",
        examples=[False],
    )
    """(Privileged) This user has been given the VPN role."""
    worker_count: int | None = Field(
        default=None,
        description="How many workers this user has created (active or inactive).",
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
    def get_http_method(self) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(self) -> type[FindUserResponse]:
        return FindUserResponse
