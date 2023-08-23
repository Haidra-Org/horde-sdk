"""Metadata specific shared across all horde APIs.

These classes can be inherited and new values added to them to support new APIs' metadata.
See the `horde_sdk.generic_api.generic_clients` module for more information.

"""

from enum import auto

from strenum import StrEnum

# TODO: Extending enums is troublesome... would regular (BaseModel?) classes be better?


class GenericHeaderFields(StrEnum):
    """`StrEnum` for data that may be passed in the header of a request.

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """

    apikey = auto()
    accept = auto()
    # X_Fields = "X-Fields" # TODO?
    client_agent = auto()


class GenericAcceptTypes(StrEnum):
    """`StrEnum` for supported values for the header parameter 'accept'.

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """

    json = "application/json"
    # html = "application/html" # TODO?


class GenericPathFields(StrEnum):
    """`StrEnum` for data that may be passed as part of a URL path (before the query string).

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """


class GenericQueryFields(StrEnum):
    """`StrEnum` for data that may be passed as part of a URL query (after the `?`).

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """
