from pydantic import BaseModel, Field, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.consts import KNOWN_SAMPLERS, KNOWN_SOURCE_PROCESSING
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import GenerationID, WorkerID
from horde_sdk.generic_api.apimodels import BaseRequest
from horde_sdk.utils import seed_to_int


class BaseAIHordeRequest(BaseRequest):
    @override
    @classmethod
    def get_api_url(cls) -> str:
        return AI_HORDE_BASE_URL


class BaseImageGenerateJobRequest(BaseModel):
    """Mix-in class for data relating to image generation jobs."""

    id: str | GenerationID  # noqa: A003
    """The UUID for this job."""


class BaseWorkerRequest(BaseModel):
    """Mix-in class for data relating to worker requests."""

    worker_id: str | WorkerID
    """The UUID of the worker in question for this request."""


class LorasPayloadEntry(BaseModel):
    """Represents a single lora parameter.

    v2 API Model: `ModelPayloadLorasStable`
    """

    name: str = Field(min_length=1, max_length=255)
    """The name of the LoRa model to use."""
    model: float = Field(default=1, ge=0, le=5)
    """The strength of the LoRa against the stable diffusion model."""
    clip: float = Field(default=1, ge=0, le=5)
    """The strength of the LoRa against the clip model."""
    inject_trigger: str | None = Field(default=None, min_length=1, max_length=30)
    """Any trigger required to activate the LoRa model."""


class BaseImageGenerateParam(BaseModel):
    """Represents some of the data included in a request to the `/v2/generate/async` endpoint.

    Also is the corresponding information returned on a job pop to the `/v2/generate/pop` endpoint.
    v2 API Model: `ModelPayloadStable`
    """

    sampler_name: KNOWN_SAMPLERS = KNOWN_SAMPLERS.k_lms
    cfg_scale: float = 7.5
    denoising_strength: float | None = Field(default=1, ge=0, le=1)
    seed: str | None = None
    height: int = 512
    width: int = 512
    seed_variation: int | None = None
    post_processing: list[str] = Field(default_factory=list)
    karras: bool = True
    tiling: bool = False
    hires_fix: bool = False
    clip_skip: int = 1
    control_type: str | None = None
    image_is_control: bool | None = None
    return_control_map: bool | None = None
    facefixer_strength: float | None = Field(default=None, ge=0, le=1)
    loras: list[LorasPayloadEntry] = Field(default_factory=list)
    special: dict = Field(default_factory=dict)
    steps: int = Field(default=25, ge=1)

    n_iter: int = Field(default=1, ge=1)
    use_nsfw_censor: bool = False

    @field_validator("sampler_name")
    def sampler_name_must_be_known(cls, v: str | KNOWN_SAMPLERS) -> str | KNOWN_SAMPLERS:
        """Ensure that the sampler name is in this list of supported samplers."""
        if v not in KNOWN_SAMPLERS.__members__:
            raise ValueError(f"Unknown sampler name {v}")
        return v

    @field_validator("seed")
    def seed_to_int_if_str(cls, v: str | int) -> str | int:
        """Ensure that the seed is an integer. If it is a string, convert it to an integer."""
        return str(seed_to_int(v))


class BaseImageGenerateImg2Img(BaseModel):
    """Mix-in class for data relating to img2img generation."""

    source_image: str | None = None
    source_processing: KNOWN_SOURCE_PROCESSING = KNOWN_SOURCE_PROCESSING.txt2img
    source_mask: str | None = None
