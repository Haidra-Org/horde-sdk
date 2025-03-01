from __future__ import annotations

from loguru import logger
from pydantic import AliasChoices, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ExtraSourceImageEntry,
    ImageGenerateParamMixin,
    JobResponseMixin,
    SingleWarningEntry,
)
from horde_sdk.ai_horde_api.apimodels.generate.check import ImageGenerateCheckRequest
from horde_sdk.ai_horde_api.apimodels.generate.status import DeleteImageGenerateRequest, ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod, HTTPStatusCode
from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeResponseBaseModel,
    HordeResponseTypes,
    RequestUsesWorkerMixin,
    ResponseRequiringFollowUpMixin,
)


class ImageGenerateAsyncResponse(
    HordeResponseBaseModel,
    JobResponseMixin,
    ResponseRequiringFollowUpMixin,
    ContainsMessageResponseMixin,
):
    """The expected cost of the requested job and any warnings generated by the server.

    A typical warning is that the request is not currently possible. You may want to handle certain
    warnings in your application. See :class:`horde_sdk.ai_horde_api.apimodels.base.SingleWarningEntry` for more
    information.

    Represents the data returned from the /v2/generate/async endpoint with http status code 202.

    v2 API Model: `RequestAsync`
    """

    """The UUID for this image generation."""
    kudos: float
    """The expected kudos consumption for this request."""
    warnings: list[SingleWarningEntry] | None = None
    """Any warnings that were generated by the server or a serving worker."""

    @model_validator(mode="after")
    def validate_warnings(self) -> ImageGenerateAsyncResponse:
        """Log any warnings that were generated by the server or a serving worker."""
        if self.warnings is None:
            return self

        for warning in self.warnings:
            logger.warning(f"Warning from server ({warning.code}): {warning.message}")

        return self

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{"id": self.id_}]

    @override
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

    def __hash__(self) -> int:
        return hash(ImageGenerateAsyncResponse.__name__) + hash(self.id_)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, ImageGenerateAsyncResponse) and self.id_ == __value.id_


class ImageGenerateAsyncDryRunResponse(HordeResponseBaseModel):
    """Request the expected cost of the job without actually starting the job.

    Represents the data returned from the /v2/generate/async endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    kudos: float
    """The expected kudos consumption for this request."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _ANONYMOUS_MODEL


class ImageGenerationInputPayload(ImageGenerateParamMixin):
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
        """Ensure that n is at least 1."""
        if value == 0:
            logger.debug("n (number of images to generate) is not set; defaulting to 1")
            return 1

        return value


class ImageGenerateAsyncRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    RequestUsesWorkerMixin,
):
    """Request to start an image generation job.

    Upon a successful response, you should poll the status of the job using the
    check endpoint. See :class:`horde_sdk.ai_horde_api.apimodels.generate.check.ImageGenerateCheckRequest` for more
    information.

    Represents a POST request to the /v2/generate/async endpoint.

    v2 API Model: `GenerationInputStable`
    """

    prompt: str
    """The prompt which will be sent to Stable Diffusion to generate an image."""

    params: ImageGenerationInputPayload | None = None
    """The parameters for the image generation."""

    nsfw: bool | None = True
    """Set to true if this request is NSFW. This will skip workers which censor images."""
    censor_nsfw: bool = False
    """If the request is SFW, and the worker accidentally generates NSFW, it will send back a censored image."""

    r2: bool = True
    """If True, the image will be sent via cloudflare r2 download link."""

    shared: bool = False
    """If True, The image will be shared with LAION for improving their dataset. This will also reduce your
    kudos consumption by 2. For anonymous users, this is always True."""

    replacement_filter: bool = True
    """If enabled, suspicious prompts are sanitized through a string replacement filter instead."""

    source_image: str | None = None
    """The public URL of the source image or a base64 string to use."""
    source_processing: KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    """If source_image is provided, specifies how to process it."""
    source_mask: str | None = None
    """If source_processing is set to 'inpainting' or 'outpainting', this parameter can be optionally provided as the
    Base64-encoded webp mask of the areas to inpaint. If this arg is not passed, the inpainting/outpainting mask has to
    be embedded as alpha channel."""
    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """Additional uploaded images which can be used for further operations."""

    @model_validator(mode="after")
    def validate_censor_nsfw(self) -> ImageGenerateAsyncRequest:
        """Ensure that censor_nsfw is not set when nsfw is enabled."""
        if self.nsfw and self.censor_nsfw:
            raise ValueError("Cannot censor NSFW content when NSFW detection is enabled.")
        return self

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
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponseTypes]]:
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
        return {"source_image", "source_mask", "extra_source_images"}
