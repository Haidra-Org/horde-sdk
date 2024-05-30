import uuid

from loguru import logger
from pydantic import Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, GenMetadataEntry, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate._progress import ResponseGenerationProgressInfoMixin
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import JobID, WorkerID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import HordeAPIObject, HordeResponseBaseModel, ResponseWithProgressMixin


class Generation(HordeAPIObject):
    model: str = Field(title="Generation Model")
    """The model which generated this image."""
    state: GENERATION_STATE = Field(
        ...,
        examples=["ok"],
        title="Generation State",
    )
    """OBSOLETE (Use the gen_metadata field). The state of this generation."""
    worker_id: str | WorkerID = Field(
        title="Worker ID",
    )
    """The UUID of the worker which generated this image."""
    worker_name: str = Field(
        title="Worker Name",
    )
    """The name of the worker which generated this image."""


class ImageGeneration(Generation):
    """Represents the individual image generation responses in a ImageGenerateStatusResponse.

    v2 API Model: `GenerationStable`
    """

    id_: JobID = Field(alias="id")
    """The UUID of this generation. Is always returned as a `JobID`, but can initialized from a `str`."""
    # todo: remove `str`?
    img: str
    """The generated image as a Base64-encoded .webp file."""
    seed: str
    """The seed which generated this image."""
    censored: bool
    """When true this image has been censored by the worker's safety filter."""
    gen_metadata: list[GenMetadataEntry] | None = None
    """Extra metadata about faulted or defaulted components of the generation"""

    @override
    @classmethod
    def get_api_model_name(self) -> str | None:
        return "GenerationStable"

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageGeneration):
            return False
        return self.id_ == other.id_

    def __hash__(self) -> int:
        return hash(ImageGeneration.__name__) + hash(self.id_)


class ImageGenerateStatusResponse(
    HordeResponseBaseModel,
    ResponseWithProgressMixin,
    ResponseGenerationProgressInfoMixin,
):
    """Represent the response from the AI-Horde API when checking the status of an image generation job.

    v2 API Model: `RequestStatusStable`
    """

    generations: list[ImageGeneration] = Field(default_factory=list)
    """The individual image generation responses in this request."""
    shared: bool | None = False
    """If True, These images have been shared with LAION."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestStatusStable"

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
        if not isinstance(other, ImageGenerateStatusResponse):
            return False
        return all(gen in other.generations for gen in self.generations)

    def __hash__(self) -> int:
        return hash(tuple(self.generations))


class DeleteImageGenerateRequest(
    BaseAIHordeRequest,
    JobRequestMixin,
):
    """Represents a DELETE request to the `/v2/generate/status/{id}` endpoint."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateStatusResponse]:
        return ImageGenerateStatusResponse

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, DeleteImageGenerateRequest):
            return False

        return self.id_ == value.id_

    @override
    def __hash__(self) -> int:
        return hash(DeleteImageGenerateRequest.__name__) + hash(self.id_)


class ImageGenerateStatusRequest(BaseAIHordeRequest, JobRequestMixin):
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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_status

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateStatusResponse]:
        return ImageGenerateStatusResponse

    @override
    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ImageGenerateStatusRequest):
            return False

        return self.id_ == value.id_

    @override
    def __hash__(self) -> int:
        return hash(ImageGenerateStatusRequest.__name__) + hash(self.id_)
