"""Metadata specific shared across all horde APIs."""

from enum import Enum


class GenericHeaderData(str, Enum):
    """Data that is exclusively passed in the header of a request."""

    apikey = "apikey"
    accept = "accept"
    # X_Fields = "X-Fields" # TODO?


class GenericAcceptTypes(str, Enum):
    """Supported values for the header parameter 'accept'."""

    json = "application/json"
    # html = "application/html" # TODO?


class GenericPathData(str, Enum):
    # TODO should this be made generic (IE, for user_id)?
    """Data that is exclusively passed as part of a URL path, and not after the '?' (query)."""
