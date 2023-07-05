from enum import auto

from strenum import StrEnum


class KNOWN_SAMPLERS(StrEnum):
    """The samplers that are known to the API."""

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
    txt2img = auto()
    img2img = auto()
    inpainting = auto()
    outpainting = auto()


class GENERATION_STATE(StrEnum):
    ok = auto()
    censored = auto()
