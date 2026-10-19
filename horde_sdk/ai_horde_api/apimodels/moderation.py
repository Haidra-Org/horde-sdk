"""Models and authenticated requests for moderator review and retained evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, override

from pydantic import Field

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseTypes,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


@Unhashable
@Unequatable
class ModerationSuspicionReason(HordeAPIObjectBaseModel):
    """An active suspicion reason and its report count.

    v2 API Model: `ModerationSuspicionReason`
    """

    id_: int | None = Field(default=None, alias="id")
    """Stable numeric suspicion reason code."""

    name: str | None = None
    """Stable symbolic suspicion reason name."""

    description: str | None = None
    """Human-readable reason."""

    count: int | None = None
    """Number of currently active reports for this reason."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModerationSuspicionReason"


@Unhashable
@Unequatable
class PromotionReviewUser(HordeAPIObjectBaseModel):
    """An account awaiting moderator review of automatic promotion.

    v2 API Model: `PromotionReviewUser`
    """

    id_: int | None = Field(default=None, alias="id")
    """The user unique ID. It is always an integer."""

    username: str | None = None
    """The user's unique Username. It is a combination of their chosen alias plus their ID."""

    last_active: datetime | None = None
    """The UTC time the account was last active."""

    account_age: int | None = None
    """How many seconds since this account was created."""

    kudos: float | None = None
    """The amount of Kudos this user has. The amount of Kudos determines the priority when requesting image
    generations."""

    evaluating_kudos: float | None = None
    """(Privileged) The amount of Evaluating Kudos this untrusted user has from generations and uptime. When this
    number reaches a prespecified threshold, they automatically become trusted."""

    suspicious: int | None = None
    """(Privileged) How much suspicion this user has accumulated."""

    suspicion_reasons: list[ModerationSuspicionReason] | None = None
    """The active suspicion reasons, by code."""

    flagged: bool | None = None
    """(Privileged) This user has been flagged for suspicious activity."""

    deleted: bool | None = None
    """This user has been marked for deletion."""

    vpn: bool | None = None
    """(Privileged) This user has been given the VPN role."""

    worker_count: int | None = None
    """How many workers this user has created (active or inactive)."""

    paused_worker_count: int | None = None
    """The number of the account's workers that are paused."""

    worker_kudos: float | None = None
    """The kudos the account's workers earned."""

    worker_fulfilments: int | None = None
    """The number of jobs the account's workers fulfilled."""

    contact: str | None = None
    """(Privileged) Contact details for the horde admins to reach the user in case of emergency."""

    admin_comment: str | None = None
    """(Privileged) Information about this users by the admins"""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromotionReviewUser"


@Unhashable
@Unequatable
class PausedWorkerReview(HordeAPIObjectBaseModel):
    """A paused worker and the account and suspicion details needed to review it.

    v2 API Model: `PausedWorkerReview`
    """

    type_: Literal["image", "text", "interrogation"] | None = Field(default=None, alias="type")
    """The Type of worker this is."""

    name: str | None = None
    """The Name given to this worker."""

    id_: str | None = Field(default=None, alias="id")
    """The UUID of this worker."""

    online: bool | None = None
    """True if the worker has checked-in the past 5 minutes."""

    owner_id: int | None = None
    """The owning account's ID."""

    owner: str | None = None
    """Privileged or public if the owner has allowed it. The alias of the owner of this worker."""

    last_check_in: datetime | None = None
    """The UTC time the worker last checked in."""

    maintenance_mode: bool | None = None
    """When True, this worker will not pick up any new requests."""

    maintenance_msg: str | None = None
    """The maintenance message."""

    suspicious: int | None = None
    """(Privileged) How much suspicion this worker has accumulated."""

    suspicion_reasons: list[ModerationSuspicionReason] | None = None
    """The active suspicion reasons, by code."""

    owner_suspicion: int | None = None
    """(Privileged) How much suspicion this user has accumulated."""

    owner_trusted: bool | None = None
    """Whether the owning account is trusted."""

    owner_flagged: bool | None = None
    """(Privileged) This user has been flagged for suspicious activity."""

    requests_fulfilled: int | None = None
    """How many images this worker has generated."""

    aborted_jobs: int | None = None
    """The number of jobs the worker aborted."""

    bridge_agent: str | None = None
    """The bridge agent name, version and website."""

    models: list[str] | None = None
    """The models reported by the API."""

    contact: str | None = None
    """(Privileged) Contact details for the horde admins to reach the owner of this worker in emergencies."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PausedWorkerReview"


@Unhashable
@Unequatable
class PromptModerationNote(HordeResponseBaseModel):
    """A moderator's note on a retained prompt event.

    Represents the data returned from the /v2/operations/moderation/prompts/{event_id}/notes endpoint with http
    status code 201.

    v2 API Model: `PromptModerationNote`
    """

    id_: int | None = Field(default=None, alias="id")
    """Note identifier."""

    author_id: int | None = None
    """Moderator who wrote the note."""

    note: str | None = None
    """Note text, at most 2000 characters."""

    created: datetime | None = None
    """UTC time the note was written."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromptModerationNote"


@Unhashable
@Unequatable
class PromptModerationRetention(HordeAPIObjectBaseModel):
    """Retention windows for prompt text, addresses, and identifying information.

    v2 API Model: `PromptModerationRetention`
    """

    text_days: int | None = None
    """Days until prompt stages are removed from an event not under moderation action; null keeps them until
    anonymization."""

    ipaddr_days: int | None = None
    """Days until the address is removed from an event not under moderation action; null keeps it until
    anonymization."""

    ceiling_days: int | None = None
    """Days until an event not under moderation action is anonymized; the reason, outcome, models, capture time,
    reporting worker and notes are kept. An event with a note, or of a flagged or suspicious account, is kept
    whole."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromptModerationRetention"


@Unhashable
@Unequatable
class PromptModerationEvent(HordeAPIObjectBaseModel):
    """Retained evidence of a rejected or censored prompt.

    v2 API Model: `PromptModerationEvent`
    """

    id_: int | None = Field(default=None, alias="id")
    """Evidence identifier, also the pagination cursor."""

    created: datetime | None = None
    """UTC capture time in ISO 8601 with a +00:00 offset."""

    user_id: int | None = None
    """Submitting account; null once the event is anonymized."""

    request_id: str | None = None
    """Waiting request ID; null for a rejected submission."""

    worker_id: str | None = None
    """Worker that reported the job, for worker reports; it identifies the reporter, not the subject."""

    proxied_account: str | None = None
    """Service-account subject, when one was supplied."""

    ipaddr: str | None = None
    """Submitting address; an IPv6 address is recorded as its /64 network."""

    ip_subject_key: str | None = None
    """Address pseudonym, equal for events from the same IPv4 address or IPv6 /64; it outlives ipaddr and is null
    once the event is anonymized. Group or filter events by it; it is not an address."""

    origin_text: str | None = None
    """The origin as a trusted proxy reported it when it was not an IP address; null otherwise or once the address
    window has passed."""

    models: list[str] | None = None
    """Model names the request asked for."""

    reason: Literal["filter_rejection", "model_rejection", "worker_csam"] | None = None
    """Why the evidence was retained."""

    outcome: Literal["rejected", "censored"] | None = None
    """What happened to the request."""

    submitted_prompt: str | None = None
    """Original submission; null when provenance is unknown or text_state is not pending."""

    moderation_prompt: str | None = None
    """Moderation input after style expansion, when known; null when text_state is not pending."""

    effective_prompt: str | None = None
    """Prompt a worker received; null for a rejection or when text_state is not pending."""

    text_state: Literal["pending", "stored", "none"] | None = None
    """Where the prompt stages are held: pending (inline in this event until uploaded), stored (in object storage,
    read through text_url) or none (no text is held)."""

    text_url: str | None = None
    """Short-lived link to the stored prompt stages as JSON; null unless text_state is stored and object storage is
    configured."""

    text_sha256: str | None = None
    """Hex SHA-256 of the stored object, the canonical JSON of the clipped prompt stages. It is recorded even when
    capture kept no text, and retention removes it with the text."""

    text_chars: int | None = None
    """Total characters of the clipped prompt stages; retention removes it with the text."""

    text_truncated: bool | None = None
    """A prompt stage exceeded the evidence length limit."""

    text_redacted: bool | None = None
    """Retention ran its text step on the event, past the text window or at anonymization, whether or not there was
    prompt text to remove."""

    ipaddr_redacted: bool | None = None
    """Retention ran its address step on the event, past the address window or at anonymization, whether or not there
    was an address to remove."""

    anonymized: bool | None = None
    """Retention removed the account, proxied account, address, address pseudonym, request and job identifiers and
    prompt stages; notes are kept."""

    hold_source: Literal["note", "account_status"] | None = None
    """Why retention keeps the event whole: note (it has a moderator note) or account_status (its account is flagged
    or suspicious), note when both apply; null when the retention windows apply. Derived when the listing is read
    from the conditions retention checks; it is not stored and cannot be released."""

    notes: list[PromptModerationNote] | None = None
    """Moderator notes, oldest first."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromptModerationEvent"


@Unhashable
@Unequatable
class WorkerSuspicionEvent(HordeAPIObjectBaseModel):
    """A historical suspicion report against a worker.

    v2 API Model: `WorkerSuspicionEvent`
    """

    id_: int | None = Field(default=None, alias="id")
    """The record identifier, also the pagination cursor."""

    created: datetime | None = None
    """UTC time the suspicion was recorded."""

    worker_id: str | None = None
    """The UUID of the worker the suspicion was raised against."""

    worker_name: str | None = None
    """The worker's name when the suspicion was recorded."""

    user_id: int | None = None
    """The account that owned the worker when the suspicion was recorded."""

    suspicion_id: int | None = None
    """The numeric suspicion reason code."""

    reason: str | None = None
    """The reason's Suspicions name, or UNKNOWN_<id> for a code this version does not define."""

    detail: str | None = None
    """The suspicion's diagnostic text."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "WorkerSuspicionEvent"


@Unhashable
@Unequatable
class ModerationOverview(HordeResponseBaseModel):
    """Promotion exceptions and paused workers for moderator review.

    Represents the data returned from the /v2/operations/moderation endpoint with http status code 200.

    v2 API Model: `ModerationOverview`
    """

    promotion_threshold: float | None = None
    """The evaluating kudos above which automatic promotion applies; null when it has no configured threshold."""

    suspicion_threshold: int | None = None
    """The report count at which an account counts as suspicious."""

    worker_suspicion_threshold: int | None = None
    """The report count at which a worker counts as suspicious."""

    promotion_blocked_users: list[PromotionReviewUser] | None = None
    """Accounts that meet every promotion criterion but suspicion, highest evaluating kudos first."""

    promotion_eligible_users: list[PromotionReviewUser] | None = None
    """Accounts automatic promotion will trust, highest evaluating kudos first."""

    paused_workers: list[PausedWorkerReview] | None = None
    """Paused workers matching the filters, in the requested order."""

    paused_workers_total: int | None = None
    """Paused workers matching the filters, including those past the limit."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModerationOverview"


@Unhashable
@Unequatable
class PromptModerationEvents(HordeResponseBaseModel):
    """A cursor-paginated page of retained prompt evidence.

    Represents the data returned from the /v2/operations/moderation/prompts endpoint with http status code 200.

    v2 API Model: `PromptModerationEvents`
    """

    events: list[PromptModerationEvent] | None = None
    """The events reported by the API."""

    next_cursor: int | None = None
    """Pass as before_id to read the next page; null on the last page."""

    retention: PromptModerationRetention | None = None
    """Retention windows in force, counted from capture; they apply only to events not under moderation action."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromptModerationEvents"


@Unhashable
@Unequatable
class WorkerSuspicionEvents(HordeResponseBaseModel):
    """A cursor-paginated page of historical worker suspicion reports.

    Represents the data returned from the /v2/operations/moderation/worker_suspicion_events endpoint with http
    status code 200.

    v2 API Model: `WorkerSuspicionEvents`
    """

    events: list[WorkerSuspicionEvent] | None = None
    """The events reported by the API."""

    next_cursor: int | None = None
    """Pass as before_id to read the next page; null on the last page."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "WorkerSuspicionEvents"


class _ModerationRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """An authenticated GET restricted to moderator API keys."""

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
    def is_api_key_required(cls) -> bool:
        return True


@Unhashable
@Unequatable
class ModerationOverviewRequest(_ModerationRequest):
    """Return promotion exceptions and paused workers for moderator review.

    Represents a GET request to the /v2/operations/moderation endpoint.
    """

    limit: int | None = None
    """Maximum rows returned in each review section (1-500)."""

    worker_type: list[Literal["image", "text", "interrogation"]] | None = None
    """Paused workers of these types; repeatable."""

    suspicion_id: list[int] | None = None
    """Paused workers carrying any of these suspicion reasons; repeatable."""

    online: bool | None = None
    """Paused workers that checked in within five minutes (true) or not (false)."""

    sort: Literal["suspicion", "last_check_in", "name", "owner"] | None = None
    """Paused-worker order."""

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["limit", "worker_type", "suspicion_id", "online", "sort"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_moderation

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModerationOverview]:
        return ModerationOverview


@Unhashable
@Unequatable
class PromptModerationEventsRequest(_ModerationRequest):
    """Return a bounded evidence page filtered by subject, time, or ID range.

    Represents a GET request to the /v2/operations/moderation/prompts endpoint.
    """

    limit: int | None = None
    """Rows per page (1-100)."""

    before_id: int | None = None
    """Exclusive descending cursor."""

    event_id: int | None = None
    """Restrict to one event; the event_id of a moderator alert link."""

    user_id: int | None = None
    """Restrict to one account."""

    proxied_account: str | None = None
    """Restrict to one proxied account."""

    ipaddr: str | None = None
    """Restrict to one IP subject, including events whose address retention removed.

    An IPv6 address selects its /64."""

    ip_subject_key: str | None = None
    """Restrict to one address pseudonym, the ip_subject_key of an event."""

    worker_id: str | None = None
    """Restrict to one reporting worker."""

    reason: list[str] | None = None
    """Restrict to events of any of these reasons; repeatable."""

    since: str | None = None
    """Inclusive ISO 8601 lower bound."""

    until: str | None = None
    """Exclusive ISO 8601 upper bound."""

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return [
            "limit",
            "before_id",
            "event_id",
            "user_id",
            "proxied_account",
            "ipaddr",
            "ip_subject_key",
            "worker_id",
            "reason",
            "since",
            "until",
        ]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_moderation_prompts

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[PromptModerationEvents]:
        return PromptModerationEvents


@Unhashable
@Unequatable
class WorkerSuspicionEventsRequest(_ModerationRequest):
    """Return a cursor-paginated page of worker suspicion history, newest first.

    Represents a GET request to the /v2/operations/moderation/worker_suspicion_events endpoint.
    """

    limit: int | None = None
    """Rows per page (1-500)."""

    before_id: int | None = None
    """Exclusive descending cursor."""

    worker_id: str | None = None
    """Restrict to one worker UUID."""

    user_id: int | None = None
    """Restrict to one owning account."""

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["limit", "before_id", "worker_id", "user_id"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_worker_suspicion_events

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[WorkerSuspicionEvents]:
        return WorkerSuspicionEvents


class PromptModerationNoteRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Append a moderator note to a retained evidence event.

    Represents a POST request to the /v2/operations/moderation/prompts/{event_id}/notes endpoint.

    v2 API Model: `PromptModerationNoteInput`
    """

    event_id: int
    """The retained event to annotate."""

    note: str = Field(min_length=1, max_length=2000, pattern=r"^[^\x00]*$")
    """The moderator's note, without NUL bytes."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "PromptModerationNoteInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_operations_moderation_prompt_notes

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[PromptModerationNote]:
        return PromptModerationNote

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponseTypes]]:
        return {HTTPStatusCode.CREATED: PromptModerationNote}

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
