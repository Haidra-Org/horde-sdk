"""The base classes for all AI Horde API requests/responses."""

from __future__ import annotations

import os
import random
import uuid

from loguru import logger
from pydantic import ConfigDict, Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.consts import (
    KNOWN_CONTROLNETS,
    KNOWN_FACEFIXERS,
    KNOWN_MISC_POST_PROCESSORS,
    KNOWN_SAMPLERS,
    KNOWN_UPSCALERS,
    METADATA_TYPE,
    METADATA_VALUE,
    POST_PROCESSOR_ORDER_TYPE,
    _all_valid_post_processors_names_and_values,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import JobID, WorkerID
from horde_sdk.generic_api.apimodels import HordeAPIDataObject, HordeRequest, HordeResponseBaseModel


class BaseAIHordeRequest(HordeRequest):
    """Base class for all AI Horde API requests."""

    @override
    @classmethod
    def get_api_url(cls) -> str:
        return AI_HORDE_BASE_URL


class JobRequestMixin(HordeAPIDataObject):
    """Mix-in class for data relating to any generation jobs."""

    id_: JobID = Field(alias="id")
    """The UUID for this job. Use this to post the results in the future."""

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, JobRequestMixin):
            return self.id_ == __value.id_
        return False

    def __hash__(self) -> int:
        return hash(self.id_)


class JobResponseMixin(HordeAPIDataObject):  # TODO: this model may not actually exist as such in the API
    """Mix-in class for data relating to any generation jobs."""

    id_: JobID = Field(alias="id")
    """The UUID for this job."""

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v


class WorkerRequestMixin(HordeAPIDataObject):
    """Mix-in class for data relating to worker requests."""

    worker_id: str | WorkerID
    """The UUID of the worker in question for this request."""


class LorasPayloadEntry(HordeAPIDataObject):
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
    is_version: bool = Field(default=False)
    """If true, will treat the lora name as a version ID."""


class TIPayloadEntry(HordeAPIDataObject):
    name: str = Field(min_length=1, max_length=255)
    inject_ti: str | None = None
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
            logger.debug("strength is only valid when inject_ti is set")
        return self


class ExtraSourceImageEntry(HordeAPIDataObject):
    """Represents a single extra source image.

    v2 API Model: `ExtraSourceImage`
    """

    image: str = Field(min_length=1)
    """The URL of the image to download."""
    strength: float = Field(default=1, ge=-5, le=5)
    """The strength to apply to this image on various operations."""


class SingleWarningEntry(HordeAPIDataObject):
    """Represents a single warning.

    v2 API Model: `RequestSingleWarning`
    """

    code: str = Field(min_length=1)
    """The code uniquely identifying this warning."""
    message: str = Field(min_length=1)
    """The human-readable description of this warning"""


class ImageGenerateParamMixin(HordeAPIDataObject):
    """Mix-in class of some of the data included in a request to the `/v2/generate/async` endpoint.

    Also is the corresponding information returned on a job pop to the `/v2/generate/pop` endpoint.
    v2 API Model: `ModelPayloadStable`
    """

    model_config = (
        ConfigDict(frozen=True) if not os.getenv("TESTS_ONGOING") else ConfigDict(frozen=True, extra="forbid")
    )

    sampler_name: KNOWN_SAMPLERS | str = KNOWN_SAMPLERS.k_lms
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
    post_processing: list[str | KNOWN_UPSCALERS | KNOWN_FACEFIXERS | KNOWN_MISC_POST_PROCESSORS] = Field(
        default_factory=list,
    )
    """A list of post-processing models to use."""
    post_processing_order: POST_PROCESSOR_ORDER_TYPE = POST_PROCESSOR_ORDER_TYPE.facefixers_first
    """The order in which to apply post-processing models.
    Applying upscalers or removing backgrounds before facefixers costs less kudos."""
    karras: bool = True
    """Set to True if you want to use the Karras scheduling."""
    tiling: bool = False
    """Deprecated."""
    hires_fix: bool = False
    """Set to True if you want to use the hires fix."""
    clip_skip: int = Field(default=1, ge=1, le=12)
    """The number of clip layers to skip."""
    control_type: str | KNOWN_CONTROLNETS | None = None
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

    @field_validator("width", "height", mode="before")
    def width_divisible_by_64(cls, value: int) -> int:
        """Ensure that the width is divisible by 64."""
        if value % 64 != 0:
            raise ValueError("width must be divisible by 64")
        return value

    use_nsfw_censor: bool = False

    @field_validator("sampler_name")
    def sampler_name_must_be_known(cls, v: str | KNOWN_SAMPLERS) -> str | KNOWN_SAMPLERS:
        """Ensure that the sampler name is in this list of supported samplers."""
        if (isinstance(v, str) and v in KNOWN_SAMPLERS.__members__) or (isinstance(v, KNOWN_SAMPLERS)):
            return v

        logger.warning(f"Unknown sampler name {v}. Is your SDK out of date or did the API change?")

        return v

    # @model_validator(mode="after")
    # def validate_hires_fix(self) -> ImageGenerateParamMixin:
    #     if self.hires_fix and (self.width < 512 or self.height < 512):
    #         raise ValueError("hires_fix is only valid when width and height are both >= 512")
    #     return self

    @field_validator("seed")
    def random_seed_if_none(cls, v: str | None) -> str | None:
        """If the seed is None, generate a random seed."""
        if v is None:
            random_seed = str(random.randint(1, 1000000000))
            logger.debug(f"Using random seed ({random_seed})")
            return random_seed

        return v

    @field_validator("post_processing")
    def post_processors_must_be_known(
        cls,
        v: list[str | KNOWN_UPSCALERS | KNOWN_FACEFIXERS | KNOWN_MISC_POST_PROCESSORS],
    ) -> list[str | KNOWN_UPSCALERS | KNOWN_FACEFIXERS | KNOWN_MISC_POST_PROCESSORS]:
        """Ensure that the post processors are in this list of supported post processors."""

        _valid_types: list[type] = [str, KNOWN_UPSCALERS, KNOWN_FACEFIXERS, KNOWN_MISC_POST_PROCESSORS]
        for post_processor in v:
            if post_processor not in _all_valid_post_processors_names_and_values or (
                type(post_processor) not in _valid_types
            ):
                logger.warning(
                    f"Unknown post processor {post_processor}. Is your SDK out of date or did the API change?",
                )
        return v

    @field_validator("control_type")
    def control_type_must_be_known(cls, v: str | KNOWN_CONTROLNETS | None) -> str | KNOWN_CONTROLNETS | None:
        """Ensure that the control type is in this list of supported control types."""
        if v is None:
            return None
        if isinstance(v, KNOWN_CONTROLNETS):
            return v
        if v in KNOWN_CONTROLNETS.__members__:
            return v

        logger.warning(f"Unknown control type {v}. Is your SDK out of date or did the API change?")
        return v


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


class GenMetadataEntry(HordeAPIDataObject):
    """Represents a single generation metadata entry.

    v2 API Model: `GenerationMetadataStable`
    """

    type_: METADATA_TYPE | str = Field(alias="type")
    """The relevance of the metadata field."""
    value: METADATA_VALUE | str = Field()
    """The value of the metadata field."""
    ref: str | None = Field(default=None, max_length=255)
    """Optionally a reference for the metadata (e.g. a lora ID)"""

    @field_validator("type_")
    def validate_type(cls, v: str | METADATA_TYPE) -> str | METADATA_TYPE:
        """Ensure that the type is in this list of supported types."""
        if isinstance(v, METADATA_TYPE):
            return v
        if isinstance(v, str) and v not in METADATA_TYPE.__members__:
            logger.warning(f"Unknown metadata type {v}. Is your SDK out of date or did the API change?")
        return v

    @field_validator("value")
    def validate_value(cls, v: str | METADATA_VALUE) -> str | METADATA_VALUE:
        """Ensure that the value is in this list of supported values."""
        if isinstance(v, METADATA_VALUE):
            return v
        if isinstance(v, str) and v not in METADATA_VALUE.__members__:
            logger.warning(f"Unknown metadata value {v}. Is your SDK out of date or did the API change?")
        return v
