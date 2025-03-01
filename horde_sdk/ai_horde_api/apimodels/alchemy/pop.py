from __future__ import annotations

from loguru import logger
from pydantic import Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.alchemy.submit import AlchemyJobSubmitRequest
from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    JobRequestMixin,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


# FIXME
class AlchemyFormPayloadStable(HordeAPIObjectBaseModel):
    """Currently unsupported.

    v2 API Model: `ModelInterrogationFormPayloadStable`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModelInterrogationFormPayloadStable"

    additionalProp1: str = Field(
        validation_alias="additionalProp1",
    )
    """Currently unsupported."""
    additionalProp2: str = Field(
        validation_alias="additionalProp2",
    )
    """Currently unsupported."""
    additionalProp3: str = Field(
        validation_alias="additionalProp3",
    )
    """Currently unsupported."""


class AlchemyPopFormPayload(HordeAPIObjectBaseModel, JobRequestMixin):
    """Contains the data for a single alchemy generation form for workers (pop).

    v2 API Model: `InterrogationPopFormPayload`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopFormPayload"

    form: KNOWN_ALCHEMY_TYPES | str = Field(
        examples=["caption"],
    )
    """The name of this interrogation form."""

    @field_validator("form", mode="before")
    def validate_form(cls, v: str | KNOWN_ALCHEMY_TYPES) -> KNOWN_ALCHEMY_TYPES | str:
        if isinstance(v, KNOWN_ALCHEMY_TYPES):
            return v
        if isinstance(v, str) and v not in KNOWN_ALCHEMY_TYPES.__members__:
            logger.warning(f"Unknown form type {v}")
        return v

    payload: AlchemyFormPayloadStable | None = None
    """The setting for this interrogation form."""
    r2_upload: str | None = Field(
        default=None,
    )
    """The URL in which the post-processed image can be uploaded."""
    source_image: str | None = Field(
        default=None,
    )
    """The URL From which the source image can be downloaded."""


class NoValidAlchemyFound(HordeAPIObjectBaseModel):
    """The number of jobs this worker was not eligible for, and why.

    v2 API Model: `NoValidInterrogationsFound`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidInterrogationsFound"

    bridge_version: int | None = Field(
        default=None,
        description=(
            "How many waiting requests were skipped because they require a higher version of the bridge than this"
            " worker is running (upgrade if you see this in your skipped list)."
        ),
        examples=[0],
        ge=0,
    )
    """How many waiting requests were skipped because they require a higher version of the bridge than this worker is
    running (upgrade if you see this in your skipped list)."""
    untrusted: int | None = Field(
        default=None,
        description=(
            "How many waiting requests were skipped because they demanded a trusted worker which this worker is not."
        ),
        ge=0,
    )
    """How many waiting requests were skipped because they demanded a trusted worker which this worker is not."""
    worker_id: int | None = Field(
        default=None,
        ge=0,
    )
    """How many waiting requests were skipped because they demanded a specific worker."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NoValidAlchemyFound):
            return False

        return (
            self.bridge_version == other.bridge_version
            and self.untrusted == other.untrusted
            and self.worker_id == other.worker_id
        )

    def __hash__(self) -> int:
        return hash((self.bridge_version, self.untrusted, self.worker_id))


class AlchemyJobPopResponse(HordeResponseBaseModel, ResponseRequiringFollowUpMixin):
    """Contains job data for workers, if any were available. Also contains data for jobs this worker was skipped for.

    This is the key response type for all alchemy workers as it contains all assignment data for the worker.

    Represents the data returned from the /v2/interrogate/pop endpoint with http status code 200.

    v2 API Model: `InterrogationPopPayload`
    """

    # and not actually specifying a schema
    forms: list[AlchemyPopFormPayload] | None = None
    """The forms that to be generated"""
    skipped: NoValidAlchemyFound | None = None
    """The requests that were skipped because this worker were not eligible for them."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopPayload"

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if not self.forms:
            return []
        all_ids: list[dict[str, object]] = []
        for form in self.forms:
            if not isinstance(form, AlchemyPopFormPayload):
                logger.warning(f"Skipping form {form} as it is not an AlchemyPopFormPayload")
                continue
            if form.id_:
                if as_python_field_name:
                    all_ids.append({"id_": form.id_})
                else:
                    all_ids.append({"id": form.id_})

        return all_ids

    @override
    @classmethod
    def get_follow_up_request_types(cls) -> list[type[AlchemyJobSubmitRequest]]:  # type: ignore[override]
        """Return a list of all the possible follow up request types for this response."""
        return [AlchemyJobSubmitRequest]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AlchemyJobPopResponse):
            return False

        forms_match = True
        skipped_match = True

        if self.forms is not None and other.forms is not None:
            forms_match = all(form in other.forms for form in self.forms)

        if self.skipped is not None:
            skipped_match = self.skipped == other.skipped

        return forms_match and skipped_match

    def __hash__(self) -> int:
        if self.forms is None:
            return hash(self.skipped)

        return hash((tuple(sorted([form.id_ for form in self.forms])), self.skipped))

    @property
    def ids(self) -> list[GenerationID]:
        """Return a list of all the ids in the response."""
        if self.forms is None:
            return []
        return [form.id_ for form in self.forms]

    @property
    def ids_present(self) -> bool:
        """Return whether the response has any ids."""
        return bool(self.ids)


class AlchemyPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Request additional jobs, if any are available, for an alchemy worker.

    This is the key request type for all alchemy workers as it requests all available jobs for the worker.

    Represents a POST request to the /v2/interrogate/pop endpoint.

    v2 API Model: `InterrogationPopInput`
    """

    name: str
    """The name of the request. This is used to identify the request in the logs."""
    priority_usernames: list[str]
    """The usernames that should be prioritized for this request."""
    forms: list[KNOWN_ALCHEMY_TYPES]
    """The types of alchemy that should be generated."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationPopInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_pop

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyJobPopResponse]:
        return AlchemyJobPopResponse
