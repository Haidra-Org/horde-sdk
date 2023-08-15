"""AI-Horde specific constants, including enums defined on the API."""

from enum import auto

from strenum import StrEnum


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
    DDIM = "DDIM"


class KNOWN_SOURCE_PROCESSING(StrEnum):
    """The source processing methods that are known to the API.

    (txt2img, img2img, inpainting, etc)
    """

    txt2img = auto()
    img2img = auto()
    inpainting = auto()
    outpainting = auto()


class GENERATION_STATE(StrEnum):
    """The generation states that are known to the API.

    (ok, censored, faulted, etc...)
    """

    ok = auto()
    censored = auto()
    faulted = auto()
    csam = auto()


class WORKER_TYPE(StrEnum):
    """The worker types that are known to the API.

    (alchemy, image, text, etc...)
    """

    image = auto()
    text = auto()
    interrogation = auto()
    alchemist = "interrogation"  # TODO


class ALCHEMY_FORMS(StrEnum):
    """Forms (type of services) for alchemist type workers.

    (nsfw, caption, interrogation, post_process, etc...)
    """

    nsfw = auto()
    caption = auto()
    interrogation = auto()
    post_process = auto()


class KNOWN_ALCHEMY_TYPES(StrEnum):
    """The alchemy processes (types) that are known to the API."""

    caption = auto()
    interrogation = auto()
    nsfw = auto()
    GFPGAN = auto()
    RealESRGAN_x4plus = auto()
    RealESRGAN_x2plus = auto()
    RealESRGAN_x4plus_anime_6B = auto()
    NMKD_Siax = auto()
    fourx_AnimeSharp = "4x_AnimeSharp"
    CodeFormers = auto()
    strip_background = auto()
