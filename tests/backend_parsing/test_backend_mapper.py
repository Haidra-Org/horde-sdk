from horde_sdk.backend_parsing.image.comfyui.hordelib import (
    KNOWN_COMFYUI_CONTROLNETS,
    KNOWN_COMFYUI_IMAGE_SAMPLERS,
    KNOWN_COMFYUI_IMAGE_SCHEDULERS,
    ComfyUIBackendValuesMapper,
)
from horde_sdk.backend_parsing.object_models import ImageBackendValuesMapper
from horde_sdk.generation_parameters.image.consts import (
    KNOWN_IMAGE_CONTROLNETS,
    KNOWN_IMAGE_SAMPLERS,
    KNOWN_IMAGE_SCHEDULERS,
)


def test_comfyui_backend_values_mapper_init() -> None:
    """Test the ComfyUIBackendValuesMapper class."""
    mapper = ComfyUIBackendValuesMapper()
    assert isinstance(mapper, ImageBackendValuesMapper)


def test_comfyui_backend_values_mapper_accurate() -> None:
    """Test the ComfyUIBackendValuesMapper class."""
    mapper = ComfyUIBackendValuesMapper()
    assert isinstance(mapper._to_sdk_sampler_map, dict)
    assert isinstance(mapper._to_backend_sampler_map, dict)
    assert len(mapper._to_sdk_sampler_map) > 0
    assert len(mapper._to_backend_sampler_map) > 0

    for sdk_sampler_key, sdk_sampler_value in mapper._to_sdk_sampler_map.items():
        assert isinstance(sdk_sampler_key, str)
        assert isinstance(sdk_sampler_value, KNOWN_IMAGE_SAMPLERS)

    for backend_sampler_key, backend_sampler_value in mapper._to_backend_sampler_map.items():
        assert isinstance(backend_sampler_key, KNOWN_IMAGE_SAMPLERS)
        assert isinstance(backend_sampler_value, str)

    assert len(mapper._to_sdk_sampler_map) == len(mapper._to_backend_sampler_map)

    assert mapper.map_to_backend_sampler(KNOWN_IMAGE_SAMPLERS.k_lms) == KNOWN_COMFYUI_IMAGE_SAMPLERS.lms
    assert mapper.map_to_backend_sampler("k_lms") == KNOWN_COMFYUI_IMAGE_SAMPLERS.lms
    assert mapper.map_to_backend_sampler("lms") == "lms"
    assert mapper.map_to_backend_sampler("lms") == KNOWN_COMFYUI_IMAGE_SAMPLERS.lms

    assert mapper.map_to_backend_scheduler(KNOWN_IMAGE_SCHEDULERS.simple) == KNOWN_COMFYUI_IMAGE_SCHEDULERS.simple
    assert mapper.map_to_backend_scheduler("simple") == KNOWN_COMFYUI_IMAGE_SCHEDULERS.simple
    assert mapper.map_to_backend_scheduler("simple") == "simple"
    assert (
        mapper.map_to_backend_scheduler(KNOWN_COMFYUI_IMAGE_SCHEDULERS.simple) == KNOWN_COMFYUI_IMAGE_SCHEDULERS.simple
    )

    assert mapper.map_to_backend_controlnet(KNOWN_IMAGE_CONTROLNETS.canny) == KNOWN_COMFYUI_CONTROLNETS.canny
    assert mapper.map_to_backend_controlnet("canny") == KNOWN_COMFYUI_CONTROLNETS.canny

    assert mapper.map_to_sdk_sampler(KNOWN_COMFYUI_IMAGE_SAMPLERS.lms) == KNOWN_IMAGE_SAMPLERS.k_lms
    assert mapper.map_to_sdk_sampler("lms") == KNOWN_IMAGE_SAMPLERS.k_lms
    assert mapper.map_to_sdk_sampler("k_lms") == "k_lms"
    assert mapper.map_to_sdk_sampler(KNOWN_IMAGE_SAMPLERS.k_lms) == KNOWN_IMAGE_SAMPLERS.k_lms

    assert mapper.map_to_sdk_scheduler(KNOWN_COMFYUI_IMAGE_SCHEDULERS.simple) == KNOWN_IMAGE_SCHEDULERS.simple
    assert mapper.map_to_sdk_scheduler("simple") == KNOWN_IMAGE_SCHEDULERS.simple
    assert mapper.map_to_sdk_scheduler("simple") == "simple"
    assert mapper.map_to_sdk_scheduler(KNOWN_IMAGE_SCHEDULERS.simple) == KNOWN_IMAGE_SCHEDULERS.simple

    assert mapper.map_to_sdk_controlnet(KNOWN_COMFYUI_CONTROLNETS.canny) == KNOWN_IMAGE_CONTROLNETS.canny
    assert mapper.map_to_sdk_controlnet("canny") == KNOWN_IMAGE_CONTROLNETS.canny
    assert mapper.map_to_sdk_controlnet("canny") == "canny"
    assert mapper.map_to_sdk_controlnet(KNOWN_IMAGE_CONTROLNETS.canny) == "canny"
