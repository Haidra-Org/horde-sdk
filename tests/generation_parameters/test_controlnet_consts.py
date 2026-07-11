"""Lockstep checks between the image-generation and annotation control-type enums."""

from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ANNOTATION_CONTROL_TYPES
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_CONTROLNETS


def test_image_controlnets_cover_all_annotation_control_types() -> None:
    """Every annotation control type must be requestable as an image-generation control_type."""
    annotation_values = {member.value for member in KNOWN_ANNOTATION_CONTROL_TYPES}
    image_values = {member.value for member in KNOWN_IMAGE_CONTROLNETS}

    assert annotation_values <= image_values


def test_image_controlnets_add_only_the_hough_alias() -> None:
    """The image enum is exactly the annotation set plus the legacy `hough` spelling of `mlsd`."""
    annotation_values = {member.value for member in KNOWN_ANNOTATION_CONTROL_TYPES}
    image_values = {member.value for member in KNOWN_IMAGE_CONTROLNETS}

    assert image_values - annotation_values == {"hough"}
    assert KNOWN_IMAGE_CONTROLNETS.mlsd.value in image_values
