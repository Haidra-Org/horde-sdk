"""Metadata specific shared across all horde APIs."""

from enum import auto

from strenum import StrEnum


class GenericHeaderData(StrEnum):
    """`StrEnum` for data that is exclusively passed in the header of a request."""

    apikey = auto()
    accept = auto()
    # X_Fields = "X-Fields" # TODO?


class GenericAcceptTypes(StrEnum):
    """`StrEnum` for supported values for the header parameter 'accept'."""

    json = "application/json"
    # html = "application/html" # TODO?


class GenericPathData(StrEnum):
    """`StrEnum` for data that is exclusively passed as part of a URL path, and not after the '?' (query)."""
