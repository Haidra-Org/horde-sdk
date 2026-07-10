"""Tests for the source-image usability and txt2img fallback helpers."""

import base64
import binascii

import pytest
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateJobPopPayload,
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
)
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SOURCE_PROCESSING
from horde_sdk.worker.dispatch.ai_horde.image.convert import convert_image_job_pop_response_to_parameters
from horde_sdk.worker.dispatch.ai_horde.image.source_image import (
    SOURCE_IMAGE_REQUIRING_PROCESSING,
    job_requires_source_image_input,
    resolve_effective_source_processing,
)

# A base64-alphabet string with a length that cannot be validly padded; base64 decoding raises on it.
UNDECODABLE_SOURCE_IMAGE = "notvalidbase64"


def _make_pop_response(
    single_id: GenerationID,
    *,
    source_image: str | None,
    source_processing: str | KNOWN_IMAGE_SOURCE_PROCESSING,
    downloaded_source_image: str | None = None,
) -> ImageGenerateJobPopResponse:
    """Build a minimal pop response exercising only the source-image fields."""
    response = ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="42"),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=source_image,
        source_processing=source_processing,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )
    if downloaded_source_image is not None:
        response._downloaded_source_image = downloaded_source_image
    return response


def test_undecodable_source_image_constant_raises() -> None:
    """The unusable-source fixture must actually fail base64 decoding to be a valid negative case."""
    with pytest.raises(binascii.Error):
        base64.b64decode(UNDECODABLE_SOURCE_IMAGE)


def test_txt2img_passthrough(single_id: GenerationID) -> None:
    """A txt2img request needs no source latent regardless of source image."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.txt2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_img2img_without_source_falls_back(single_id: GenerationID) -> None:
    """An img2img request with no source image degrades to txt2img."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_img2img_with_usable_source_is_preserved(
    single_id: GenerationID,
    img2img_testing_image_base64: str,
) -> None:
    """An img2img request with a decodable source image keeps needing a source latent."""
    response = _make_pop_response(
        single_id,
        source_image=img2img_testing_image_base64,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.img2img
    assert job_requires_source_image_input(response) is True


def test_img2img_with_undecodable_source_falls_back(single_id: GenerationID) -> None:
    """An img2img request whose source image cannot be decoded degrades to txt2img."""
    response = _make_pop_response(
        single_id,
        source_image=UNDECODABLE_SOURCE_IMAGE,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_img2img_with_url_source_not_downloaded_falls_back(single_id: GenerationID) -> None:
    """A URL source image that was never downloaded is unusable and degrades to txt2img."""
    response = _make_pop_response(
        single_id,
        source_image="https://not.a.real.url.internal/source.webp",
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_img2img_with_url_source_downloaded_is_preserved(
    single_id: GenerationID,
    img2img_testing_image_base64: str,
) -> None:
    """A URL source image with a completed download is usable and keeps needing a source latent."""
    response = _make_pop_response(
        single_id,
        source_image="https://not.a.real.url.internal/source.webp",
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
        downloaded_source_image=img2img_testing_image_base64,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.img2img
    assert job_requires_source_image_input(response) is True


def test_empty_string_source_image_is_usable(single_id: GenerationID) -> None:
    """An empty-string source image decodes to empty bytes and is treated as usable (no fallback).

    This preserves the converter's existing behavior, where an empty string yields non-None bytes.
    """
    response = _make_pop_response(
        single_id,
        source_image="",
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.img2img
    assert job_requires_source_image_input(response) is True


def test_inpainting_without_source_falls_back(single_id: GenerationID) -> None:
    """An inpainting request with no source image degrades to txt2img."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_outpainting_shares_inpainting_membership(single_id: GenerationID) -> None:
    """`outpainting` aliases `inpainting`; both are source-requiring and fall back without a source."""
    assert KNOWN_IMAGE_SOURCE_PROCESSING.outpainting in SOURCE_IMAGE_REQUIRING_PROCESSING
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_remix_without_source_falls_back(single_id: GenerationID) -> None:
    """A remix request with no source image degrades to txt2img."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.remix,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    assert job_requires_source_image_input(response) is False


def test_remix_with_usable_source_is_preserved(
    single_id: GenerationID,
    img2img_testing_image_base64: str,
) -> None:
    """A remix request with a decodable source image keeps needing a source latent."""
    response = _make_pop_response(
        single_id,
        source_image=img2img_testing_image_base64,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.remix,
    )
    assert resolve_effective_source_processing(response) == KNOWN_IMAGE_SOURCE_PROCESSING.remix
    assert job_requires_source_image_input(response) is True


def test_unknown_source_processing_passthrough(single_id: GenerationID) -> None:
    """An unknown source-processing string is returned unchanged and needs no source latent."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing="some_future_mode",
    )
    assert resolve_effective_source_processing(response) == "some_future_mode"
    assert job_requires_source_image_input(response) is False


def test_converter_fallback_agrees_with_helper(
    single_id: GenerationID,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """The converter's produced source_processing must match the helper's effective verdict."""
    response = _make_pop_response(
        single_id,
        source_image=None,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )

    conversion_result = convert_image_job_pop_response_to_parameters(
        api_response=response,
        model_reference_manager=model_reference_manager,
    )

    assert (
        conversion_result.generation_parameters.source_processing
        == resolve_effective_source_processing(response)
        == KNOWN_IMAGE_SOURCE_PROCESSING.txt2img
    )


def test_converter_preserves_usable_source_agrees_with_helper(
    single_id: GenerationID,
    img2img_testing_image_base64: str,
    model_reference_manager: ModelReferenceManager,
) -> None:
    """A usable img2img source is preserved by the converter and matches the helper's verdict."""
    response = _make_pop_response(
        single_id,
        source_image=img2img_testing_image_base64,
        source_processing=KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
    )

    conversion_result = convert_image_job_pop_response_to_parameters(
        api_response=response,
        model_reference_manager=model_reference_manager,
    )

    assert (
        conversion_result.generation_parameters.source_processing
        == resolve_effective_source_processing(response)
        == KNOWN_IMAGE_SOURCE_PROCESSING.img2img
    )
