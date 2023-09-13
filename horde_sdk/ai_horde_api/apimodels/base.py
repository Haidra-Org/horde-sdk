"""The base classes for all AI Horde API requests/responses."""
from __future__ import annotations

from loguru import logger
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.consts import KNOWN_SAMPLERS
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import JobID, WorkerID
from horde_sdk.generic_api.apimodels import HordeRequest, HordeResponseBaseModel


class BaseAIHordeRequest(HordeRequest):
    """Base class for all AI Horde API requests."""

    @override
    @classmethod
    def get_api_url(cls) -> str:
        return AI_HORDE_BASE_URL


class JobRequestMixin(BaseModel):
    """Mix-in class for data relating to any generation jobs."""

    id_: JobID = Field(alias="id")
    """The UUID for this job. Use this to post the results in the future."""


class JobResponseMixin(BaseModel):  # TODO: this model may not actually exist as such in the API
    """Mix-in class for data relating to any generation jobs."""

    id_: JobID = Field(alias="id")
    """The UUID for this job."""


class WorkerRequestMixin(BaseModel):
    """Mix-in class for data relating to worker requests."""

    worker_id: str | WorkerID
    """The UUID of the worker in question for this request."""


class LorasPayloadEntry(BaseModel):
    """Represents a single lora parameter.

    v2 API Model: `ModelPayloadLorasStable`
    """

    name: str = Field(min_length=1, max_length=255)
    """The name of the LoRa model to use."""
    model: float = Field(default=1, ge=-5, le=5)
    """The strength of the LoRa against the stable diffusion model."""
    clip: float = Field(default=1, ge=-5, le=5)
    """The strength of the LoRa against the clip model."""
    inject_trigger: str | None = Field(default=None, min_length=1, max_length=30)
    """Any trigger required to activate the LoRa model."""


class TIPayloadEntry(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    inject_ti: str | None
    strength: float = Field(default=1, ge=-5, le=5)

    @field_validator("inject_ti")
    def validate_inject_ti(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in ["prompt", "negprompt"]:
            raise ValueError("inject_ti must be either 'prompt' or 'negprompt'")
        return v

    @field_validator("strength")
    def validate_strength(cls, v: float) -> float:
        if v == 0:
            raise ValueError("strength must be non-zero")

        return v

    @model_validator(mode="after")
    def strength_only_if_inject_ti(self) -> TIPayloadEntry:
        if self.strength and self.inject_ti is None:
            raise ValueError("strength is only valid when inject_ti is set")
        return self


class ImageGenerateParamMixin(BaseModel):
    """Mix-in class of some of the data included in a request to the `/v2/generate/async` endpoint.

    Also is the corresponding information returned on a job pop to the `/v2/generate/pop` endpoint.
    v2 API Model: `ModelPayloadStable`
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    sampler_name: KNOWN_SAMPLERS = KNOWN_SAMPLERS.k_lms
    """The sampler to use for this generation. Defaults to `KNOWN_SAMPLERS.k_lms`."""
    cfg_scale: float = 7.5
    """The cfg_scale to use for this generation. Defaults to 7.5."""
    denoising_strength: float | None = Field(default=1, ge=0, le=1)
    """The denoising strength to use for this generation. Defaults to 1."""
    seed: str | None = None
    """The seed to use for this generation. If not provided, a random seed will be used."""
    height: int = Field(default=512, ge=64, le=3072)
    """The desired output image height."""
    width: int = Field(default=512, ge=64, le=3072)
    """The desired output image width."""
    seed_variation: int | None = Field(default=None, ge=1, le=1000)
    """Deprecated."""
    post_processing: list[str] = Field(default_factory=list)
    """A list of post-processing models to use."""
    karras: bool = True
    """Set to True if you want to use the Karras scheduling."""
    tiling: bool = False
    """Deprecated."""
    hires_fix: bool = False
    """Set to True if you want to use the hires fix."""
    clip_skip: int = Field(default=1, ge=1, le=12)
    """The number of clip layers to skip."""
    control_type: str | None = None
    """The type of control net type to use."""
    image_is_control: bool | None = None
    """Set to True if the image is a control image."""
    return_control_map: bool | None = None
    """Set to True if you want the ControlNet map returned instead of a generated image."""
    facefixer_strength: float | None = Field(default=None, ge=0, le=1)
    """The strength of the facefixer model."""
    loras: list[LorasPayloadEntry] = Field(default_factory=list)
    """A list of lora parameters to use."""
    tis: list[TIPayloadEntry] = Field(default_factory=list)
    """A list of textual inversion (embedding) parameters to use."""
    special: dict = Field(default_factory=dict)
    """Reserved for future use."""
    steps: int = Field(default=25, ge=1, validation_alias=AliasChoices("steps", "ddim_steps"))
    """The number of image generation steps to perform."""

    n: int = Field(default=1, ge=1, le=20, validation_alias=AliasChoices("n", "n_iter"))
    """The number of images to generate. Defaults to 1, maximum is 20."""

    @field_validator("width", "height", mode="before")
    def width_divisible_by_64(cls, value: int) -> int:
        """Ensure that the width is divisible by 64."""
        if value % 64 != 0:
            raise ValueError("width must be divisible by 64")
        return value

    @field_validator("n", mode="before")
    def validate_n(cls, value: int) -> int:
        if value == 0:
            logger.debug("n (number of images to generate) is not set; defaulting to 1")
            return 1

        return value

    use_nsfw_censor: bool = False

    @field_validator("sampler_name")
    def sampler_name_must_be_known(cls, v: str | KNOWN_SAMPLERS) -> str | KNOWN_SAMPLERS:
        """Ensure that the sampler name is in this list of supported samplers."""
        if v not in KNOWN_SAMPLERS.__members__:
            raise ValueError(f"Unknown sampler name {v}")
        return v

    @model_validator(mode="after")
    def validate_hires_fix(self) -> ImageGenerateParamMixin:
        if self.hires_fix and (self.width < 512 or self.height < 512):
            raise ValueError("hires_fix is only valid when width and height are both >= 512")
        return self


class JobSubmitResponse(HordeResponseBaseModel):
    """The response to a job submission request, indicating the number of kudos gained.

    v2 API Model: `GenerationSubmitted`
    """

    reward: float
    """The amount of kudos gained for submitting this request."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationSubmitted"
