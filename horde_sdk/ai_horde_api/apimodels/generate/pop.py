from __future__ import annotations

import asyncio
import uuid
from urllib.parse import urlparse

import aiohttp
from loguru import logger
from pydantic import AliasChoices, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ExtraSourceImageEntry,
    ImageGenerateParamMixin,
)
from horde_sdk.ai_horde_api.apimodels.generate.submit import ImageGenerationJobSubmitRequest
from horde_sdk.ai_horde_api.apimodels.workers.messages import _ResponseModelMessageData, ResponseModelMessage
from horde_sdk.ai_horde_api.consts import (
    GENERATION_STATE,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.consts import _ANONYMOUS_MODEL, _MODEL_OVERLOADED, HTTPMethod
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_FACEFIXERS, KNOWN_UPSCALERS
from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    ResponseRequiringDownloadMixin,
    ResponseRequiringFollowUpMixin,
)


class NoValidRequestFound(HordeAPIObjectBaseModel):
    """Base class for the number of jobs a worker skipped for, and why.

    v2 API Model: `NoValidRequestFound`
    """

    blacklist: int | None = Field(default=None, ge=0)
    """How many waiting requests were skipped because they demanded a generation with a word that this worker does
    not accept."""
    bridge_version: int | None = Field(default=None, examples=[0], ge=0)
    """How many waiting requests were skipped because they require a higher version of the bridge than this worker
    is running (upgrade if you see this in your skipped list)."""
    kudos: int | None = Field(default=None)
    """How many waiting requests were skipped because the user didn't have enough kudos when this worker requires"""
    models: int | None = Field(default=None, examples=[0], ge=0)
    """How many waiting requests were skipped because they demanded a different model than what this worker
    provides."""
    nsfw: int | None = Field(default=None, ge=0)
    """How many waiting requests were skipped because they demanded a nsfw generation which this worker does not
    provide."""
    performance: int | None = Field(
        default=None,
        ge=0,
    )
    """How many waiting requests were skipped because they demanded a higher performance than this worker provides."""
    untrusted: int | None = Field(default=None, ge=0)
    """How many waiting requests were skipped because they demanded a trusted worker which this worker is not."""
    worker_id: int | None = Field(
        default=None,
        ge=0,
    )
    """How many waiting requests were skipped because they demanded a specific worker."""

    def is_empty(self) -> bool:
        """Whether or not this object has any non-zero values."""
        return len(self.model_fields_set) == 0

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidRequestFound"


class ImageGenerateJobPopSkippedStatus(NoValidRequestFound):
    """The number of jobs a worker was skipped for, and why.

    v2 API Model: `NoValidRequestFoundStable`
    """

    max_pixels: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a higher size than this worker provides."""
    unsafe_ip: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they came from an unsafe IP."""
    img2img: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they requested img2img."""
    painting: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they requested inpainting/outpainting."""
    post_processing: int = Field(default=0, ge=0, alias="post-processing")
    """How many waiting requests were skipped because they requested post-processing."""
    lora: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they requested loras."""
    controlnet: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they requested a controlnet."""
    step_count: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they requested more steps than this worker provides."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidRequestFoundStable"


class ImageGenerateJobPopPayload(ImageGenerateParamMixin):
    """Mixin for the additional image generation parameters used in dispatching a job to a worker.

    v2 API Model: `ModelPayloadRootStable`
    """

    prompt: str | None = None
    """The prompt to use for this image generation."""

    ddim_steps: int = Field(default=25, ge=1, validation_alias=AliasChoices("steps", "ddim_steps"))
    """The number of image generation steps to perform."""

    n_iter: int = Field(default=1, ge=1, le=20, validation_alias=AliasChoices("n", "n_iter"))
    """The number of images to generate. Defaults to 1, maximum is 20."""


class ExtraSourceImageMixin(ResponseRequiringDownloadMixin):
    """Mixin for jobs which have extra source images."""

    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """Additional uploaded images (as base64) which can be used for further operations."""
    _downloaded_extra_source_images: list[ExtraSourceImageEntry] | None = None

    async def async_download_extra_source_images(
        self,
        client_session: aiohttp.ClientSession,
        *,
        max_retries: int = 5,
    ) -> list[ExtraSourceImageEntry] | None:
        """Download the extra source images concurrently.

        You can also use `get_downloaded_extra_source_images` to get the downloaded images later, if needed.

        Args:
            client_session: The aiohttp client session to use for downloading.
            max_retries: The maximum number of times to retry downloading an image.

        Returns:
            The downloaded extra source images.
        """
        if not self.extra_source_images:
            logger.info("No extra source images to download.")
            return None

        if self._downloaded_extra_source_images is not None:
            logger.warning("Extra source images already downloaded.")
            return self._downloaded_extra_source_images

        self._downloaded_extra_source_images = []

        download_tasks = []
        for extra_source_image in self.extra_source_images:
            download_tasks.append(
                asyncio.create_task(
                    self._download_image_if_needed(client_session, extra_source_image, max_retries),
                ),
            )

        await asyncio.gather(*download_tasks)

        self._sort_downloaded_images()
        return self._downloaded_extra_source_images.copy()

    def get_downloaded_extra_source_images(self) -> list[ExtraSourceImageEntry] | None:
        """Get the downloaded extra source images."""
        return (
            self._downloaded_extra_source_images.copy() if self._downloaded_extra_source_images is not None else None
        )

    async def _download_image_if_needed(
        self,
        client_session: aiohttp.ClientSession,
        extra_source_image: ExtraSourceImageEntry,
        max_retries: int,
    ) -> None:
        """Download an extra source image if it has not already been downloaded.

        Args:
            client_session: The aiohttp client session to use for downloading.
            extra_source_image: The extra source image to download.
            max_retries: The maximum number of times to retry downloading an image.
        """
        if self._downloaded_extra_source_images is None:
            self._downloaded_extra_source_images = []

        if extra_source_image.image in (entry.original_url for entry in self._downloaded_extra_source_images):
            logger.debug(f"Extra source image {extra_source_image.image} already downloaded.")
            return

        for attempt in range(max_retries):
            try:
                downloaded_image = await self.download_file_as_base64(client_session, extra_source_image.image)
                self._downloaded_extra_source_images.append(
                    ExtraSourceImageEntry(
                        image=downloaded_image,
                        strength=extra_source_image.strength,
                        original_url=extra_source_image.image,
                    ),
                )
                break
            except Exception as e:
                logger.error(f"Error downloading extra source image {extra_source_image.image}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to download image {extra_source_image.image} after {max_retries} attempts.")

    def _sort_downloaded_images(self) -> None:
        """Sort the downloaded extra source images in the order they were requested."""
        if self.extra_source_images is None or self._downloaded_extra_source_images is None:
            return

        _extra_source_images = self.extra_source_images.copy()
        self._downloaded_extra_source_images.sort(
            key=lambda entry: next(
                (i for i, image in enumerate(_extra_source_images) if image.image == entry.original_url),
                len(_extra_source_images),
            ),
        )


class PopResponseModelMessage(_ResponseModelMessageData):
    """The message data which appears in a job pop response."""

    id_: str | None = Field(default=None, alias="id")
    """The ID of the message."""

    expiry: str | None = None
    """The time at which this message expires."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _MODEL_OVERLOADED


class ImageGenerateJobPopResponse(
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
    ExtraSourceImageMixin,
):
    """Contains job data for workers, if any were available. Also contains data for jobs this worker was skipped for.

    This is the key response type for all image workers as it contains all assignment data for the worker.

    Represents the data returned from the /v2/generate/pop endpoint with http status code 200.

    v2 API Model: `GenerationPayloadStable`
    """

    id_: GenerationID | None = Field(default=None, alias="id")
    """(Obsolete) The UUID for this image generation."""
    ids: list[GenerationID]
    """A list of UUIDs for image generation."""

    payload: ImageGenerateJobPopPayload
    """The parameters used to generate this image."""
    skipped: ImageGenerateJobPopSkippedStatus = Field(default_factory=ImageGenerateJobPopSkippedStatus)
    """The reasons this worker was not issued certain jobs, and the number of jobs for each reason."""
    model: str | None = None
    """Which of the available models to use for this request."""
    source_image: str | None = None
    """The URL or Base64-encoded webp to use for img2img."""
    _downloaded_source_image: str | None = None
    """The downloaded source image (as base64), if any. This is not part of the API response."""
    source_processing: str | KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    """If source_image is provided, specifies how to process it."""
    source_mask: str | None = None
    """If img_processing is set to 'inpainting' or 'outpainting', this parameter can be optionally provided as the
    mask of the areas to inpaint. If this arg is not passed, the inpainting/outpainting mask has to be embedded as
    alpha channel."""
    _downloaded_source_mask: str | None = None
    """The downloaded source mask (as base64), if any. This is not part of the API response."""
    r2_upload: str | None = None
    """(Obsolete) The r2 upload link to use to upload this image."""
    r2_uploads: list[str] | None = None
    """The r2 upload links for each this image. Each index matches the ID in self.ids"""
    ttl: int | None = None
    """The amount of seconds before this job is considered stale and aborted."""

    messages: list[PopResponseModelMessage] | None = None
    """The messages that have been sent to this worker."""

    @field_validator("source_processing")
    def source_processing_must_be_known(cls, v: str | KNOWN_SOURCE_PROCESSING) -> str | KNOWN_SOURCE_PROCESSING:
        """Ensure that the source processing is in this list of supported source processing."""
        if isinstance(v, KNOWN_SOURCE_PROCESSING):
            return v

        try:
            KNOWN_SOURCE_PROCESSING(v)
        except ValueError:
            logger.warning(f"Unknown source processing {v}. Is your SDK out of date or did the API change?")
        return v

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | GenerationID) -> GenerationID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return GenerationID(root=uuid.uuid4())

        return v

    _ids_present: bool = False

    @property
    def ids_present(self) -> bool:
        """Whether or not the IDs are present."""
        return self._ids_present

    @model_validator(mode="after")
    def validate_ids_present(self) -> ImageGenerateJobPopResponse:
        """Ensure that either id_ or ids is present."""
        if self.model is None:
            if self.skipped.is_empty():
                logger.debug("No model or skipped data found in response.")
            else:
                logger.debug("No model found in response.")
            return self

        if self.id_ is None and len(self.ids) == 0:
            raise ValueError("Neither id_ nor ids were present in the response.")

        self._ids_present = True

        return self

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationPayloadStable"

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[ImageGenerationJobSubmitRequest]:
        return ImageGenerationJobSubmitRequest

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[ImageGenerationJobSubmitRequest]:
        return ImageGenerationJobSubmitRequest

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{"id": self.id_}]

    @override
    def get_follow_up_failure_cleanup_params(self) -> dict[str, object]:
        return {
            "state": GENERATION_STATE.faulted,
            "seed": self.payload.seed,
            "generation": "Faulted",
        }  # TODO: One day, could I do away with the magic string?

    @override
    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        return {"source_image", "source_mask", "extra_source_images"}

    @override
    def ignore_failure(self) -> bool:
        if self.id_ is None:
            return True

        return super().ignore_failure()

    @property
    def has_upscaler(self) -> bool:
        """Whether or not this image generation has an upscaler."""
        if len(self.payload.post_processing) == 0:
            return False

        return any(
            post_processing in KNOWN_UPSCALERS.__members__ or post_processing in KNOWN_UPSCALERS._value2member_map_
            for post_processing in self.payload.post_processing
        )

    @property
    def has_facefixer(self) -> bool:
        """Whether or not this image generation has a facefixer."""
        if len(self.payload.post_processing) == 0:
            return False

        return any(post_processing in KNOWN_FACEFIXERS.__members__ for post_processing in self.payload.post_processing)

    def get_downloaded_source_image(self) -> str | None:
        """Get the downloaded source image."""
        return self._downloaded_source_image

    def get_downloaded_source_mask(self) -> str | None:
        """Get the downloaded source mask."""
        return self._downloaded_source_mask

    def async_download_source_image(self, client_session: aiohttp.ClientSession) -> asyncio.Task[None]:
        """Download the source image concurrently."""
        # If the source image is not set, there is nothing to download.
        if self.source_image is None:
            return asyncio.create_task(asyncio.sleep(0))

        # If the source image is not a URL, it is already a base64 string.
        if urlparse(self.source_image).scheme not in ["http", "https"]:
            self._downloaded_source_image = self.source_image
            return asyncio.create_task(asyncio.sleep(0))

        return asyncio.create_task(
            self.download_file_to_field_as_base64(client_session, self.source_image, "_downloaded_source_image"),
        )

    def async_download_source_mask(self, client_session: aiohttp.ClientSession) -> asyncio.Task[None]:
        """Download the source mask concurrently."""
        # If the source mask is not set, there is nothing to download.
        if self.source_mask is None:
            return asyncio.create_task(asyncio.sleep(0))

        # If the source mask is not a URL, it is already a base64 string.
        if urlparse(self.source_mask).scheme not in ["http", "https"]:
            self._downloaded_source_mask = self.source_mask
            return asyncio.create_task(asyncio.sleep(0))

        return asyncio.create_task(
            self.download_file_to_field_as_base64(client_session, self.source_mask, "_downloaded_source_mask"),
        )

    @override
    async def async_download_additional_data(self, client_session: aiohttp.ClientSession) -> None:
        """Download all additional images concurrently."""
        await asyncio.gather(
            self.async_download_source_image(client_session),
            self.async_download_source_mask(client_session),
            self.async_download_extra_source_images(client_session),
        )

    @override
    def download_additional_data(self) -> None:
        raise NotImplementedError("This method is not yet implemented. Use async_download_additional_data instead.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ImageGenerateJobPopResponse):
            return False

        if self.id_ is not None and other.id_ is not None:
            return self.id_ == other.id_

        if len(self.ids) > 0 and len(other.ids) > 0:
            if len(self.ids) != len(other.ids):
                return False

            return all(i in other.ids for i in self.ids)

        logger.warning("No ID or IDs found in response. This is a bug.")
        return False

    def __hash__(self) -> int:
        if self.id_ is not None:
            return hash(ImageGenerateJobPopResponse.__name__) + hash(self.id_)

        if len(self.ids) > 0:
            return hash(ImageGenerateJobPopResponse.__name__) + hash(tuple(self.ids))

        logger.warning("No ID or IDs found in response. This is a bug.")
        return hash(0)


class PopInput(HordeAPIObjectBaseModel):
    """The input data for a image worker requesting jobs.

    v2 API Model: `PopInput`
    """

    amount: int | None = Field(1, ge=1, le=20)
    """The number of jobs to pop at the same time."""
    bridge_agent: str | None = Field(
        "unknown:0:unknown",
        examples=["AI Horde Worker reGen:4.1.0:https://github.com/Haidra-Org/horde-worker-reGen"],
        max_length=1000,
    )
    """The worker name, version and website."""
    models: list[str]
    """The models this worker can generate."""
    name: str
    """The Name of the Worker."""
    nsfw: bool | None = Field(
        default=False,
    )
    """Whether this worker can generate NSFW requests or not."""
    priority_usernames: list[str] | None = None
    """The usernames that should be prioritized by this worker."""
    require_upfront_kudos: bool | None = Field(
        default=False,
        description=(
            "If True, this worker will only pick up requests where the owner has the required kudos to consume already"
            " available."
        ),
        examples=[
            False,
        ],
    )
    """If True, this worker will only pick up requests where the owner has the required kudos to consume already
    available."""
    threads: int | None = Field(
        default=1,
        description=(
            "How many threads this worker is running. This is used to accurately the current power available in the"
            " horde."
        ),
        ge=1,
        le=50,
    )
    """How many threads this worker is running. This is used to accurately the current power available in the horde."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "PopInput"


class ImageGenerateJobPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin, PopInput):
    """Request additional jobs, if any are available, for an image worker.

    This is the key request type for all image workers as it contains all the parameters needed to request a job.

    Represents a POST request to the /v2/generate/pop endpoint.

    v2 API Model: `PopInputStable`
    """

    bridge_version: int | None = None
    """The version of the bridge this worker is running."""
    max_pixels: int = Field(examples=[262144])
    """The maximum number of pixels this worker can generate."""
    blacklist: list[str] = Field(default_factory=list)
    """The list of words this worker will not accept in a prompt."""
    allow_img2img: bool = True
    """Whether this worker can generate img2img."""
    allow_painting: bool = False
    """Whether this worker can generate inpainting/outpainting."""
    allow_unsafe_ipaddr: bool = True
    """Whether this worker will generate from unsafe/VPN IP addresses."""
    allow_post_processing: bool = True
    """Whether this worker can do post-processing."""
    allow_controlnet: bool = False
    """Whether this worker can generate using controlnets."""
    allow_sdxl_controlnet: bool = False
    """Whether this worker can generate using SDXL controlnets."""
    allow_lora: bool = False
    """Whether this worker can generate using Loras."""
    extra_slow_worker: bool = False
    """Marks the worker as extra slow."""
    limit_max_steps: bool = False
    """Prevents the worker picking up jobs with more steps than the model average."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "PopInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_pop

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateJobPopResponse]:
        return ImageGenerateJobPopResponse
