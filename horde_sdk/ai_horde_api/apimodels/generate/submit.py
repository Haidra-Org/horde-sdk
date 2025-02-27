from __future__ import annotations

from loguru import logger
from pydantic import model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    GenMetadataEntry,
    JobRequestMixin,
    JobSubmitResponse,
)
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin


class ImageGenerationJobSubmitRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
    APIKeyAllowedInRequestMixin,
):
    """Represents the data needed to make a job submit 'request' from a worker to the /v2/generate/submit endpoint.

    v2 API Model: `SubmitInputStable`
    """

    generation: str = ""
    """R2 result was uploaded to R2, else the string of the result."""
    state: GENERATION_STATE
    """The state of this generation."""
    seed: int = 0
    """The seed for this generation."""
    censored: bool = False
    """If True, this resulting image has been censored."""
    gen_metadata: list[GenMetadataEntry] | None = None
    """Extra metadata about faulted or defaulted components of the generation"""

    @model_validator(mode="after")
    def validate_generation(self) -> ImageGenerationJobSubmitRequest:
        if self.generation == "":
            logger.error("Generation cannot be an empty string.")
            logger.error(self.log_safe_model_dump())

        if self.seed == 0:
            logger.debug(f"Seed is 0 for {self.id_}. That might not be intended.")
            logger.debug(self.log_safe_model_dump())

        return self

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
