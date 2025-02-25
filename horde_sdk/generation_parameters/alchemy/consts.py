from enum import auto

from strenum import StrEnum


class KNOWN_ALCHEMY_FORMS(StrEnum):
    """Forms (type of services) for alchemist type workers.

    (nsfw, caption, interrogation, post_process, etc...)
    """

    nsfw = auto()
    """NSFW detection."""
    caption = auto()
    """Captioning (i.e., BLIP)."""
    interrogation = auto()
    """Interrogation (i.e., CLIP)."""
    post_process = auto()
    """Upscaling, facefixing, etc."""


class KNOWN_UPSCALERS(StrEnum):
    """The upscalers that are known to the API.

    (RealESRGAN_x4plus, RealESRGAN_x2plus, RealESRGAN_x4plus_anime_6B, etc)
    """

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    RealESRGAN_x4plus = auto()
    RealESRGAN_x2plus = auto()
    RealESRGAN_x4plus_anime_6B = auto()
    NMKD_Siax = auto()
    four_4x_AnimeSharp = "4x_AnimeSharp"
    """AKA 4x_AnimeSharp"""


class KNOWN_FACEFIXERS(StrEnum):
    """The facefixers that are known to the API.

    (CodeFormers, etc)
    """

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    GFPGAN = auto()
    CodeFormers = auto()


class KNOWN_MISC_POST_PROCESSORS(StrEnum):
    """The misc post processors that are known to the API.

    (strip_background, etc)
    """

    strip_background = auto()


_all_valid_post_processors_names_and_values = (
    list(KNOWN_UPSCALERS.__members__.keys())
    + list(KNOWN_UPSCALERS.__members__.values())
    + list(KNOWN_FACEFIXERS.__members__.keys())
    + list(KNOWN_FACEFIXERS.__members__.values())
    + list(KNOWN_MISC_POST_PROCESSORS.__members__.keys())
    + list(KNOWN_MISC_POST_PROCESSORS.__members__.values())
)
"""Used to validate post processor names and values. \
    This is because some post processor names are not valid python variable names."""


class KNOWN_CLIP_BLIP_TYPES(StrEnum):
    """The CLIP and BLIP models that are known to the API."""

    caption = auto()
    """The caption (BLIP) model."""
    interrogation = auto()
    """The interrogation (CLIP) model."""
    nsfw = auto()
    """The NSFW model."""


class KNOWN_INTERROGATORS(StrEnum):
    """The interrogators that are known to the API."""

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    vit_l_14 = "sentence-transformers/clip-ViT-L-14"
    vit_big_g_14_laion2b_39b_b160k = "laion/CLIP-ViT-bigG-14-laion2B-39B-b160k"


class KNOWN_CAPTION_MODELS(StrEnum):
    """The caption models that are known to the API."""

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    BLIP_BASE_SALESFORCE = "Salesforce/blip-image-captioning-base"
    BLIP_LARGE_SALESFORCE = "Salesforce/blip-image-captioning-large"


class KNOWN_NSFW_DETECTOR(StrEnum):
    """The NSFW detectors that are known to the API."""

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    horde_safety = auto()
    """The AI-Horde horde_safety package."""

    compvis_safety_checkers = auto()
    """The compvis safety checker model released with stable diffusion."""


class KNOWN_ALCHEMY_TYPES(StrEnum):
    """The alchemy processes (types) that are known to the API.

    (caption, GFPGAN, strip_background, etc)
    """

    _NONE = ""  # FIXME

    caption = KNOWN_CLIP_BLIP_TYPES.caption
    interrogation = KNOWN_CLIP_BLIP_TYPES.interrogation
    nsfw = KNOWN_CLIP_BLIP_TYPES.nsfw

    RealESRGAN_x4plus = KNOWN_UPSCALERS.RealESRGAN_x4plus
    RealESRGAN_x2plus = KNOWN_UPSCALERS.RealESRGAN_x2plus
    RealESRGAN_x4plus_anime_6B = KNOWN_UPSCALERS.RealESRGAN_x4plus_anime_6B
    NMKD_Siax = KNOWN_UPSCALERS.NMKD_Siax
    fourx_AnimeSharp = KNOWN_UPSCALERS.four_4x_AnimeSharp

    GFPGAN = KNOWN_FACEFIXERS.GFPGAN
    CodeFormers = KNOWN_FACEFIXERS.GFPGAN

    strip_background = KNOWN_MISC_POST_PROCESSORS.strip_background


def is_upscaler_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an upscaler form."""
    return form in KNOWN_UPSCALERS or form in KNOWN_UPSCALERS.__members__.values()


def is_facefixer_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is a facefixer form."""
    return form in KNOWN_FACEFIXERS or form in KNOWN_FACEFIXERS.__members__.values()


def is_interrogator_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an interrogator form."""
    return form in KNOWN_INTERROGATORS or form in KNOWN_INTERROGATORS.__members__.values()


def is_caption_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is a caption form."""
    return form in KNOWN_CAPTION_MODELS or form in KNOWN_CAPTION_MODELS.__members__.values()


def is_nsfw_detector_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an NSFW form."""
    return form in KNOWN_NSFW_DETECTOR or form in KNOWN_NSFW_DETECTOR.__members__.values()
