from loguru import logger
from pydantic import BaseModel, RootModel, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    BaseResponse,
    ResponseWithProgressMixin,
)

# FIXME: All vs API models defs? (override get_api_model_name and add to docstrings)


class AlchemyUpscaleResult(RootModel[str]):
    """Represents the result of an upscale job."""


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

    form: str
    state: str
    result: AlchemyInterrogationDetails | AlchemyNSFWResult | AlchemyCaptionResult | AlchemyUpscaleResult | None = None

    @field_validator("result", mode="before")
    def validate_result(
        cls,
        v: dict[str, object],
    ) -> dict[str, object] | None:
        if "additionalProp1" in v:
            logger.debug("Found additionalProp1 in result, this is a dummy result. Ignoring.")
            return None
        return v


class AlchemyStatusResponse(BaseResponse, ResponseWithProgressMixin):
    """The response from the `/v2/interrogate/status/{id}` endpoint.

    You will find the results of the alchemy here.

    v2 API Model: `InterrogationStatus`
    """

    state: str
    forms: list[AlchemyFormStatus]

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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_interrogate_status

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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_interrogate_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyStatusResponse]:
        return AlchemyStatusResponse
