from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._shared import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.generic_api.apimodels import BaseRequestAuthenticated, BaseResponse


class ImageGenerationJobSubmitRequest(BaseAIHordeRequest, BaseRequestAuthenticated):
    """Represents the data needed to make a job submit 'request' from a worker to the /v2/generate/submit endpoint.

    v2 API Model: `SubmitInputStable`
    """

    id: str | GenerationID  # noqa: A003
    """The UUID for this image generation."""
    generation: str
    """R2 result was uploaded to R2, else the string of the result."""
    state: str
    """The state of this generation."""
    seed: str
    """The seed for this generation."""
    censored: bool = False
    """If True, this resulting image has been censored."""

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return AI_HORDE_API_URL_Literals.v2_generate_submit

    @override
    @staticmethod
    def get_expected_response_type() -> type[BaseResponse]:
        return ImageGenerationJobSubmitResponse


class ImageGenerationJobSubmitResponse(BaseResponse):
    reward: float
    """The amount of kudos gained for submitting this request."""
