"""AI-Horde specific constants, including enums defined on the API."""

from enum import auto

from strenum import StrEnum

GENERATION_MAX_LIFE = (60 * 20) - 30
"""The maximum time for the life of a generation request in seconds, minus 30 seconds to account for network latency.

This is the amount of time that passes before the server will delete the request.
"""


class GENERATION_STATE(StrEnum):
    """The generation states that are known to the API.

    (ok, censored, faulted, etc...)
    """

    _NONE = ""  # FIXME

    ok = auto()
    censored = auto()
    faulted = auto()
    csam = auto()
    waiting = auto()
    processing = auto()
    partial = auto()
    cancelled = auto()
    done = auto()


class WORKER_TYPE(StrEnum):
    """The worker types that are known to the API.

    (alchemy, image, text, etc...)
    """

    image = auto()
    text = auto()
    interrogation = auto()
    alchemist = "interrogation"


class ALCHEMY_FORMS(StrEnum):
    """Forms (type of services) for alchemist type workers.

    (nsfw, caption, interrogation, post_process, etc...)
    """

    nsfw = auto()
    caption = auto()
    interrogation = auto()
    post_process = auto()


class KNOWN_SAMPLERS(StrEnum):
    """The samplers that are known to the API.

    (k_lms, k_heun, DDIM, etc)
    """

    k_lms = auto()
    k_heun = auto()
    k_euler = auto()
    k_euler_a = auto()
    k_dpm_2 = auto()
    k_dpm_2_a = auto()
    k_dpm_fast = auto()
    k_dpm_adaptive = auto()
    k_dpmpp_2s_a = auto()
    k_dpmpp_2m = auto()
    dpmsolver = auto()
    k_dpmpp_sde = auto()
    lcm = auto()
    DDIM = "DDIM"


class KNOWN_CONTROLNETS(StrEnum):
    """The controlnets that are known to the API."""

    canny = auto()
    hed = auto()
    depth = auto()
    normal = auto()
    openpose = auto()
    seg = auto()
    scribble = auto()
    fakescribbles = auto()
    hough = auto()


class KNOWN_SOURCE_PROCESSING(StrEnum):
    """The source processing methods that are known to the API.

    (txt2img, img2img, inpainting, etc)
    """

    txt2img = auto()
    img2img = auto()
    inpainting = auto()
    outpainting = auto()


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


class POST_PROCESSOR_ORDER_TYPE(StrEnum):
    """The post processor order types that are known to the API.

    (facefixers_first, upscalers_first, custom, etc)
    """

    facefixers_first = auto()
    upscalers_first = auto()
    custom = auto()


DEFAULT_POST_PROCESSOR_ORDER = POST_PROCESSOR_ORDER_TYPE.facefixers_first


class KNOWN_CLIP_BLIP_TYPES(StrEnum):
    caption = auto()
    interrogation = auto()
    nsfw = auto()


class KNOWN_INTERROGATORS(StrEnum):
    vit_l_14 = "ViT-L/14"


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


class METADATA_TYPE(StrEnum):
    """The generation metadata types that are known to the API.

    (lora, ti, censorship, etc)
    """

    lora = auto()
    ti = auto()
    censorship = auto()
    source_image = auto()
    source_mask = auto()


class METADATA_VALUE(StrEnum):
    """The generation metadata values that are known to the API.

    (download_failed, baseline_mismatch, etc)
    """

    download_failed = auto()
    parse_failed = auto()
    baseline_mismatch = auto()
    csam = auto()
    nsfw = auto()
