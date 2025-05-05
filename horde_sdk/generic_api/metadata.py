"""Metadata specific shared across all horde APIs.

These classes can be inherited and new values added to them to support new APIs' metadata.
See the `horde_sdk.generic_api.generic_clients` module for more information.

"""

from enum import auto

from strenum import StrEnum

# TODO: Extending enums is troublesome... would regular (BaseModel?) classes be better?


class GenericHeaderFields(StrEnum):
    """`StrEnum` for data that may be passed in the header of a request.

    Maps the python object's field name which matches to a comparable header. This implies that fields with these
    names are *always* passed in the header of a request.

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

    Used to replace path parameters like `/api/v1/{path_field}` with the value of the field. This implies that fields
    with these names are *always* passed in the path of a request.

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """


class GenericQueryFields(StrEnum):
    """`StrEnum` for data that may be passed as part of a URL query (after the `?`).

    Used to replace query parameters like `/api/v1/resource?query_field=value` with the value of the field.
    This implies that fields with these names are *always* passed in the query of a request.

    Pass this in to a GenericClient initializer if implementing a new API. See an existing API's `metadata.py` module.
    """
