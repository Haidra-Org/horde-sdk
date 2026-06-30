from enum import auto

from strenum import StrEnum


class ALCHEMY_PARAMETER_FIELDS(StrEnum):
    """Field names that commonly appear in alchemy parameter payloads."""

    result_id = auto()
    form = auto()
    source_image = auto()
    upscaler = auto()
    facefixer = auto()
    interrogator = auto()
    caption_model = auto()
    nsfw_detector = auto()


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
    vectorize = auto()
    """Vectorization (raster image -> SVG)."""


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

    # Names begin with a digit (the upscale factor), so the member identifier prepends the
    # spelled-out leading digit while the value keeps the on-disk file-stem form.
    four_4xNomos8kSC = "4xNomos8kSC"
    four_4xLSDIRplus = "4xLSDIRplus"
    four_4xNomosWebPhoto_RealPLKSR = "4xNomosWebPhoto_RealPLKSR"
    four_4xNomos2_realplksr_dysample = "4xNomos2_realplksr_dysample"
    four_4xNomos2_hq_dat2 = "4xNomos2_hq_dat2"
    two_2xModernSpanimationV1 = "2xModernSpanimationV1"


class KNOWN_FACEFIXERS(StrEnum):
    """The facefixers that are known to the API.

    (CodeFormers, etc)
    """

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    GFPGAN = auto()
    CodeFormers = auto()

    GFPGANv1_3 = "GFPGANv1.3"
    """GFPGANv1.3: the predecessor GFPGAN weight, more identity-faithful than the default v1.4."""
    RestoreFormer = auto()
    """RestoreFormer: an Apache-2.0 transformer-based blind face restorer, realism-oriented."""


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

    four_4xNomos8kSC = KNOWN_UPSCALERS.four_4xNomos8kSC
    four_4xLSDIRplus = KNOWN_UPSCALERS.four_4xLSDIRplus
    four_4xNomosWebPhoto_RealPLKSR = KNOWN_UPSCALERS.four_4xNomosWebPhoto_RealPLKSR
    four_4xNomos2_realplksr_dysample = KNOWN_UPSCALERS.four_4xNomos2_realplksr_dysample
    four_4xNomos2_hq_dat2 = KNOWN_UPSCALERS.four_4xNomos2_hq_dat2
    two_2xModernSpanimationV1 = KNOWN_UPSCALERS.two_2xModernSpanimationV1

    GFPGAN = KNOWN_FACEFIXERS.GFPGAN
    CodeFormers = KNOWN_FACEFIXERS.CodeFormers
    GFPGANv1_3 = KNOWN_FACEFIXERS.GFPGANv1_3
    RestoreFormer = KNOWN_FACEFIXERS.RestoreFormer

    strip_background = KNOWN_MISC_POST_PROCESSORS.strip_background

    vectorize = KNOWN_ALCHEMY_FORMS.vectorize


def is_upscaler_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an upscaler form."""
    value = form
    if isinstance(form, KNOWN_ALCHEMY_TYPES):
        value = form.value

    return value in KNOWN_UPSCALERS.__members__ or value in KNOWN_UPSCALERS.__members__.values()


def is_facefixer_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is a facefixer form."""
    value = form
    if isinstance(form, KNOWN_ALCHEMY_TYPES):
        value = form.value

    return value in KNOWN_FACEFIXERS.__members__ or value in KNOWN_FACEFIXERS.__members__.values()


def is_interrogator_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an interrogator form."""
    return form == KNOWN_CLIP_BLIP_TYPES.interrogation


def is_caption_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is a caption form."""
    return form == KNOWN_CLIP_BLIP_TYPES.caption


def is_nsfw_detector_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an NSFW form."""
    return form == KNOWN_CLIP_BLIP_TYPES.nsfw


def is_strip_background_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is a strip background form."""
    return form == KNOWN_MISC_POST_PROCESSORS.strip_background


def is_image_vectorizer_form(form: KNOWN_ALCHEMY_TYPES | str) -> bool:
    """Check if the form is an image vectorizer (raster -> SVG) form."""
    return form == KNOWN_ALCHEMY_FORMS.vectorize
