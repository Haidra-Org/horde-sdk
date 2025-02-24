from enum import auto

from strenum import StrEnum


class KNOWN_ALCHEMY_FORMS(StrEnum):
    """Forms (type of services) for alchemist type workers.

    (nsfw, caption, interrogation, post_process, etc...)
    """

    nsfw = auto()
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

    vit_l_14 = "ViT-L/14"
