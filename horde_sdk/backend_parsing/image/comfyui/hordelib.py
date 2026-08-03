from enum import auto
from typing import ClassVar

from strenum import StrEnum

from horde_sdk.backend_parsing.object_models import ImageBackendValuesMapper
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
)


class KNOWN_COMFYUI_IMAGE_SAMPLERS(StrEnum):
    """The samplers that are known to the API.

    (k_lms, k_heun, DDIM, etc)

    This mirrors ComfyUI's own sampler list and is not exhaustive of it: the `exp_heun_2_x0*`,
    `dpmpp_2m_sde_heun*`, `gradient_estimation_cfg_pp`, `seeds_2`, `seeds_3` and `sa_solver_pece`
    names ComfyUI also offers have no horde counterpart and are not listed here.
    """

    euler = auto()
    euler_cfg_pp = auto()
    euler_ancestral = auto()
    euler_ancestral_cfg_pp = auto()
    heun = auto()
    heunpp2 = auto()
    dpm_2 = auto()
    dpm_2_ancestral = auto()
    lms = auto()
    dpm_fast = auto()
    dpm_adaptive = auto()
    dpmpp_2s_ancestral = auto()
    dpmpp_2s_ancestral_cfg_pp = auto()
    dpmpp_sde = auto()
    dpmpp_sde_gpu = auto()
    dpmpp_2m = auto()
    dpmpp_2m_cfg_pp = auto()
    dpmpp_2m_sde = auto()
    dpmpp_2m_sde_gpu = auto()
    dpmpp_3m_sde = auto()
    dpmpp_3m_sde_gpu = auto()
    ddpm = auto()
    lcm = auto()
    ipndm = auto()
    ipndm_v = auto()
    deis = auto()
    res_multistep = auto()
    res_multistep_cfg_pp = auto()
    res_multistep_ancestral = auto()
    res_multistep_ancestral_cfg_pp = auto()
    gradient_estimation = auto()
    er_sde = auto()
    sa_solver = auto()

    ddim = auto()
    uni_pc = auto()
    uni_pc_bh2 = auto()


KNOWN_COMFYUI_IMAGE_SCHEDULERS = KNOWN_IMAGE_SCHEDULERS
KNOWN_COMFYUI_CONTROLNETS = KNOWN_IMAGE_CONTROLNETS


class ComfyUIBackendValuesMapper(
    ImageBackendValuesMapper[
        KNOWN_COMFYUI_IMAGE_SAMPLERS,
        KNOWN_COMFYUI_IMAGE_SCHEDULERS,
        KNOWN_COMFYUI_CONTROLNETS,
    ],
):
    """Mapper for ComfyUI backend values."""

    _COMFYUI_SAMPLERS_CONVERT_MAP: ClassVar[dict[KNOWN_COMFYUI_IMAGE_SAMPLERS | str, KNOWN_IMAGE_SAMPLERS]] = {
        KNOWN_COMFYUI_IMAGE_SAMPLERS.euler: KNOWN_IMAGE_SAMPLERS.k_euler,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.euler_ancestral: KNOWN_IMAGE_SAMPLERS.k_euler_a,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.heun: KNOWN_IMAGE_SAMPLERS.k_heun,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpm_2: KNOWN_IMAGE_SAMPLERS.k_dpm_2,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpm_2_ancestral: KNOWN_IMAGE_SAMPLERS.k_dpm_2_a,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.lms: KNOWN_IMAGE_SAMPLERS.k_lms,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpm_fast: KNOWN_IMAGE_SAMPLERS.k_dpm_fast,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpm_adaptive: KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpmpp_2s_ancestral: KNOWN_IMAGE_SAMPLERS.k_dpmpp_2s_a,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpmpp_sde: KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpmpp_2m: KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.ddim: KNOWN_IMAGE_SAMPLERS.DDIM,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.lcm: KNOWN_IMAGE_SAMPLERS.lcm,
        # The extended solvers are spelled identically on both sides, so these pairs are identity
        # mappings. They are listed anyway because the mapper converts by lookup, not by name equality.
        KNOWN_COMFYUI_IMAGE_SAMPLERS.uni_pc: KNOWN_IMAGE_SAMPLERS.uni_pc,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.uni_pc_bh2: KNOWN_IMAGE_SAMPLERS.uni_pc_bh2,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpmpp_2m_sde: KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.dpmpp_3m_sde: KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.ddpm: KNOWN_IMAGE_SAMPLERS.ddpm,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.deis: KNOWN_IMAGE_SAMPLERS.deis,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.ipndm: KNOWN_IMAGE_SAMPLERS.ipndm,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.res_multistep: KNOWN_IMAGE_SAMPLERS.res_multistep,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.gradient_estimation: KNOWN_IMAGE_SAMPLERS.gradient_estimation,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.heunpp2: KNOWN_IMAGE_SAMPLERS.heunpp2,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.er_sde: KNOWN_IMAGE_SAMPLERS.er_sde,
        KNOWN_COMFYUI_IMAGE_SAMPLERS.sa_solver: KNOWN_IMAGE_SAMPLERS.sa_solver,
    }

    # ComfyUI names its schedules exactly as the API does, so these pairs are identity mappings. They
    # are declared rather than inferred because the mapper converts by lookup, and an absent entry is
    # an unmappable value rather than a pass-through.
    _COMFYUI_SCHEDULERS_CONVERT_MAP: ClassVar[dict[KNOWN_COMFYUI_IMAGE_SCHEDULERS | str, KNOWN_IMAGE_SCHEDULERS]] = {
        schedule: schedule for schedule in KNOWN_IMAGE_SCHEDULERS
    }

    def __init__(self) -> None:
        """Initialize the ComfyUI backend values mapper."""
        super().__init__(
            backend_samplers_type=KNOWN_COMFYUI_IMAGE_SAMPLERS,
            backend_schedulers_type=KNOWN_COMFYUI_IMAGE_SCHEDULERS,
            backend_controlnets_type=KNOWN_COMFYUI_CONTROLNETS,
            sdk_samplers_map=self._COMFYUI_SAMPLERS_CONVERT_MAP,
            sdk_schedulers_map=self._COMFYUI_SCHEDULERS_CONVERT_MAP,
            sdk_controlnets_map={},
        )
