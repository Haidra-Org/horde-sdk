from loguru import logger
from pydantic import AliasChoices, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ImageGenerateParamMixin,
    JobResponseMixin,
)
from horde_sdk.ai_horde_api.apimodels.generate._check import ImageGenerateCheckRequest
from horde_sdk.ai_horde_api.apimodels.generate._status import DeleteImageGenerateRequest, ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObject,
    HordeResponse,
    HordeResponseBaseModel,
    RequestUsesImageWorkerMixin,
    ResponseRequiringFollowUpMixin,
)


class ImageGenerateAsyncResponse(
    HordeResponseBaseModel,
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
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{"id": self.id_}]

    @classmethod
    def get_follow_up_default_request_type(cls) -> type[ImageGenerateCheckRequest]:
        return ImageGenerateCheckRequest

    @override
    @classmethod
    def get_follow_up_request_types(  # type: ignore[override]
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


class ImageGenerateAsyncDryRunResponse(HordeResponseBaseModel):
    kudos: float

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "UNDOCUMENTED"


class ImageGenerationInputPayload(HordeAPIObject, ImageGenerateParamMixin):
    """Represents the 'params' field in the `/v2/generate/async` endpoint.

    v2 API Model: `ModelGenerationInputStable`
    """

    steps: int = Field(default=25, ge=1, validation_alias=AliasChoices("steps", "ddim_steps"))
    """The number of image generation steps to perform."""

    n: int = Field(default=1, ge=1, le=20, validation_alias=AliasChoices("n", "n_iter"))
    """The number of images to generate. Defaults to 1, maximum is 20."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModelGenerationInputStable"

    @field_validator("n", mode="before")
    def validate_n(cls, value: int) -> int:
        if value == 0:
            logger.debug("n (number of images to generate) is not set; defaulting to 1")
            return 1

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
        if values.get("censor_nsfw") and values.get("nsfw"):
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
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_async

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateAsyncResponse]:
        return ImageGenerateAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponse]]:
        return {
            HTTPStatusCode.OK: ImageGenerateAsyncDryRunResponse,
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }

    @override
    def get_number_of_results_expected(self) -> int:
        if not self.params:
            return 1
        return self.params.n

    @override
    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        return {"source_image"}
