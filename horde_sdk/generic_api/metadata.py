"""Metadata specific shared across all horde APIs.

These classes can be inherited and new values added to them to support new APIs' metadata.
See the `horde_sdk.generic_api.generic_clients` module for more information.

"""

from enum import auto

from strenum import StrEnum


class GenericHeaderFields(StrEnum):
    """`StrEnum` for data that is exclusively passed in the header of a request."""

    apikey = auto()
    accept = auto()
    # X_Fields = "X-Fields" # TODO?
    client_agent = auto()


class GenericAcceptTypes(StrEnum):
    """`StrEnum` for supported values for the header parameter 'accept'."""

    json = "application/json"
    # html = "application/html" # TODO?


class GenericPathFields(StrEnum):
    """`StrEnum` for data that is exclusively passed as part of a URL path (not a query string after the `?`)."""


class GenericQueryFields(StrEnum):
    """`StrEnum` for data that is exclusively passed as part of a URL query (after the `?`)."""
