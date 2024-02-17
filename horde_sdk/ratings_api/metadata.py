"""Request metadata specific to the Ratings API."""

from enum import auto

from horde_sdk.generic_api.metadata import GenericPathFields, GenericQueryFields


class RatingsAPIPathFields(GenericPathFields):
    """Data that is exclusively passed as part of a URL path, and not after the '?' (query)."""

    user_id = auto()
    image_id = auto()
    dataset_id = auto()
    filename = auto()


class RatingsAPIQueryFields(GenericQueryFields):
    """Data that is exclusively passed as part of a URL query, and not before the '?' (path)."""

    rating = auto()
    rating_comparison = auto()
    artifacts = auto()
    artifacts_comparison = auto()
    min_ratings = auto()
    format = "format"  # type: ignore

    minutes = auto()

    limit = auto()
    offset = auto()
    divergence = auto()
    client_agent = auto()
