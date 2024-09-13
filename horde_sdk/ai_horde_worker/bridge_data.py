"""The bridge data file definitions and functions for any horde worker type."""

from __future__ import annotations

import pathlib
import re
import urllib.parse

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from strenum import StrEnum

from horde_sdk.ai_horde_api.consts import ALCHEMY_FORMS
from horde_sdk.ai_horde_worker.locale_info.bridge_data_fields import BRIDGE_DATA_FIELD_DESCRIPTIONS
from horde_sdk.generic_api.consts import ANON_API_KEY

_UNREASONABLE_NUMBER_OF_MODELS = 1000
"""1000"""


class MetaInstruction(StrEnum):
    """Model load instructions which requiring further processing to resolve."""

    ALL_REGEX = r"all$|all models?$"

    ALL_SDXL_REGEX = r"all sdxl$|all sdxl models?$"
    ALL_SD15_REGEX = r"all sd15$|all sd15 models?$"
    ALL_SD21_REGEX = r"all sd21$|all sd21 models?$"

    ALL_SFW_REGEX = r"all sfw$|all sfw models?$"
    ALL_NSFW_REGEX = r"all nsfw$|all nsfw models?$"

    ALL_INPAINTING_REGEX = r"all inpainting$|all inpainting models?$"

    TOP_N_REGEX = r"TOP (\d+)"
    """The regex to use to match the top N models. The number is in a capture group on its own."""

    BOTTOM_N_REGEX = r"BOTTOM (\d+)"


class BaseHordeBridgeData(BaseModel):
    """The base bridge data file for all worker types."""

    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extra_params_warning(self) -> BaseHordeBridgeData:
        """Warn on extra parameters being passed."""
        if self.model_extra is not None:
            for key in self.model_extra:
                logger.warning(f"Unknown parameter {key} in bridge data file.")

        return self


class SharedHordeBridgeData(BaseHordeBridgeData):
    """The base bridge data file for all worker types."""

    #
    # Shared Worker-type Settings
    #

    api_key: str = Field(
        default=ANON_API_KEY,
        title="API Key",
    )
    """The API key to use to authenticate with the Horde API. Defaults to the anonymous API key."""

    default_worker_name: str = Field("An Awesome AI Horde Worker", alias="worker_name")
    """The default name for any worker type. This is used to easily identify the worker.

    Note that if the user switches to a different worker type after having run a different worker type, the name will
    be rejected by the Horde API. This is because the name is unique to the worker type.
    """

    models_folder_parent: str = Field(
        default="./",
        alias="cache_home",
    )
    """The directories to use to store the model folders. The spirit of this derives from `XDG_CACHE_HOME`, but it is
    not a *volatile* cache. It is the ordinary location for the models. Defaults to the current working directory."""

    temp_dir: str = "./tmp/"
    """The directory to use for temporary files such as model caches. Defaults to `./tmp/`."""

    allow_unsafe_ip: bool = True
    """Whether to allow img2img from unsafe IP addresses. This is only relevant if img2img is enabled."""

    priority_usernames: list[str] = Field(default_factory=list)
    """A list of usernames to prioritize. The API always considers this worker's user to be on this list."""

    stats_output_frequency: int = Field(default=30, json_schema_extra={"unit": "seconds"})
    """The frequency at which to output stats to the console, in seconds. Set to 0 to disable."""
    disable_terminal_ui: bool = False
    """Whether to disable the terminal UI. This is useful for running the worker in a container."""
    always_download: bool = True
    """Whether to always download models, without prompting for permission for each one."""
    suppress_speed_warnings: bool = False
    """Whether to suppress warnings about slower than ideal generations."""
    horde_url: str = ""  # TODO: consts.DEFAULT_HORDE_API_URL
    """The URL of the Horde API to use. Defaults to the official API."""

    @field_validator("horde_url")
    def validate_url(cls, v: str) -> str:
        """Validate the URL is valid."""
        parsed_url = urllib.parse.urlparse(v)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError(f"Invalid URL: {v}")
        return v

    @field_validator("api_key")
    def validate_api_key_length(cls, v: str) -> str:
        """Validate that the API key is the correct length."""
        if v == ANON_API_KEY:
            return v
        if len(v) != 22:
            raise ValueError("API key must be 22 characters long")
        return v

    @field_validator("models_folder_parent", "temp_dir")
    def validate_is_dir(cls, v: str) -> str:
        """Validate that the path is a directory."""
        paths_list = []
        # Does it specific multiple directories?
        if ";" in v:
            for sub_v in v.split(";"):
                paths_list.append(sub_v)
        else:
            paths_list.append(v)
        for sub_v in paths_list:
            # See if it's a well-formed path, but don't check if it exists
            pathlib.Path(sub_v).absolute()

        return v


class ImageWorkerBridgeData(SharedHordeBridgeData):
    """The bridge data file for a Dreamer or Alchemist worker."""

    extra_stable_diffusion_models_folders: list[str] = Field(default_factory=list)
    """A list of extra folders to search for stable diffusion models."""

    allow_controlnet: bool = False
    """Whether to allow the use of ControlNet. This requires img2img to be enabled."""

    allow_sdxl_controlnet: bool = False
    """Whether to allow the use of SDXL ControlNet. This requires controlnet to be enabled."""

    allow_img2img: bool = True
    """Whether to allow the use of img2img."""

    allow_lora: bool = False
    """Whether to allow the use of LoRA."""

    extra_slow_worker: bool = False
    """Marks the worker as extra slow."""

    limit_max_steps: bool = False
    """Prevents the worker picking up jobs with more steps than the model average."""

    max_lora_cache_size: int = Field(
        default=10,
        ge=10,
        le=2048,  # I do not foresee anyone having a 2TB lora cache
        json_schema_extra={"unit": "GB"},
    )
    """The maximum size of the LoRA cache, in gigabytes."""

    allow_inpainting: bool = Field(
        default=False,
        alias="allow_painting",
    )
    """Whether to allow the use of inpainting."""

    allow_post_processing: bool = False
    """Whether to allow the use of post-processing."""

    blacklist: list[str] = Field(
        default_factory=list,
    )
    """A list of terms or phrases to blacklist. Jobs containing these terms will be not be assigned to this worker."""

    censor_nsfw: bool = False
    """Whether to censor NSFW content."""

    censorlist: list[str] = Field(
        default_factory=list,
    )
    """A list of terms to allow through the censor. Jobs containing these terms will not be censored for those words
    alone."""

    disable_disk_cache: bool = False
    """Whether to disable the disk cache."""

    dreamer_worker_name: str = Field(
        default="An Awesome Dreamer",
        alias="dreamer_name",
    )

    dynamic_models: bool = False
    """Whether to dynamically switch the models loaded to correspond to the models with the longest queues."""

    max_dynamic_models_to_download: int = Field(
        default=10,
        ge=0,
        le=_UNREASONABLE_NUMBER_OF_MODELS,
        alias="max_models_to_download",
    )
    """The maximum number of models to download."""

    number_of_dynamic_models_to_load: int = Field(
        default=1,
        ge=0,
        le=_UNREASONABLE_NUMBER_OF_MODELS,
        alias="number_of_dynamic_models",
    )
    """The number of dynamic models to load at a time."""

    max_power: int = Field(
        default=8,
        ge=1,
        le=512,
        json_schema_extra={"unit": "* (8 * 64 * 64) pixels"},
    )
    """The factor in the equation `max_power * (8 * 64 * 64)`. This will be the maximum number of pixels that can be
    generated (with inference) in a single job by this worker."""

    image_models_to_load: list[str] = Field(
        default_factory=list,
        alias="models_to_load",
    )

    """A list of models to load. This can be a list of model names, or a list of model loading instructions, such as
    `top 100` or `all models`."""

    image_models_to_skip: list[str] = Field(
        default_factory=list,
        alias="models_to_skip",
    )
    """When a meta model loading instruction is given, like `top 100`, models in this list will be skipped."""

    nsfw: bool = True
    """Whether to allow NSFW content."""

    queue_size: int = Field(default=1, ge=0, le=4)
    """The number of jobs to queue."""

    max_threads: int = Field(
        default=1,
        ge=1,
        le=16,  # 8 already seems incredibly out of reach for most people, but I have set it to 16 just in case
    )
    """The number of threads to use for inference."""

    max_batch: int = Field(
        default=1,
        ge=1,
        le=20,  # 20 is the max per request on the horde
    )
    """The number of threads to use for inference."""

    require_upfront_kudos: bool = False
    """Whether to require upfront kudos for jobs. This effectively makes the worker reject jobs from
    the anonymous API key, or from keys with no kudos."""

    ram_to_leave_free: str = Field(
        default="80%",
        pattern=r"^\d+%$|^\d+$",
        json_schema_extra={"unit": "Percent or MB"},
    )
    """The amount of RAM to leave free for the system to use. This is a percentage or a number in megabytes."""

    vram_to_leave_free: str | None = Field(
        default="80%",
        pattern=r"^\d+%$|^\d+$",
        json_schema_extra={"unit": "Percent or MB"},
    )
    """The amount of VRAM to leave free for the system to use. This is a percentage or a number in megabytes."""

    #
    # Alchemist Settings
    #

    alchemist_name: str = "An Awesome Alchemist"
    """The name of the worker if it is an alchemist. This is used to easily identify the worker."""

    forms: list[str] = Field(
        default_factory=list,
    )
    """The type of services or processing an alchemist worker will provide."""

    @field_validator("forms", mode="before")
    def default_forms(cls, v: list[str]) -> list[str]:
        """Set the default forms if none are specified."""
        if v is None or len(v) == 0:
            logger.info("Using the default alchemy forms as none were specified.")
            return ["caption", "nsfw", "interrogation", "post-process"]

        return v

    @model_validator(mode="after")
    def validate_model(self) -> ImageWorkerBridgeData:
        """Validate that the parameters are not conflicting and make any fixed adjustments."""
        if not self.allow_img2img and self.allow_controlnet:
            logger.warning(
                (
                    "allow_controlnet is set to True, but allow_img2img is set to False. "
                    "ControlNet requires img2img to be enabled. Setting allow_controlnet to false."
                ),
            )
            self.allow_controlnet = False

        if not self.allow_controlnet and self.allow_sdxl_controlnet:
            logger.warning(
                (
                    "allow_sdxl_controlnet is set to True, but allow_controlnet is set to False. "
                    "SDXL ControlNet requires allow_controlnet to be enabled. Setting allow_sdxl_controlnet to false."
                ),
            )
            self.allow_sdxl_controlnet = False

        self.image_models_to_skip.append("SDXL_beta::stability.ai#6901")  # FIXME: no magic strings

        return self

    _meta_load_instructions: list[str] | None = None
    _meta_skip_instructions: list[str] | None = None

    @property
    def meta_load_instructions(self) -> list[str] | None:
        """The meta load instructions."""
        return self._meta_load_instructions

    @model_validator(mode="after")
    def handle_meta_instructions(self) -> ImageWorkerBridgeData:
        """Handle the meta instructions by resolving and applying them."""
        # See if any entries are meta instructions, and if so, remove them and place them in _meta_load_instructions
        for instruction_regex in MetaInstruction.__members__.values():
            for i, model in enumerate(self.image_models_to_load):
                if re.match(instruction_regex, model, re.IGNORECASE):
                    if self._meta_load_instructions is None:
                        self._meta_load_instructions = []
                    self._meta_load_instructions.append(model)
                    self.image_models_to_load.pop(i)

        return self

    @property
    def meta_skip_instructions(self) -> list[str] | None:
        """The meta skip instructions."""
        return self._meta_skip_instructions

    @model_validator(mode="after")
    def handle_meta_skip_instructions(self) -> ImageWorkerBridgeData:
        """Handle the meta skip instructions by resolving and applying them."""
        # See if any entries are meta instructions, and if so, remove them and place them in _meta_skip_instructions
        for instruction_regex in MetaInstruction.__members__.values():
            for i, model in enumerate(self.image_models_to_skip):
                if re.match(instruction_regex, model, re.IGNORECASE):
                    if self._meta_skip_instructions is None:
                        self._meta_skip_instructions = []
                    self._meta_skip_instructions.append(model)
                    self.image_models_to_skip.pop(i)

        return self

    @field_validator("image_models_to_load")
    def validate_models_to_load(cls, v: list[str]) -> list[str]:
        """Validate and parse the models to load."""
        if not isinstance(v, list):
            v = [v]
        if not v:
            v = ["top 2"]
            logger.warning("No models specified in bridgeData.yaml. Defaulting to top 2 models.")
        return v

    @field_validator("ram_to_leave_free", "vram_to_leave_free")
    def validate_ram_to_leave_free(cls, v: str | int | float) -> str | int | float:
        """Validate VRAM/RAM to leave free."""
        if isinstance(v, str):
            if v.isdigit():
                v = int(v)
            elif v.endswith("%"):
                _ = float(v[:-1])
                if _ < 0 or _ > 100:
                    raise ValueError("RAM to leave free must be between 0 and 100%")
        else:
            if v < 0:
                raise ValueError("RAM to leave free must be greater than or equal to 0")
        return v

    @field_validator("forms")
    def validate_alchemy_forms(cls, v: list[str]) -> list[str | ALCHEMY_FORMS]:
        """Validate the alchemy forms (services offered)."""
        if not isinstance(v, list):
            raise ValueError("forms must be a list")
        validated_forms = []
        for form in v:
            form = str(form).lower()
            form = form.replace("-", "_")
            if form not in ALCHEMY_FORMS.__members__:
                raise ValueError(f"Invalid form: {form}")
            validated_forms.append(form)
        return validated_forms


class ScribeBridgeData(SharedHordeBridgeData):
    """The bridge data file subset for a Scribe worker."""

    # Scribe Settings
    scribe_name: str = "An Awesome Scribe"
    kai_url: str = "http://localhost:5000"
    """The URL of the KoboldAI API to use. Defaults to the official API."""

    max_context_length: int = Field(
        default=1024,
        ge=1,
        le=16384,  # This is just a sanity check, I doubt anyone would want to go this high
        json_schema_extra={"unit": "tokens"},
    )
    """The maximum number of tokens to use for context with a scribe job."""

    max_length: int = Field(
        default=80,
        ge=1,
        le=16384,  # This is just a sanity check, I doubt anyone would want to go this high
        json_schema_extra={"unit": "tokens"},
    )
    """The maximum number of tokens to generate for a scribe job."""

    branded_model: bool = True
    """If true, this is a custom scribe model, and the horde API will identify uniquely to this worker's API key."""


class CombinedHordeBridgeData(ImageWorkerBridgeData, ScribeBridgeData):
    """The bridge data file for a worker bridge that supports all worker types."""


# Get all BaseModels from the current file
ALL_DATA_FILES_TYPES: list[type[BaseModel]] = [
    SharedHordeBridgeData,
    ImageWorkerBridgeData,
    ScribeBridgeData,
    CombinedHordeBridgeData,
]


# Dynamically add descriptions to the fields of all the base models
for data_file_type in ALL_DATA_FILES_TYPES:
    for field_name, field in data_file_type.model_fields.items():
        if field_name in BRIDGE_DATA_FIELD_DESCRIPTIONS:
            field.description = BRIDGE_DATA_FIELD_DESCRIPTIONS[field_name]
