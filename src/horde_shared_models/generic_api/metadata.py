"""Metadata specific shared across all horde APIs."""

from enum import Enum


class GenericHeaderData(str, Enum):
    """`Enum` for data that is exclusively passed in the header of a request."""

    apikey = "apikey"
    accept = "accept"
    # X_Fields = "X-Fields" # TODO?


class GenericAcceptTypes(str, Enum):
    """`Enum` for supported values for the header parameter 'accept'."""

    json = "application/json"
    # html = "application/html" # TODO?


class GenericPathData(str, Enum):
    # TODO should this be made generic (IE, for user_id)?
    """`Enum` for data that is exclusively passed as part of a URL path, and not after the '?' (query)."""
