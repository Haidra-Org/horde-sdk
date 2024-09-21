from __future__ import annotations

from loguru import logger
from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.alchemy._submit import AlchemyJobSubmitRequest
from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    JobRequestMixin,
)
from horde_sdk.ai_horde_api.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObject,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


# FIXME
class AlchemyFormPayloadStable(HordeAPIObject):
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


class AlchemyPopFormPayload(HordeAPIObject, JobRequestMixin):
    """v2 API Model: `InterrogationPopFormPayload`."""

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


class NoValidAlchemyFound(HordeAPIObject):
    """v2 API Model: `NoValidInterrogationsFoundStable`."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidInterrogationsFoundStable"

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


class AlchemyPopResponse(HordeResponseBaseModel, ResponseRequiringFollowUpMixin):
    """v2 API Model: `InterrogationPopPayload`."""

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

    @model_validator(mode="after")
    def coerce_list_order(self) -> AlchemyPopResponse:
        if self.forms is not None:
            logger.debug("Sorting forms by id")
            self.forms.sort(key=lambda form: form.id_)

        return self

    @override
    @classmethod
    def get_follow_up_request_types(cls) -> list[type[AlchemyJobSubmitRequest]]:  # type: ignore[override]
        """Return a list of all the possible follow up request types for this response."""
        return [AlchemyJobSubmitRequest]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AlchemyPopResponse):
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

        return hash((tuple([form.id_ for form in self.forms]), self.skipped))


class AlchemyPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Represents the data needed to make a request to the `/v2/interrogate/pop` endpoint.

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
    def get_default_success_response_type(cls) -> type[AlchemyPopResponse]:
        return AlchemyPopResponse
