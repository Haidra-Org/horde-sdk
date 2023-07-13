from pydantic import Field, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    BaseImageGenerateParam,
)
from horde_sdk.ai_horde_api.apimodels.generate._check import ImageGenerateCheckRequest
from horde_sdk.ai_horde_api.apimodels.generate._status import DeleteImageGenerateRequest, ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    BaseRequestAuthenticated,
    BaseRequestWorkerDriven,
    BaseResponse,
)


class ImageGenerateAsyncResponse(BaseResponse):
    """Represents the data returned from the `/v2/generate/async` endpoint.

    v2 API Model: `RequestAsync`
    """

    id_: str | GenerationID = Field(alias="id")  # TODO: Remove `str`?
    """The UUID for this image generation."""
    kudos: float
    message: str | None = None

    @override
    @classmethod
    def is_requiring_follow_up(cls) -> bool:
        return True

    @override
    def get_follow_up_data(self) -> dict[str, object]:
        return {"id": self.id_}

    @classmethod
    def get_follow_up_default_request(cls) -> type[ImageGenerateCheckRequest]:
        return ImageGenerateCheckRequest

    @override
    @classmethod
    def get_follow_up_request_types(
        cls,
    ) -> list[type[ImageGenerateCheckRequest | ImageGenerateStatusRequest]]:
        return [ImageGenerateCheckRequest, ImageGenerateStatusRequest]

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestAsync"


class ImageGenerationInputPayload(BaseImageGenerateParam):
    n: int = Field(default=1, ge=1)


class ImageGenerateAsyncRequest(
    BaseAIHordeRequest,
    BaseRequestAuthenticated,
    BaseRequestWorkerDriven,
):
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

    source_image: str | None = None
    source_processing: KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    source_mask: str | None = None

    @model_validator(mode="before")
    def validate_censor_nsfw(cls, values: dict) -> dict:
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
    @classmethod
    def get_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_URL_Literals.v2_generate_async

    @override
    @classmethod
    def get_success_response_type(cls) -> type[ImageGenerateAsyncResponse]:
        return ImageGenerateAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[BaseResponse]]:
        return {
            HTTPStatusCode.ACCEPTED: cls.get_success_response_type(),
        }

    @override
    @classmethod
    def is_recovery_enabled(cls) -> bool:
        return True

    def get_recovery_request_type(self) -> type[DeleteImageGenerateRequest]:
        return DeleteImageGenerateRequest
