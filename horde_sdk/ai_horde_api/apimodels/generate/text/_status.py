import uuid

from loguru import logger
from pydantic import Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, GenMetadataEntry, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate._progress import ResponseGenerationProgressInfoMixin
from horde_sdk.ai_horde_api.apimodels.generate._status import Generation
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import HordeResponseBaseModel, ResponseWithProgressMixin


class GenerationKobold(Generation):
    id_: str | None = Field(default=None, title="Generation ID")
    """The ID for this generation."""
    gen_metadata: list[GenMetadataEntry] | None = None  # FIXME: API declares a `GenerationMetadataKobold` here
    """Extra metadata about faulted or defaulted components of the generation."""
    seed: int | None = Field(0, title="Generation Seed")
    """The seed which generated this text."""
    text: str | None = Field(default=None, min_length=0, title="Generated Text")
    """The generated text."""

    @override
    @classmethod
    def get_api_model_name(self) -> str | None:
        return "GenerationKobold"

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GenerationKobold):
            return False
        return self.id_ == other.id_

    def __hash__(self) -> int:
        return hash(GenerationKobold.__name__) + hash(self.id_)


class TextGenerateStatusResponse(
    HordeResponseBaseModel,
    ResponseWithProgressMixin,
    ResponseGenerationProgressInfoMixin,
):
    generations: list[GenerationKobold] = Field(
        default_factory=list,
        title="Generations",
    )
    """The generations that have been completed in this request."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestStatusKobold"

    @override
    @classmethod
    def get_finalize_success_request_type(cls) -> None:
        return None

    @override
    def is_job_complete(self, number_of_result_expected: int) -> bool:
        return len(self.generations) == number_of_result_expected

    @override
    def is_job_possible(self) -> bool:
        return self.is_possible

    @override
    @classmethod
    def is_final_follow_up(cls) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextGenerateStatusResponse):
            return False
        return all(gen in other.generations for gen in self.generations)

    def __hash__(self) -> int:
        return hash(tuple(self.generations))


class DeleteTextGenerateRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
):
    """Represents a DELETE request to the `/v2/generate/text/status/{id}` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_text_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextGenerateStatusResponse]:
        return TextGenerateStatusResponse

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DeleteTextGenerateRequest):
            return False

        return self.id_ == value.id_

    @override
    def __hash__(self) -> int:
        return hash(DeleteTextGenerateRequest.__name__) + hash(self.id_)


class TextGenerateStatusRequest(BaseAIHordeRequest, JobRequestMixin):
    """Represents a GET request to the `/v2/generate/status/{id}` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_text_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextGenerateStatusResponse]:
        return TextGenerateStatusResponse

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, TextGenerateStatusRequest):
            return False

        return self.id_ == value.id_

    @override
    def __hash__(self) -> int:
        return hash(TextGenerateStatusRequest.__name__) + hash(self.id_)
