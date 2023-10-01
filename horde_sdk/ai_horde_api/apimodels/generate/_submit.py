from loguru import logger
from pydantic import field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin, JobSubmitResponse
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin


class ImageGenerationJobSubmitRequest(BaseAIHordeRequest, JobRequestMixin, APIKeyAllowedInRequestMixin):
    """Represents the data needed to make a job submit 'request' from a worker to the /v2/generate/submit endpoint.

    v2 API Model: `SubmitInputStable`
    """

    generation: str = ""
    """R2 result was uploaded to R2, else the string of the result."""
    state: GENERATION_STATE
    """The state of this generation."""
    seed: int = -1
    """The seed for this generation."""
    censored: bool = False
    """If True, this resulting image has been censored."""

    @field_validator("generation", "seed")
    def validate_generation(cls, value: str) -> str:
        if value == "":
            logger.warning("Generation or seed is empty. If the generation didn't fail, this is a bug!")
        return value

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SubmitInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_submit

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[JobSubmitResponse]:
        return JobSubmitResponse
