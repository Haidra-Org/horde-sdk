"""Any model or helper useful for creating or interacting with a horde API."""

# isort: off
# We import dotenv first so that we can use it to load environment variables before importing anything else.
import ssl
import certifi
import dotenv

# If the current working directory contains a `.env` file, import the environment variables from it.
# This is useful for development.
dotenv.load_dotenv()

import os

# We import the horde_sdk logging module first so that we can use it to configure the logging system before importing
from horde_sdk.horde_logging import COMPLETE_LOGGER_LABEL, PROGRESS_LOGGER_LABEL

from loguru import logger

# isort: on


def _dev_env_var_warnings() -> None:  # pragma: no cover
    _dev_ai_horde_url = os.getenv("AI_HORDE_DEV_URL")
    _ai_horde_url = os.getenv("AI_HORDE_URL")

    if _dev_ai_horde_url:
        logger.debug(
            f"AI_HORDE_DEV_URL is {_dev_ai_horde_url}.",
        )
    elif _ai_horde_url:
        logger.debug(
            f"AI_HORDE_URL is {_ai_horde_url}.",
        )

    _ratings_dev_url = os.getenv("RATINGS_DEV_URL")
    if _ratings_dev_url:
        logger.debug(
            f"RATINGS_DEV_URL is {_ratings_dev_url}.",
        )

    _ai_worker_cache_home = os.getenv("AIWORKER_CACHE_HOME")
    if _ai_worker_cache_home:
        logger.debug(
            f"AIWORKER_CACHE_HOME is {_ai_worker_cache_home}.",
        )

    dev_key = os.getenv("AI_HORDE_DEV_APIKEY")
    if dev_key:
        logger.debug(
            "AI_HORDE_DEV_APIKEY is set.",
        )
        if len(dev_key) != 10 and len(dev_key) != 22:
            raise ValueError("AI_HORDE_DEV_APIKEY must be the anon key or 22 characters long.")

    AI_HORDE_MODEL_META_LARGE_MODELS = os.getenv("AI_HORDE_MODEL_META_LARGE_MODELS")
    if AI_HORDE_MODEL_META_LARGE_MODELS:
        logger.debug(
            f"AI_HORDE_MODEL_META_LARGE_MODELS is {AI_HORDE_MODEL_META_LARGE_MODELS}.",
        )


_dev_env_var_warnings()
_default_sslcontext = ssl.create_default_context(cafile=certifi.where())

from horde_sdk.consts import (
    PAYLOAD_HTTP_METHODS,
    HTTPMethod,
    HTTPStatusCode,
    get_all_error_status_codes,
    get_all_success_status_codes,
    is_error_status_code,
    is_success_status_code,
)
from horde_sdk.exceptions import HordeException
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIDataObject,
    HordeAPIMessage,
    HordeAPIObject,
    HordeRequest,
    RequestErrorResponse,
    RequestSpecifiesUserIDMixin,
    RequestUsesWorkerMixin,
    ResponseRequiringFollowUpMixin,
    ResponseWithProgressMixin,
)
from horde_sdk.generic_api.consts import ANON_API_KEY

__all__ = [
    "PAYLOAD_HTTP_METHODS",
    "HTTPMethod",
    "HTTPStatusCode",
    "get_all_error_status_codes",
    "get_all_success_status_codes",
    "is_error_status_code",
    "is_success_status_code",
    "APIKeyAllowedInRequestMixin",
    "HordeRequest",
    "ContainsMessageResponseMixin",
    "HordeAPIDataObject",
    "HordeAPIMessage",
    "HordeAPIObject",
    "RequestErrorResponse",
    "RequestSpecifiesUserIDMixin",
    "RequestUsesWorkerMixin",
    "ResponseRequiringFollowUpMixin",
    "ResponseWithProgressMixin",
    "ANON_API_KEY",
    "PROGRESS_LOGGER_LABEL",
    "COMPLETE_LOGGER_LABEL",
    "HordeException",
    "_default_sslcontext",
]
