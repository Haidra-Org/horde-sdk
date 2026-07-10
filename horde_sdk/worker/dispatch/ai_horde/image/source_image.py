"""Source-image usability and txt2img fallback decisions for image job pop responses.

This module is the single authority for the question "does this job need a source latent?".
Both the image parameter converter and external routing consumers derive their answer here so
the fallback semantics cannot drift between them. It is intentionally free of heavy dependencies
(no torch, no imaging libraries) so it can run in torch-free orchestration processes.
"""

import base64
from urllib.parse import urlparse

from horde_sdk.ai_horde_api.apimodels.generate.pop import ImageGenerateJobPopResponse
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SOURCE_PROCESSING

SOURCE_IMAGE_REQUIRING_PROCESSING: frozenset[KNOWN_IMAGE_SOURCE_PROCESSING] = frozenset(
    {
        KNOWN_IMAGE_SOURCE_PROCESSING.img2img,
        KNOWN_IMAGE_SOURCE_PROCESSING.inpainting,
        KNOWN_IMAGE_SOURCE_PROCESSING.outpainting,
        KNOWN_IMAGE_SOURCE_PROCESSING.remix,
    },
)
"""The source-processing modes whose generation consumes a source latent.

A pop response requesting any of these modes degrades to txt2img when it carries no usable
source image. `outpainting` shares a value with `inpainting`, so both collapse to a single member.
"""


def _is_url(value: str) -> bool:
    """Check whether the value is an HTTP(S) URL rather than inline base64 data."""
    return urlparse(value).scheme in ("http", "https")


def _source_image_is_usable(api_response: ImageGenerateJobPopResponse) -> bool:
    """Whether the response's primary source image resolves and decodes to bytes.

    A source image is usable when it is present as inline base64 (or a URL whose download has
    already been performed) and that base64 decodes without raising. This mirrors the converter's
    resolve-then-decode determination while remaining side-effect-free: it neither logs nor records
    faults, so it can be called for a routing decision without disturbing observable behavior.
    """
    field_value = api_response.source_image
    if field_value is None:
        return False

    if _is_url(field_value):
        field_value = api_response.get_downloaded_source_image()
        if field_value is None:
            return False

    try:
        base64.b64decode(field_value)
    except Exception:
        return False

    return True


def resolve_effective_source_processing(
    api_response: ImageGenerateJobPopResponse,
) -> str | KNOWN_IMAGE_SOURCE_PROCESSING:
    """Return the source-processing mode after the converter's unusable-source txt2img fallback.

    A request for a source-requiring mode (img2img, inpainting/outpainting, remix) with no usable
    source image degrades to txt2img. Any other mode, including unknown strings, is returned
    unchanged.
    """
    source_processing = api_response.source_processing

    if source_processing in SOURCE_IMAGE_REQUIRING_PROCESSING and not _source_image_is_usable(api_response):
        return KNOWN_IMAGE_SOURCE_PROCESSING.txt2img

    return source_processing


def job_requires_source_image_input(api_response: ImageGenerateJobPopResponse) -> bool:
    """Whether the job, after fallback, still needs a source latent.

    This is the routing predicate for consumers that must decide from a raw pop response, before
    conversion, whether the job will run as an img2img-family or remix generation. It is True only
    when the effective (post-fallback) source-processing consumes a source latent.
    """
    return resolve_effective_source_processing(api_response) in SOURCE_IMAGE_REQUIRING_PROCESSING
