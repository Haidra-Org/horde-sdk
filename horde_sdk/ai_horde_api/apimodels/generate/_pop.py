import pydantic
from pydantic import Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ImageGenerateParamMixin,
    JobResponseMixin,
)
from horde_sdk.ai_horde_api.apimodels.generate._submit import ImageGenerationJobSubmitRequest
from horde_sdk.ai_horde_api.consts import GENERATION_STATE, KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
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
    prompt: str


class ImageGenerateJobResponse(HordeResponseBaseModel, JobResponseMixin, ResponseRequiringFollowUpMixin):
    """Represents the data returned from the `/v2/generate/pop` endpoint.

    v2 API Model: `GenerationPayloadStable`
    """

    payload: ImageGenerateJobPopPayload
    """The parameters used to generate this image."""
    skipped: ImageGenerateJobPopSkippedStatus
    """The reasons this worker was not issued certain jobs, and the number of jobs for each reason."""
    model: str
    """Which of the available models to use for this request."""
    source_image: str | None = None
    """The Base64-encoded webp to use for img2img."""
    source_processing: str | KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    """If source_image is provided, specifies how to process it."""
    source_mask: str | None = None
    """If img_processing is set to 'inpainting' or 'outpainting', this parameter can be optionally provided as the
    mask of the areas to inpaint. If this arg is not passed, the inpainting/outpainting mask has to be embedded as
    alpha channel."""
    r2_upload: str | None = None
    """The r2 upload link to use to upload this image."""

    @field_validator("source_processing")
    def source_processing_must_be_known(cls, v: str | KNOWN_SOURCE_PROCESSING) -> str | KNOWN_SOURCE_PROCESSING:
        """Ensure that the source processing is in this list of supported source processing."""
        if v not in KNOWN_SOURCE_PROCESSING.__members__:
            raise ValueError(f"Unknown source processing {v}")
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
    def get_follow_up_returned_params(self) -> list[dict[str, object]]:
        return [{"id": self.id_}]

    @override
    def get_follow_up_failure_cleanup_params(self) -> dict[str, object]:
        return {"state": GENERATION_STATE.faulted}  # TODO: One day, could I do away with the magic string?

    @override
    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        return {"source_image"}


class ImageGenerateJobPopRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    """Represents the data needed to make a job request from a worker to the /v2/generate/pop endpoint.

    v2 API Model: `PopInputStable`
    """

    name: str
    priority_usernames: list[str] = Field(default_factory=list)
    nsfw: bool = True
    models: list[str]
    bridge_version: int
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
    def get_default_success_response_type(cls) -> type[ImageGenerateJobResponse]:
        return ImageGenerateJobResponse
