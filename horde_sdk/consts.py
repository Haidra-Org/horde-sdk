"""Constants used by the SDK."""

import os
from enum import IntEnum, auto
from uuid import UUID

from pydantic import ConfigDict
from strenum import StrEnum

_ANONYMOUS_MODEL = "_ANONYMOUS_MODEL"
"""This model is on the API but does not have a name."""

_OVERLOADED_MODEL = "_MODEL_OVERLOADED"
"""The model is used incorrectly on the API."""

ID_TYPES = str | UUID
"""The types that can be used as IDs."""

horde_sdk_github_url = "https://github.com/Haidra-Org/horde_sdk"


def get_default_frozen_model_config_dict() -> ConfigDict:
    """Return the default horde-sdk frozen model config dict for a pydantic `BaseModel`.

    Critically, models configured this way will behave differently when used in tests, preventing
    the use of extra fields being passed to constructors. However, this is not the case in production,
    where pass-through is allowed and up to implementors to choose to handle.
    """
    return (
        ConfigDict(
            frozen=True,
            use_attribute_docstrings=True,
            extra="allow",
        )
        if not os.getenv("TESTS_ONGOING")
        else ConfigDict(
            frozen=True,
            use_attribute_docstrings=True,
            extra="forbid",
        )
    )


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


class KNOWN_DISPATCH_SOURCE(StrEnum):
    """The known sources of a dispatch."""

    UNKNOWN = auto()
    """The source of the dispatch is unknown."""

    LOCAL_CUSTOM_3RD_PARTY = auto()
    """The source of the dispatch is a local custom 3rd party API."""

    AI_HORDE_API_OFFICIAL = auto()
    """The source of the dispatch is the official AI Horde API."""

    AI_HORDE_API_FORK = auto()
    """The source of the dispatch is a fork of the official AI Horde API."""


class KNOWN_NSFW_DETECTOR(StrEnum):
    """The NSFW detectors that are known to the API."""

    BACKEND_DEFAULT = auto()
    """The default model for the worker backend."""

    HORDE_SAFETY = auto()
    """The AI-Horde horde_safety package."""

    COMPVIS_SAFETY_CHECKER = auto()
    """The compvis safety checker model released with stable diffusion."""


class WORKER_TYPE(StrEnum):
    """The worker types that are known.

    (alchemy, image, text, etc...)
    """

    image = auto()
    """Image generation worker."""
    text = auto()
    """Text generation worker."""
    interrogation = auto()
    """Alchemy/Interrogation worker."""
    alchemist = "interrogation"
    """Alchemy/Interrogation worker."""
    video = auto()
    """Video generation worker."""
    audio = auto()
    """Audio generation worker."""


class KNOWN_INFERENCE_BACKEND(StrEnum):
    """The known generative inference backends."""

    UNKNOWN = auto()
    """The inference backend is unknown."""

    IN_MODEL_NAME = auto()
    """The model name is prepended with the backend name."""

    CUSTOM_UNPUBLISHED = auto()
    """The inference backend is a custom, unpublished backend."""

    COMFYUI = auto()
    """The inference backend is ComfyUI."""

    A1111 = auto()
    """The inference backend is A1111."""

    HORDE_ALCHEMIST = auto()
    """The inference backend is the Horde Alchemist."""

    KOBOLD_CPP = auto()
    """The inference backend is Kobold CPP."""

    APHRODITE = auto()
    """The inference backend is Aphrodite."""


class KNOWN_ALCHEMY_BACKEND(StrEnum):
    """The known alchemy backends."""

    UNKNOWN = auto()
    """The alchemy backend is unknown."""

    CUSTOM_UNPUBLISHED = auto()
    """The alchemy backend is a custom, unpublished backend."""

    HORDE_ALCHEMIST = auto()
    """The alchemy backend is the Horde Alchemist."""
