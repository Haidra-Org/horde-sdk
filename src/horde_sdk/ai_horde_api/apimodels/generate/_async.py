from pydantic import Field, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._shared import (
    BaseAIHordeRequest,
    BaseImageGenerateParam,
    ImageGenerateImg2ImgData,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseRequestWorkerDriven, BaseResponse


class ImageGenerateAsyncResponse(BaseResponse):
    """Represents the data returned from the `/v2/generate/async` endpoint."""

    id: str | GenerationID  # noqa: A003
    """The UUID for this image generation."""
    kudos: float
    message: str

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestAsync"


class ImageGenerationInputPayload(BaseImageGenerateParam):
    n: int = Field(default=1, ge=1)


class ImageGenerateAsyncRequest(BaseAIHordeRequest, ImageGenerateImg2ImgData, BaseRequestWorkerDriven):
    """Represents the data needed to make a request to the `/v2/generate/async` endpoint.

    v2 API Model: `GenerationInputStable`
    """

    prompt: str
    params: ImageGenerationInputPayload | None = None

    nsfw: bool | None = True
    censor_nsfw: bool = False

    r2: bool = True

    shared: bool = False

    replacement_filter: bool = True

    @model_validator(mode="before")
    def validate_censor_nsfw(cls, values):
        if values.get("censor_nsfw", None) and values.get("nsfw", None):
            raise ValueError("censor_nsfw is only valid when nsfw is False")
        return values

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return AI_HORDE_API_URL_Literals.v2_generate_async

    @override
    @staticmethod
    def get_expected_response_type() -> type[ImageGenerateAsyncResponse]:
        return ImageGenerateAsyncResponse
