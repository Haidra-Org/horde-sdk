"""Lockstep checks between the API sampler enum and the ComfyUI backend mapping."""

from horde_sdk.backend_parsing.image.comfyui.hordelib import (
    KNOWN_COMFYUI_IMAGE_SAMPLERS,
    ComfyUIBackendValuesMapper,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS

# Solvers the API accepts that the ComfyUI mapping deliberately does not name. `dpmsolver` is a
# diffusers-era name the backend renders with another solver, and `plms` never reached this enum.
_UNMAPPED_API_SAMPLERS = {"dpmsolver"}


def test_convert_map_targets_are_all_real_api_samplers() -> None:
    """A mapping onto a sampler the API does not accept could never be requested."""
    mapper = ComfyUIBackendValuesMapper()
    api_values = {member.value for member in KNOWN_IMAGE_SAMPLERS}

    for backend_name, api_sampler in mapper._COMFYUI_SAMPLERS_CONVERT_MAP.items():
        assert api_sampler.value in api_values, f"{backend_name} maps onto unknown API sampler {api_sampler}"


def test_convert_map_sources_are_all_real_backend_samplers() -> None:
    """A mapping from a backend name the backend does not offer is dead weight."""
    mapper = ComfyUIBackendValuesMapper()
    backend_values = {member.value for member in KNOWN_COMFYUI_IMAGE_SAMPLERS}

    for backend_name in mapper._COMFYUI_SAMPLERS_CONVERT_MAP:
        assert backend_name.value in backend_values, f"{backend_name} is not a known backend sampler"


def test_every_api_sampler_is_mapped_or_explicitly_exempt() -> None:
    """An unmapped API sampler cannot be recovered from a backend response."""
    mapper = ComfyUIBackendValuesMapper()
    mapped = {api_sampler.value for api_sampler in mapper._COMFYUI_SAMPLERS_CONVERT_MAP.values()}
    api_values = {member.value for member in KNOWN_IMAGE_SAMPLERS}

    assert api_values - mapped == _UNMAPPED_API_SAMPLERS


def test_extended_solvers_share_their_backend_spelling() -> None:
    """The extended solvers were named after the backend, so both sides must agree letter for letter."""
    for name in (
        "uni_pc",
        "uni_pc_bh2",
        "dpmpp_2m_sde",
        "dpmpp_3m_sde",
        "ddpm",
        "deis",
        "ipndm",
        "res_multistep",
        "gradient_estimation",
        "heunpp2",
        "er_sde",
        "sa_solver",
        "euler_cfg_pp",
        "euler_ancestral_cfg_pp",
        "exp_heun_2_x0",
        "exp_heun_2_x0_sde",
        "dpmpp_2s_ancestral_cfg_pp",
        "dpmpp_2m_cfg_pp",
        "dpmpp_2m_sde_heun",
        "ipndm_v",
        "res_multistep_cfg_pp",
        "res_multistep_ancestral",
        "res_multistep_ancestral_cfg_pp",
        "gradient_estimation_cfg_pp",
        "seeds_2",
        "seeds_3",
        "sa_solver_pece",
    ):
        assert KNOWN_IMAGE_SAMPLERS(name).value == KNOWN_COMFYUI_IMAGE_SAMPLERS(name).value


def test_backend_sampler_vocabulary_matches_the_pinned_backend() -> None:
    """The backend enum is a copy of a list that lives in another repo, so drift has to be caught here.

    The set below is `comfy.samplers.SAMPLER_NAMES` at the pinned ComfyUI revision fb991e2c.
    """
    pinned_backend_samplers = {
        "euler",
        "euler_cfg_pp",
        "euler_ancestral",
        "euler_ancestral_cfg_pp",
        "heun",
        "heunpp2",
        "exp_heun_2_x0",
        "exp_heun_2_x0_sde",
        "dpm_2",
        "dpm_2_ancestral",
        "lms",
        "dpm_fast",
        "dpm_adaptive",
        "dpmpp_2s_ancestral",
        "dpmpp_2s_ancestral_cfg_pp",
        "dpmpp_sde",
        "dpmpp_sde_gpu",
        "dpmpp_2m",
        "dpmpp_2m_cfg_pp",
        "dpmpp_2m_sde",
        "dpmpp_2m_sde_gpu",
        "dpmpp_2m_sde_heun",
        "dpmpp_2m_sde_heun_gpu",
        "dpmpp_3m_sde",
        "dpmpp_3m_sde_gpu",
        "ddpm",
        "lcm",
        "ipndm",
        "ipndm_v",
        "deis",
        "res_multistep",
        "res_multistep_cfg_pp",
        "res_multistep_ancestral",
        "res_multistep_ancestral_cfg_pp",
        "gradient_estimation",
        "gradient_estimation_cfg_pp",
        "er_sde",
        "seeds_2",
        "seeds_3",
        "sa_solver",
        "sa_solver_pece",
        "ddim",
        "uni_pc",
        "uni_pc_bh2",
    }

    assert {member.value for member in KNOWN_COMFYUI_IMAGE_SAMPLERS} == pinned_backend_samplers


def test_only_the_device_variants_are_left_unmapped() -> None:
    """The `_gpu` names differ only in where noise is drawn, which is the worker's choice, not the caller's."""
    mapper = ComfyUIBackendValuesMapper()
    unmapped = {member.value for member in KNOWN_COMFYUI_IMAGE_SAMPLERS} - {
        str(backend_name) for backend_name in mapper._COMFYUI_SAMPLERS_CONVERT_MAP
    }

    assert unmapped == {
        "dpmpp_sde_gpu",
        "dpmpp_2m_sde_gpu",
        "dpmpp_2m_sde_heun_gpu",
        "dpmpp_3m_sde_gpu",
    }


def test_classic_samplers_keep_their_translated_names() -> None:
    """The `k_` block is translated rather than shared, and must not drift into identity mapping."""
    mapper = ComfyUIBackendValuesMapper()
    convert_map = mapper._COMFYUI_SAMPLERS_CONVERT_MAP

    assert convert_map[KNOWN_COMFYUI_IMAGE_SAMPLERS.euler] == KNOWN_IMAGE_SAMPLERS.k_euler
    assert convert_map[KNOWN_COMFYUI_IMAGE_SAMPLERS.euler_ancestral] == KNOWN_IMAGE_SAMPLERS.k_euler_a
    assert convert_map[KNOWN_COMFYUI_IMAGE_SAMPLERS.ddim] == KNOWN_IMAGE_SAMPLERS.DDIM
