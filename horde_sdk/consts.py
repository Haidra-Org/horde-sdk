"""Constants used by the SDK."""

from enum import IntEnum

from strenum import StrEnum

_ANONYMOUS_MODEL = "_ANONYMOUS_MODEL"
"""This model is on the API but does not have a name."""


class HTTPMethod(StrEnum):
    """An enum representing all HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


PAYLOAD_HTTP_METHODS = {HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH}


class HTTPStatusCode(IntEnum):
    """An enum representing all HTTP status codes."""

    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204

    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    NOT_ACCEPTABLE = 406
    REQUEST_TIMEOUT = 408
    CONFLICT = 409
    GONE = 410
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429

    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504


def get_all_success_status_codes() -> list[HTTPStatusCode]:
    """Return a list of all success status codes."""
    return [status_code for status_code in HTTPStatusCode if is_success_status_code(status_code)]


def get_all_error_status_codes() -> list[HTTPStatusCode]:
    """Return a list of all error status codes."""
    return [status_code for status_code in HTTPStatusCode if is_error_status_code(status_code)]


def is_success_status_code(status_code: HTTPStatusCode | int) -> bool:
    """Return True if the status code is a success code, False otherwise."""
    if isinstance(status_code, HTTPStatusCode):
        status_code = status_code.value
    return 200 <= status_code < 300


def is_error_status_code(status_code: HTTPStatusCode | int) -> bool:
    """Return True if the status code is an error code, False otherwise."""
    if isinstance(status_code, HTTPStatusCode):
        status_code = status_code.value
    return 400 <= status_code < 600
