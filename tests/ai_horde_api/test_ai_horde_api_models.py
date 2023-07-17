"""Unit tests for AI-Horde API models."""
from horde_sdk.ai_horde_api.apimodels.generate._async import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)
from horde_sdk.ai_horde_api.consts import KNOWN_SAMPLERS, KNOWN_SOURCE_PROCESSING
from horde_sdk.generic_api.consts import ANON_API_KEY


def test_api_endpoint() -> None:
    ImageGenerateAsyncRequest.get_api_url()
    ImageGenerateAsyncRequest.get_endpoint_subpath()
    ImageGenerateAsyncRequest.get_endpoint_url()


def test_ImageGenerateAsyncRequest() -> None:
    test_async_request = ImageGenerateAsyncRequest(
        apikey=ANON_API_KEY,
        models=["Deliberate"],
        prompt="test prompt",
        params=ImageGenerationInputPayload(
            sampler_name=KNOWN_SAMPLERS.k_lms,
            cfg_scale=7.5,
            denoising_strength=1,
            seed=None,
            height=512,
            width=512,
            seed_variation=None,
            post_processing=[],
            karras=True,
            tiling=False,
            hires_fix=False,
            clip_skip=1,
            control_type=None,
            image_is_control=None,
            return_control_map=None,
            facefixer_strength=None,
            loras=[],
            special={},
            steps=25,
            n_iter=1,
            use_nsfw_censor=False,
        ),
        nsfw=True,
        trusted_workers=False,
        slow_workers=False,
        workers=[],
        censor_nsfw=False,
        source_image="test source image (usually base64)",
        source_processing=KNOWN_SOURCE_PROCESSING.txt2img,
        source_mask="test source mask (usually base64)",
        r2=True,
        shared=False,
        replacement_filter=True,
        dry_run=False,
    )
    assert test_async_request.apikey == ANON_API_KEY
    assert test_async_request.models == ["Deliberate"]
    assert test_async_request.prompt == "test prompt"
    assert test_async_request.params is not None
    assert test_async_request.params.sampler_name == "k_lms"
    assert test_async_request.params.cfg_scale == 7.5
    assert test_async_request.params.denoising_strength == 1
    assert test_async_request.params.seed is not None
    assert test_async_request.params.seed.isdigit()
    assert test_async_request.params.height == 512
    assert test_async_request.params.width == 512
    assert test_async_request.params.seed_variation is None
    assert test_async_request.params.post_processing == []
    assert test_async_request.params.karras is True
    assert test_async_request.params.tiling is False
    assert test_async_request.params.hires_fix is False
    assert test_async_request.params.clip_skip == 1
    assert test_async_request.params.control_type is None
    assert test_async_request.params.image_is_control is None
    assert test_async_request.params.return_control_map is None
    assert test_async_request.params.facefixer_strength is None
    assert test_async_request.params.loras == []
    assert test_async_request.params.special == {}
    assert test_async_request.params.steps == 25
    assert test_async_request.params.n_iter == 1
    assert test_async_request.params.use_nsfw_censor is False
    assert test_async_request.nsfw is True
    assert test_async_request.trusted_workers is False
    assert test_async_request.slow_workers is False
    assert test_async_request.workers == []
    assert test_async_request.censor_nsfw is False
    assert test_async_request.source_image == "test source image (usually base64)"
    assert test_async_request.source_processing == KNOWN_SOURCE_PROCESSING.txt2img
    assert test_async_request.source_mask == "test source mask (usually base64)"
    assert test_async_request.r2 is True
    assert test_async_request.shared is False
    assert test_async_request.replacement_filter is True
    assert test_async_request.dry_run is False
