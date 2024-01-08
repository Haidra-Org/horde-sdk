from loguru import logger
from pydantic import BaseModel, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE, KNOWN_ALCHEMY_TYPES, KNOWN_UPSCALERS
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeResponseBaseModel,
    ResponseWithProgressMixin,
)

# FIXME: All vs API models defs? (override get_api_model_name and add to docstrings)


class AlchemyUpscaleResult(BaseModel):
    """Represents the result of an upscale job."""

    upscaler_used: KNOWN_UPSCALERS | str
    url: str


class AlchemyCaptionResult(BaseModel):
    """Represents the result of a caption job."""

    caption: str


class AlchemyNSFWResult(BaseModel):
    """Represents the result of an NSFW evaluation."""

    nsfw: bool


class AlchemyInterrogationResultItem(BaseModel):
    """Represents an item in the result of an interrogation job."""

    text: str
    confidence: float


class AlchemyInterrogationDetails(BaseModel):
    """The details of an interrogation job."""

    tags: list[AlchemyInterrogationResultItem]
    sites: list[AlchemyInterrogationResultItem]
    artists: list[AlchemyInterrogationResultItem]
    flavors: list[AlchemyInterrogationResultItem]
    mediums: list[AlchemyInterrogationResultItem]
    movements: list[AlchemyInterrogationResultItem]
    techniques: list[AlchemyInterrogationResultItem]


class AlchemyInterrogationResult(BaseModel):
    """Represents the result of an interrogation job. Use the `interrogation` field for the details."""

    interrogation: AlchemyInterrogationDetails


class AlchemyFormStatus(BaseModel):
    """Represents the status of a form in an interrogation job."""

    form: KNOWN_ALCHEMY_TYPES
    state: GENERATION_STATE
    result: AlchemyInterrogationDetails | AlchemyNSFWResult | AlchemyCaptionResult | AlchemyUpscaleResult | None = None

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
    forms: list[AlchemyFormStatus]

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
