from strenum import StrEnum


from enum import auto


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


class KNOWN_SCHEDULERS(StrEnum):
    """The schedulers that are known to the API.

    (normal, karras, exponential, etc)
    """

    normal = auto()
    karras = auto()
    exponential = auto()
    sgm_uniform = auto()
    simple = auto()
    ddim_uniform = auto()
    beta = auto()
    linear_quadratic = auto()
    kl_optimal = auto()


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
    outpainting = "inpainting"
    """Outpainting is just"""
    remix = auto()
    """Stable Cascade Remix"""
