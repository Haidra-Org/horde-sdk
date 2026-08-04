from enum import auto

from strenum import StrEnum


class KNOWN_IMAGE_SAMPLERS(StrEnum):
    """The samplers that are known to the API.

    (k_lms, k_heun, DDIM, etc)

    The members below `DDIM` are the extended solvers, which only bridges new enough to render them
    are offered. They carry the image backend's own spelling rather than the `k_` prefix of the
    k-diffusion block, because they are backend-native solvers rather than k-diffusion samplers.

    The members below `sa_solver` complete the backend's non-`_gpu` solver list. The `_gpu` variants
    are deliberately absent: they differ from their counterparts only in which device draws the noise,
    which is a worker-side concern rather than a request-side choice. Like the block above them these
    names are shared letter for letter with the backend.
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

    uni_pc = auto()
    uni_pc_bh2 = auto()
    dpmpp_2m_sde = auto()
    dpmpp_3m_sde = auto()
    ddpm = auto()
    deis = auto()
    ipndm = auto()
    res_multistep = auto()
    gradient_estimation = auto()
    heunpp2 = auto()
    er_sde = auto()
    sa_solver = auto()

    euler_cfg_pp = auto()
    euler_ancestral_cfg_pp = auto()
    exp_heun_2_x0 = auto()
    exp_heun_2_x0_sde = auto()
    dpmpp_2s_ancestral_cfg_pp = auto()
    dpmpp_2m_cfg_pp = auto()
    dpmpp_2m_sde_heun = auto()
    ipndm_v = auto()
    res_multistep_cfg_pp = auto()
    res_multistep_ancestral = auto()
    res_multistep_ancestral_cfg_pp = auto()
    gradient_estimation_cfg_pp = auto()
    seeds_2 = auto()
    seeds_3 = auto()
    sa_solver_pece = auto()


class KNOWN_IMAGE_SCHEDULERS(StrEnum):
    """The schedulers that are known to the API.

    (normal, karras, exponential, etc)

    `align_your_steps` and `gits` are not schedules the backend names alongside the others: they are
    sigma generators supplied by separate nodes, and each is only defined for a subset of the known
    baselines. See
    [`SCHEDULER_BASELINE_APPLICABILITY`][horde_sdk.generation_parameters.image.constraints.SCHEDULER_BASELINE_APPLICABILITY]
    for where they may be requested.
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

    align_your_steps = auto()
    gits = auto()


class KNOWN_IMAGE_CONTROLNETS(StrEnum):
    """The controlnets that are known to the API.

    This is the full image-generation `control_type` surface: every member of
    :class:`horde_sdk.generation_parameters.alchemy.consts.KNOWN_ANNOTATION_CONTROL_TYPES` plus `hough`,
    the legacy image-generation spelling of the `mlsd` line detector. Both spellings validate; `hough`
    is kept so existing clients keep working.
    """

    canny = auto()
    hed = auto()
    depth = auto()
    normal = auto()
    openpose = auto()
    seg = auto()
    scribble = auto()
    fakescribbles = auto()
    hough = auto()
    mlsd = auto()
    binary = auto()
    standard_lineart = auto()
    lineart = auto()
    lineart_anime = auto()
    lineart_anime_denoise = auto()
    pidinet = auto()
    scribble_xdog = auto()
    scribble_pidinet = auto()
    teed = auto()
    pyracanny = auto()
    midas_depth = auto()
    zoe_depth = auto()
    depth_anything = auto()
    depth_anything_v2 = auto()
    normal_bae = auto()
    oneformer_ade20k = auto()
    oneformer_coco = auto()
    color = auto()
    shuffle = auto()
    recolor_luminance = auto()
    recolor_intensity = auto()
    tile = auto()
    tile_ttplanet_guided = auto()
    tile_ttplanet_simple = auto()


class KNOWN_IMAGE_SOURCE_PROCESSING(StrEnum):
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


class TI_TRIGGER_INJECT_CHOICE(StrEnum):
    """The TI trigger inject choices that are known to the API."""

    NO_INJECT = auto()
    """No injection - the model either does not require it or the user will add the trigger manually."""

    POSITIVE_PROMPT = auto()
    """Injects into the 'positive' prompt."""

    NEGATIVE_PROMPT = auto()
    """Injects into the 'negative' prompt."""


class LORA_TRIGGER_INJECT_CHOICE(StrEnum):
    """The LoRa trigger inject choices that are known to the API."""

    NO_INJECT = auto()
    """No injection - the model either does not require it or the user will add the trigger manually."""

    EXACT_POSITIVE = auto()
    """Injects the exact specified trigger term into the 'positive' prompt."""

    EXACT_NEGATIVE = auto()
    """Injects the exact specified trigger term into the 'negative' prompt."""

    FUZZY_POSITIVE = auto()
    """Attempt to match the specified trigger term to a published trigger term into the 'positive' prompt."""

    FUZZY_NEGATIVE = auto()
    """Attempt to match the specified trigger term to a published trigger term into the 'negative' prompt."""


class KNOWN_IMAGE_WORKFLOWS(StrEnum):
    """The controlnets that are known to the API."""

    qr_code = auto()


class CLIP_SKIP_REPRESENTATION(StrEnum):
    """The CLIP skip representations that are known."""

    NEGATIVE_OFFSET = auto()
    """CLIP skip is used with a negative offset.

    For example, -1 means "no skipped layers" and -2 means "skip the last layer". This is the case for comfyui.
    """

    POSITIVE_OFFSET = auto()
    """CLIP skip is used with a positive offset.

    For example, 1 means "skip no layers" and 2 means "skip the first layer". This is the case for many frontends.
    """
