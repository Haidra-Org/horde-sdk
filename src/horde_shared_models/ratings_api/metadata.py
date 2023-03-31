"""Request metadata specific to the Ratings API."""
from ..generic_api import GenericPathData


class RatingsAPIPathData(GenericPathData):
    """Data that is exclusively passed as part of a URL path, and not after the '?' (query)."""

    user_id = "user_id"
    image_id = "image_id"
