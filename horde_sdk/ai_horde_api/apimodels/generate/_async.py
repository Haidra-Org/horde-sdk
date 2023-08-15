from loguru import logger
from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ImageGenerateParamMixin,
    JobResponseMixin,
)
from horde_sdk.ai_horde_api.apimodels.generate._check import ImageGenerateCheckRequest
from horde_sdk.ai_horde_api.apimodels.generate._status import DeleteImageGenerateRequest, ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    BaseResponse,
    ContainsMessageResponseMixin,
    RequestUsesImageWorkerMixin,
    ResponseRequiringFollowUpMixin,
)


class ImageGenerateAsyncResponse(
    BaseResponse,
    JobResponseMixin,
    ResponseRequiringFollowUpMixin,
    ContainsMessageResponseMixin,
):
    """Represents the data returned from the `/v2/generate/async` endpoint.

    v2 API Model: `RequestAsync`
    """

    """The UUID for this image generation."""
    kudos: float

    @override
    def get_follow_up_returned_params(self) -> list[dict[str, object]]:
        return [{"id": self.id_}]

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
    def get_follow_up_failure_cleanup_request_type(cls) -> type[DeleteImageGenerateRequest]:
        return DeleteImageGenerateRequest

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestAsync"


class ImageGenerationInputPayload(ImageGenerateParamMixin):
    n: int = Field(default=1, ge=1, le=60)

    @field_validator("n", mode="before")
    def validate_n(cls, value: int) -> int:
        if value >= 30:
            logger.warning(
                "n (number of images to generate) is >= 30; only moderators and certain users can generate that many "
                f"images at once. The request will probably fail. (n={value}))",
            )
        return value


class ImageGenerateAsyncRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    RequestUsesImageWorkerMixin,
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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_generate_async

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateAsyncResponse]:
        return ImageGenerateAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[BaseResponse]]:
        return {
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }
