from loguru import logger
from pydantic import field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE, KNOWN_ALCHEMY_TYPES, KNOWN_UPSCALERS
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIDataObject,
    HordeResponseBaseModel,
    ResponseWithProgressMixin,
)

# FIXME: All vs API models defs? (override get_api_model_name and add to docstrings)


class AlchemyUpscaleResult(HordeAPIDataObject):
    """Represents the result of an upscale job."""

    upscaler_used: KNOWN_UPSCALERS | str
    url: str


class AlchemyCaptionResult(HordeAPIDataObject):
    """Represents the result of a caption job."""

    caption: str


class AlchemyNSFWResult(HordeAPIDataObject):
    """Represents the result of an NSFW evaluation."""

    nsfw: bool


class AlchemyInterrogationResultItem(HordeAPIDataObject):
    """Represents an item in the result of an interrogation job."""

    text: str
    confidence: float


class AlchemyInterrogationDetails(HordeAPIDataObject):
    """The details of an interrogation job."""

    tags: list[AlchemyInterrogationResultItem]
    sites: list[AlchemyInterrogationResultItem]
    artists: list[AlchemyInterrogationResultItem]
    flavors: list[AlchemyInterrogationResultItem]
    mediums: list[AlchemyInterrogationResultItem]
    movements: list[AlchemyInterrogationResultItem]
    techniques: list[AlchemyInterrogationResultItem]


class AlchemyInterrogationResult(HordeAPIDataObject):
    """Represents the result of an interrogation job. Use the `interrogation` field for the details."""

    interrogation: AlchemyInterrogationDetails


class AlchemyFormStatus(HordeAPIDataObject):
    """Represents the status of a form in an interrogation job."""

    form: KNOWN_ALCHEMY_TYPES | str
    state: GENERATION_STATE
    result: AlchemyInterrogationDetails | AlchemyNSFWResult | AlchemyCaptionResult | AlchemyUpscaleResult | None = None

    @field_validator("form", mode="before")
    def validate_form(cls, v: str | KNOWN_ALCHEMY_TYPES) -> KNOWN_ALCHEMY_TYPES | str:
        if isinstance(v, KNOWN_ALCHEMY_TYPES):
            return v
        if str(v) not in KNOWN_ALCHEMY_TYPES.__members__:
            logger.warning(f"Unknown form type {v}. Is your SDK out of date or did the API change?")
        return v

    @property
    def done(self) -> bool:
        """Return whether the form is done."""
        return self.state == "done"

    @field_validator("result", mode="before")
    def validate_result(
        cls,
        v: dict[str, object],
    ) -> dict[str, object] | None:
        if "additionalProp1" in v:
            logger.debug("Found additionalProp1 in result, this is a dummy result. Ignoring.")
            return None

        for key in list(v.keys()):
            if key in KNOWN_UPSCALERS.__members__:
                v["upscaler_used"] = KNOWN_UPSCALERS(key)
                v["url"] = v[key]
                del v[key]

        return v


class AlchemyStatusResponse(HordeResponseBaseModel, ResponseWithProgressMixin):
    """The response from the `/v2/interrogate/status/{id}` endpoint.

    You will find the results of the alchemy here.

    v2 API Model: `InterrogationStatus`
    """

    state: GENERATION_STATE
    """The state of the job. See `GENERATION_STATE` for possible values."""
    forms: list[AlchemyFormStatus]
    """The status of each form in the job."""

    @property
    def all_interrogation_results(self) -> list[AlchemyInterrogationDetails]:
        """Return all completed interrogation results."""
        return [
            form.result for form in self.forms if form.done and isinstance(form.result, AlchemyInterrogationDetails)
        ]

    @property
    def all_nsfw_results(self) -> list[AlchemyNSFWResult]:
        """Return all completed nsfw results."""
        return [form.result for form in self.forms if form.done and isinstance(form.result, AlchemyNSFWResult)]

    @property
    def all_caption_results(self) -> list[AlchemyCaptionResult]:
        """Return all completed caption results."""
        return [form.result for form in self.forms if form.done and isinstance(form.result, AlchemyCaptionResult)]

    @property
    def all_upscale_results(self) -> list[AlchemyUpscaleResult]:
        """Return all completed upscale results."""
        return [form.result for form in self.forms if form.done and isinstance(form.result, AlchemyUpscaleResult)]

    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InterrogationStatus"

    @override
    def is_job_complete(self, number_of_result_expected: int) -> bool:
        found_results = 0
        if not self.forms:
            return False
        for form in self.forms:
            if form.state != "done":
                return False
            found_results += 1
        return found_results == number_of_result_expected

    @override
    def is_job_possible(self) -> bool:
        return True  # FIXME

    @override
    @classmethod
    def is_final_follow_up(cls) -> bool:
        return True

    @override
    @classmethod
    def get_finalize_success_request_type(cls) -> None:
        return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AlchemyStatusResponse):
            return False
        return self.state == other.state and all(form in other.forms for form in self.forms)

    def __hash__(self) -> int:
        return hash((self.state, tuple(self.forms)))


class AlchemyStatusRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
    APIKeyAllowedInRequestMixin,
):
    """Represents the data needed to make a request to the `/v2/interrogate/status/{id}` endpoint."""

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
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyStatusResponse]:
        return AlchemyStatusResponse


class AlchemyDeleteRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
):
    """Represents the data needed to make a request to the `/v2/interrogate/status/{id}` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyStatusResponse]:
        return AlchemyStatusResponse
