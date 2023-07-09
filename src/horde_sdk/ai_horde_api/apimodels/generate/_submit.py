from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseRequestAuthenticated, BaseResponse


class ImageGenerationJobSubmitResponse(BaseResponse):
    reward: float
    """The amount of kudos gained for submitting this request."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"


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
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SubmitInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return AI_HORDE_API_URL_Literals.v2_generate_submit

    @override
    @staticmethod
    def get_success_response_type() -> type[ImageGenerationJobSubmitResponse]:
        return ImageGenerationJobSubmitResponse
