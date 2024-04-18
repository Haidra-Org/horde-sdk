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
from horde_sdk.ai_horde_api.apimodels.generate._submit import ImageGenerationJobSubmitRequest
from horde_sdk.ai_horde_api.consts import (
    GENERATION_STATE,
    KNOWN_FACEFIXERS,
    KNOWN_SOURCE_PROCESSING,
    KNOWN_UPSCALERS,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeAPIDataObject,
    HordeResponseBaseModel,
    ResponseRequiringDownloadMixin,
    ResponseRequiringFollowUpMixin,
)


class ImageGenerateJobPopSkippedStatus(HordeAPIDataObject):
    """Represents the data returned from the `/v2/generate/pop` endpoint for why a worker was skipped.

    v2 API Model: `NoValidRequestFoundStable`
    """

    worker_id: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a specific worker."""
    performance: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they required higher performance."""
    nsfw: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a nsfw generation which this worker
    does not provide."""
    blacklist: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a generation with a word that this worker does
    not accept."""
    untrusted: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a trusted worker which this worker is not."""
    models: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they demanded a different model than what this worker
    provides."""
    bridge_version: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because they require a higher version of the bridge than this worker is
    running (upgrade if you see this in your skipped list)."""
    kudos: int = Field(default=0, ge=0)
    """How many waiting requests were skipped because the user didn't have enough kudos when this worker requires
     upfront kudos."""
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

    def is_empty(self) -> bool:
        """Whether or not this object has any non-zero values."""
        return len(self.model_fields_set) == 0


class ImageGenerateJobPopPayload(ImageGenerateParamMixin):
    prompt: str | None = None
    ddim_steps: int = Field(default=25, ge=1, validation_alias=AliasChoices("steps", "ddim_steps"))
    """The number of image generation steps to perform."""

    n_iter: int = Field(default=1, ge=1, le=20, validation_alias=AliasChoices("n", "n_iter"))
    """The number of images to generate. Defaults to 1, maximum is 20."""


class ImageGenerateJobPopResponse(
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
    ResponseRequiringDownloadMixin,
):
    """Represents the data returned from the `/v2/generate/pop` endpoint.

    v2 API Model: `GenerationPayloadStable`
    """

    id_: JobID | None = Field(None, alias="id")
    """(Obsolete) The UUID for this image generation."""
    ids: list[JobID]
    """A list of UUIDs for image generation."""

    payload: ImageGenerateJobPopPayload
    """The parameters used to generate this image."""
    skipped: ImageGenerateJobPopSkippedStatus
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
    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """Additional uploaded images (as base64) which can be used for further operations."""
    _downloaded_extra_source_images: list[ExtraSourceImageEntry] | None = None
    """The downloaded extra source images, if any. This is not part of the API response."""
    r2_upload: str | None = None
    """(Obsolete) The r2 upload link to use to upload this image."""
    r2_uploads: list[str] | None = None
    """The r2 upload links for each this image. Each index matches the ID in self.ids"""

    @field_validator("source_processing")
    def source_processing_must_be_known(cls, v: str | KNOWN_SOURCE_PROCESSING) -> str | KNOWN_SOURCE_PROCESSING:
        """Ensure that the source processing is in this list of supported source processing."""
        if v not in KNOWN_SOURCE_PROCESSING.__members__:
            raise ValueError(f"Unknown source processing {v}")
        return v

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v

    @model_validator(mode="after")
    def ids_present(self) -> ImageGenerateJobPopResponse:
        """Ensure that either id_ or ids is present."""
        if self.model is None:
            if self.skipped.is_empty():
                logger.debug("No model or skipped data found in response.")
            else:
                logger.debug("No model found in response.")
            return self

        if self.id_ is None and len(self.ids) == 0:
            raise ValueError("Neither id_ nor ids were present in the response.")

        if len(self.ids) > 1:
            logger.debug("Sorting IDs")
            self.ids.sort()

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

    def get_downloaded_extra_source_images(self) -> list[ExtraSourceImageEntry] | None:
        """Get the downloaded extra source images."""
        return (
            self._downloaded_extra_source_images.copy() if self._downloaded_extra_source_images is not None else None
        )

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
        if not self.source_mask.startswith("http"):
            self._downloaded_source_mask = self.source_mask
            return asyncio.create_task(asyncio.sleep(0))

        return asyncio.create_task(
            self.download_file_to_field_as_base64(client_session, self.source_mask, "_downloaded_source_mask"),
        )

    async def async_download_extra_source_images(
        self,
        client_session: aiohttp.ClientSession,
        *,
        max_retries: int = 5,
    ) -> list[ExtraSourceImageEntry] | None:
        """Download all extra source images concurrently."""

        if self.extra_source_images is None or len(self.extra_source_images) == 0:
            logger.info("No extra source images to download.")
            return None

        if self._downloaded_extra_source_images is None:
            self._downloaded_extra_source_images = []
        else:
            logger.warning("Extra source images already downloaded.")
            return self._downloaded_extra_source_images

        attempts = 0
        while attempts < max_retries:
            tasks: list[asyncio.Task[str | None]] = []

            for extra_source_image in self.extra_source_images:
                if extra_source_image.image is None:
                    continue

                if urlparse(extra_source_image.image).scheme not in ["http", "https"]:
                    self._downloaded_extra_source_images.append(extra_source_image)
                    tasks.append(asyncio.create_task(asyncio.sleep(0)))
                    continue

                if any(
                    extra_source_image.image == downloaded_extra_source_image.original_url
                    for downloaded_extra_source_image in self._downloaded_extra_source_images
                ):
                    logger.debug(f"Extra source image {extra_source_image.image} already downloaded.")
                    tasks.append(asyncio.create_task(asyncio.sleep(0)))
                    continue

                tasks.append(
                    asyncio.create_task(
                        self.download_file_as_base64(client_session, extra_source_image.image),
                    ),
                )

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result, extra_source_image in zip(results, self.extra_source_images, strict=True):
                if isinstance(result, Exception) or not isinstance(result, str):
                    logger.error(f"Error downloading extra source image {extra_source_image.image}: {result}")
                    continue

                self._downloaded_extra_source_images.append(
                    ExtraSourceImageEntry(
                        image=result,
                        strength=extra_source_image.strength,
                        original_url=extra_source_image.image,
                    ),
                )

            if len(self._downloaded_extra_source_images) == len(self.extra_source_images):
                break

            attempts += 1

        # If there are any entries in _downloaded_extra_source_images,
        # make sure the order matches the order of the original list.
        if (
            self.extra_source_images is not None
            and self._downloaded_extra_source_images is not None
            and len(self._downloaded_extra_source_images) > 0
        ):

            def _sort_key(x: ExtraSourceImageEntry) -> int:
                if self.extra_source_images is not None:
                    for i, extra_source_image in enumerate(self.extra_source_images):
                        if extra_source_image.image == x.original_url:
                            return i

                return 0

            self._downloaded_extra_source_images.sort(key=_sort_key)

        return self._downloaded_extra_source_images.copy()

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
            return hash(self.id_)

        if len(self.ids) > 0:
            return hash(tuple(self.ids))

        logger.warning("No ID or IDs found in response. This is a bug.")
        return hash(0)


class ImageGenerateJobPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Represents the data needed to make a job request from a worker to the /v2/generate/pop endpoint.

    v2 API Model: `PopInputStable`
    """

    name: str
    priority_usernames: list[str] = Field(default_factory=list)
    nsfw: bool = True
    models: list[str]
    bridge_version: int | None = None
    bridge_agent: str
    threads: int = 1
    require_upfront_kudos: bool = False
    max_pixels: int
    blacklist: list[str] = Field(default_factory=list)
    allow_img2img: bool = True
    allow_painting: bool = False
    allow_unsafe_ipaddr: bool = True
    allow_post_processing: bool = True
    allow_controlnet: bool = False
    allow_lora: bool = False
    amount: int = 1

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
