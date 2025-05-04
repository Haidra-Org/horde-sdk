import base64
import io

import PIL.Image
from horde_model_reference.meta_consts import (
    KNOWN_IMAGE_GENERATION_BASELINE,
)
from loguru import logger

IMAGE_CHUNK_SIZE = 64
"""The chunk size used for image processing. Images must be divisible by this value.

Note that, at the time of writing, 64 is the de-facto standard value for all image models.
"""
DEFAULT_IMAGE_MIN_RESOLUTION = 512
"""The default minimum resolution of the shortest dimension to use for the first pass."""
DEFAULT_HIGHER_RES_MAX_RESOLUTION = 1024
"""The default maximum resolution of the shortest dimension to use for the second pass."""

IDEAL_SDXL_RESOLUTIONS = [
    (1024, 1024),
    (1152, 896),
    (896, 1152),
    (1216, 832),
    (832, 1216),
    (1344, 768),
    (768, 1344),
    (1536, 640),
    (640, 1536),
]
"""The Stability.AI recommended resolutions for SDXL generation."""

IDEAL_SDXL_RESOLUTIONS_ASPECT_RATIOS = [width / height for width, height in IDEAL_SDXL_RESOLUTIONS]
"""The aspect ratios of the Stability.AI recommended resolutions for SDXL generation."""

MIN_DENOISING_STRENGTH = 0.01
"""The minimum denoising strength to use for the upscale sampler"""
MAX_DENOISING_STRENGTH = 1.0
"""The maximum denoising strength to use for the upscale sampler"""
DECAY_RATE = 2
"""The rate at which the upscale steps decay based on the denoising strength"""
MIN_STEPS = 3
"""The minimum number of steps to use for the upscaling sampler"""
UPSCALE_ADJUSTMENT_FACTOR = 0.5
"""The factor by which the upscale steps are adjusted based on the native resolution distance factor"""
UPSCALE_DIVISOR = 2.25
"""The divisor used to adjust the upscale steps based on the native resolution distance factor"""

STANDARD_RESOLUTION = 512
"""The standard resolution used for the resolution penalty calculation"""
RESOLUTION_PENALTY_MULTIPLIER = 3
"""The multiplier used for the resolution penalty calculation"""

STEP_FLOOR_THRESHOLD = 18
"""The threshold at which the upscale steps are adjusted to the ddim steps"""


def resize_image_dimensions(
    width: int,
    height: int,
    desired_dimension: int,
    use_min: bool,
    *,
    image_chunk_size: int = IMAGE_CHUNK_SIZE,
) -> tuple[int, int]:
    """Resize the image dimensions to have one side equal to the desired resolution, keeping the aspect ratio.

    - If use_min is True, the side with the minimum length will be resized to the desired resolution.
        - For example, if the image is 1024x2048 and the desired resolution is 512, the image will be
        resized to 512x1024. (As desired for 512x trained models)
    - If use_min is False, the side with the maximum length will be resized to the desired resolution.
        - For example, if the image is 1024x2048 and the desired resolution is 1024, the image will be
        resized to 512x1024. (As desired for 1024x trained models)
    - If the image is smaller than the desired resolution, the image will not be resized.

    Args:
        width (int): The width of the image.
        height (int): The height of the image.
        desired_dimension (int): The desired single side resolution.
        use_min (bool): Whether to use the minimum or maximum side.
        image_chunk_size (int): The chunk size used for image processing. Images must be divisible by this value. \
            Defaults to 64, which is the de-facto standard value for all image models at the time of writing. \
            This only should be changed if you are certain that the model you are using requires a different value.

    Returns:
        tuple[int, int]: The target first pass width and height of the image.
    """
    if desired_dimension is None or desired_dimension <= 0:
        raise ValueError("desired_resolution must be a positive integer.")

    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integers.")

    if width < desired_dimension and height < desired_dimension:
        return width, height

    if use_min:
        ratio = min(
            height / desired_dimension,
            width / desired_dimension,
        )
    else:
        ratio = max(
            height / desired_dimension,
            width / desired_dimension,
        )

    new_width = int(width // (ratio * image_chunk_size)) * image_chunk_size
    new_height = int(height // (ratio * image_chunk_size)) * image_chunk_size

    return new_width, new_height


def get_first_pass_image_resolution_min(
    width: int,
    height: int,
    min_dimension: int = DEFAULT_IMAGE_MIN_RESOLUTION,
) -> tuple[int, int]:
    """Resize the image dimensions to have one side equal to the desired resolution, keeping the aspect ratio.

    - If the image is larger than the desired resolution, the side with the minimum length will be resized to the
        desired resolution.
    - If the image is smaller than the desired resolution, the image will not be resized.

    """
    if width > min_dimension and height > min_dimension:
        return resize_image_dimensions(
            width,
            height,
            desired_dimension=min_dimension,
            use_min=True,
        )
    return width, height


def get_first_pass_image_resolution_max(
    width: int,
    height: int,
    max_dimension: int = DEFAULT_HIGHER_RES_MAX_RESOLUTION,
) -> tuple[int, int]:
    """Resize the image dimensions to have one side equal to the desired resolution, keeping the aspect ratio.

    - If the image is larger than the desired resolution, the side with the maximum length will be resized to the
        desired resolution.
    - If the image is smaller than the desired resolution, the image will not be resized.
    """
    if max(width, height) > max_dimension:
        return resize_image_dimensions(
            width,
            height,
            desired_dimension=max_dimension,
            use_min=False,
        )
    return width, height


def get_first_pass_image_resolution_sdxl(
    width: int,
    height: int,
) -> tuple[int, int]:
    """Resize the image to fit the SDXL resolution bucket which most closely matches the aspect ratio."""
    aspect_ratio = width / height
    closest_aspect_ratio = min(
        IDEAL_SDXL_RESOLUTIONS_ASPECT_RATIOS,
        key=lambda x: abs(aspect_ratio - x),
    )

    index = IDEAL_SDXL_RESOLUTIONS_ASPECT_RATIOS.index(closest_aspect_ratio)
    return IDEAL_SDXL_RESOLUTIONS[index]


def get_first_pass_image_resolution_by_baseline(
    width: int,
    height: int,
    baseline: KNOWN_IMAGE_GENERATION_BASELINE | None,
) -> tuple[int, int]:
    """Get the first pass image resolution based on the baseline category."""
    if baseline == KNOWN_IMAGE_GENERATION_BASELINE.stable_cascade:
        return get_first_pass_image_resolution_max(width, height)
    if baseline == KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl:
        return get_first_pass_image_resolution_sdxl(width, height)

    return get_first_pass_image_resolution_min(width, height)


def calc_upscale_sampler_steps(
    model_native_resolution: int | None,
    width: int,
    height: int,
    hires_fix_denoising_strength: float,
    ddim_steps: int,
    *,
    resolution_penalty_multiplier: float = RESOLUTION_PENALTY_MULTIPLIER,
    standard_resolution: int = STANDARD_RESOLUTION,
    min_denoising_strength: float = MIN_DENOISING_STRENGTH,
    max_denoising_strength: float = MAX_DENOISING_STRENGTH,
    min_steps: int = MIN_STEPS,
    decay_rate: int = DECAY_RATE,
    upscale_adjustment_factor: float = UPSCALE_ADJUSTMENT_FACTOR,
    upscale_divisor: float = UPSCALE_DIVISOR,
    step_floor_threshold: int = STEP_FLOOR_THRESHOLD,
) -> int:
    """Calculate the number of upscale steps to use for the upscale sampler based on the input parameters.

    Note: The resulting values are non-linear to the input values. The heuristic is based on the native resolution
    of the model, the requested resolution, the denoising strength and the number of steps used for the ddim
    sampler.

    Practically speaking, the resulting number of steps should be roughly the number of step required
    for most models to converge to a good result. Generally, doing more second pass steps than the value
    returned by this function is wasted effort.

    Args:
        model_native_resolution (int): The native resolution of the model to use for the generation. \
            This is the single side resolution (e.g. 512 for a 512x512 model). \
            Note that if this is unspecified (None), the upscale steps will not be adjusted based on the native \
            which will lead to suboptimal results, especially for models which work best at high resolutions.
        width (int): The width of the image to generate.
        height (int): The height of the image to generate.
        hires_fix_denoising_strength (float): The denoising strength to use for the upscale sampler.
        ddim_steps (int): The number of steps used for the sampler.
        resolution_penalty_multiplier (float): The multiplier used for the resolution penalty calculation.
        standard_resolution (int): The standard resolution used for the resolution penalty calculation.
        min_denoising_strength (float): The minimum denoising strength to use for the upscale sampler.
        max_denoising_strength (float): The maximum denoising strength to use for the upscale sampler.
        min_steps (int): The minimum number of steps to use for the upscaling sampler.
        decay_rate (int): The rate at which the upscale steps decay based on the denoising strength.
        upscale_adjustment_factor (float): The factor by which the upscale steps are adjusted based on the native \
            resolution distance factor.
        upscale_divisor (float): The divisor used to adjust the upscale steps based on the native resolution \
            distance factor.
        step_floor_threshold (int): The threshold at which the upscale steps are adjusted to the ddim steps.

    Returns:
        int: The number of upscale steps to use for the upscale sampler.
    """
    native_resolution_distance_factor: float = 0

    if model_native_resolution is not None:
        native_resolution_pixels = model_native_resolution * model_native_resolution

        requested_pixels = width * height
        native_resolution_distance_factor = requested_pixels / native_resolution_pixels

        resolution_penalty = resolution_penalty_multiplier * (standard_resolution / model_native_resolution)
        native_resolution_distance_factor /= resolution_penalty

    hires_fix_denoising_strength = max(
        min_denoising_strength,
        min(max_denoising_strength, hires_fix_denoising_strength),
    )

    scale = ddim_steps - min_steps
    upscale_steps = round(min_steps + scale * (hires_fix_denoising_strength**decay_rate))

    # if native_resolution_distance_factor > NATIVE_RESOLUTION_THRESHOLD:
    upscale_steps = round(
        upscale_steps * ((1 / (upscale_adjustment_factor**native_resolution_distance_factor)) / upscale_divisor),
    )

    logger.trace(f"Upscale steps calculated as {upscale_steps}")

    if ddim_steps <= step_floor_threshold:
        logger.debug(f"Upscale steps increased by {min_steps} due to low requested ddim steps")
        upscale_steps += min_steps

    if upscale_steps > ddim_steps:
        logger.debug(f"Upscale steps adjusted to {ddim_steps} from {upscale_steps}")
        upscale_steps = ddim_steps

    step_floor = min(6, ddim_steps)
    if step_floor > upscale_steps:
        logger.debug(f"Upscale steps adjusted to {step_floor} from {upscale_steps}")
        upscale_steps = step_floor

    return upscale_steps


def base64_str_to_pil_image(
    base64_str: str,
    *,
    except_on_parse_fail: bool = False,
) -> PIL.Image.Image | None:
    """Convert a base64 string to a PIL image.

    Args:
        base64_str (str): The base64 string to convert to a PIL image.
        except_on_parse_fail (bool): Whether to raise an exception if the base64 string cannot be parsed. \
            Defaults to False.

    Returns:
        PIL.Image.Image: The PIL image.
    """
    try:
        image_bytes = base64.b64decode(base64_str)
        return PIL.Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        if except_on_parse_fail:
            raise e
        logger.error(f"({type(e)}) Failed to parse base64 image: {e}")
        return None


def bytes_to_pil_image(
    image_bytes: bytes,
    *,
    except_on_parse_fail: bool = False,
) -> PIL.Image.Image | None:
    """Convert bytes to a PIL image.

    Args:
        image_bytes (bytes): The bytes to convert to a PIL image.
        except_on_parse_fail (bool): Whether to raise an exception if the bytes cannot be parsed. \
            Defaults to False.

    Returns:
        PIL.Image.Image: The PIL image.
    """
    try:
        return PIL.Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        if except_on_parse_fail:
            raise e
        logger.error(f"({type(e)}) Failed to parse image bytes: {e}")
        return None


def base64_str_to_bytes(
    base64_str: str,
    *,
    except_on_parse_fail: bool = False,
) -> bytes | None:
    """Convert a base64 string to bytes.

    Args:
        base64_str (str): The base64 string to convert to bytes.
        except_on_parse_fail (bool): Whether to raise an exception if the base64 string cannot be parsed. \
            Defaults to False.

    Returns:
        bytes: The bytes.
    """
    try:
        return base64.b64decode(base64_str)
    except Exception as e:
        if except_on_parse_fail:
            raise e
        logger.error(f"({type(e)}) Failed to parse base64 image: {e}")
        return None
