import uuid

import pydantic
from loguru import logger
from pydantic import AliasChoices, Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ImageGenerateParamMixin,
)
from horde_sdk.ai_horde_api.apimodels.generate._submit import ImageGenerationJobSubmitRequest
from horde_sdk.ai_horde_api.consts import GENERATION_STATE, KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


class ImageGenerateJobPopSkippedStatus(pydantic.BaseModel):
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


class ImageGenerateJobPopPayload(ImageGenerateParamMixin):
    prompt: str | None = None
    ddim_steps: int = Field(default=25, ge=1, validation_alias=AliasChoices("steps", "ddim_steps"))
    """The number of image generation steps to perform."""

    n_iter: int = Field(default=1, ge=1, le=20, validation_alias=AliasChoices("n", "n_iter"))
    """The number of images to generate. Defaults to 1, maximum is 20."""


class ImageGenerateJobPopResponse(HordeResponseBaseModel, ResponseRequiringFollowUpMixin):
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
    source_processing: str | KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    """If source_image is provided, specifies how to process it."""
    source_mask: str | None = None
    """If img_processing is set to 'inpainting' or 'outpainting', this parameter can be optionally provided as the
    mask of the areas to inpaint. If this arg is not passed, the inpainting/outpainting mask has to be embedded as
    alpha channel."""
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
        return {"source_image"}

    @override
    def ignore_failure(self) -> bool:
        if self.id_ is None:
            return True

        return super().ignore_failure()


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
