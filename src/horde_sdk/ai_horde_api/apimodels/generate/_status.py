from typing_extensions import override

from pydantic import BaseModel

from horde_sdk.ai_horde_api.apimodels._base import BaseImageGenerateJobRequest
from horde_sdk.ai_horde_api.apimodels.generate._check import ImageGenerateCheckResponse
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL, AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import ImageID, WorkerID
from horde_sdk.generic_api.apimodels import BaseResponse
from horde_sdk.generic_api.endpoints import url_with_path


class ImageGenerateStatusRequest(BaseImageGenerateJobRequest):
    """Represents a GET request to the `/v2/generate/status/{id}` endpoint."""


class ImageGeneration(BaseModel):
    """Represents the individual image generation responses in a ImageGenerateStatusResponse.

    v2 API Model: `GenerationStable`
    """

    id: str | ImageID  # noqa: A003
    """The UUID of this image. Is always returned as a `ImageID`, but can initialized from a `str`."""
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

    generations: list[ImageGeneration]
    """The individual image generation responses in this request."""
    shared: bool
    """If True, These images have been shared with LAION."""


class CancelImageGenerateRequest(BaseImageGenerateJobRequest):
    """Represents a DELETE request to the `/v2/generate/status/{id}` endpoint.

    v2 API Model: `CancelInputStable`
    """

    @override
    @staticmethod
    def get_endpoint_url() -> str:
        return url_with_path(base_url=AI_HORDE_BASE_URL, path=AI_HORDE_API_URL_Literals.v2_generate_status)

    @override
    @staticmethod
    def get_expected_response_type() -> type[BaseResponse]:
        return ImageGenerateStatusResponse
