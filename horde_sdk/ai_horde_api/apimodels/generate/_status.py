from pydantic import BaseModel, Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate._check import ImageGenerateCheckResponse
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.ai_horde_api.fields import ImageID, WorkerID
from horde_sdk.consts import HTTPMethod


class ImageGeneration(BaseModel):
    """Represents the individual image generation responses in a ImageGenerateStatusResponse.

    v2 API Model: `GenerationStable`
    """

    id_: str | ImageID = Field(alias="id")
    """The UUID of this image. Is always returned as a `ImageID`, but can initialized from a `str`."""
    # todo: remove `str`?
    worker_id: str | WorkerID
    """The UUID of the worker which generated this image."""
    worker_name: str
    """The name of the worker which generated this image."""
    model: str
    """The model which generated this image."""
    state: GENERATION_STATE
    """The state of this generation."""
    img: str
    """The generated image as a Base64-encoded .webp file."""
    seed: str
    """The seed which generated this image."""
    censored: bool
    """When true this image has been censored by the worker's safety filter."""


class ImageGenerateStatusResponse(ImageGenerateCheckResponse):
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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_generate_status

    @override
    @classmethod
    def get_success_response_type(cls) -> type[ImageGenerateStatusResponse]:
        return ImageGenerateStatusResponse


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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_generate_status

    @override
    @classmethod
    def get_success_response_type(cls) -> type[ImageGenerateStatusResponse]:
        return ImageGenerateStatusResponse
