"""Any model or helper useful for creating or interacting with a horde API."""

# isort: off
# We import dotenv first so that we can use it to load environment variables before importing anything else.
import asyncio
import ssl
import certifi
import dotenv
import sys

import socket
from typing import Any, override

import aiohttp.client_exceptions
from aiohttp.abc import AbstractResolver, ResolveResult
from aiohttp.resolver import AsyncResolver, DefaultResolver, ThreadedResolver

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

_async_client_exceptions: tuple[type[Exception], ...] = (TimeoutError, aiohttp.client_exceptions.ClientError, OSError)

if sys.version_info[:2] == (3, 10):
    _async_client_exceptions = (asyncio.exceptions.TimeoutError, aiohttp.client_exceptions.ClientError, OSError)


class HordeDNSResolver(AbstractResolver):
    """Resolve hostnames with `aiodns`, falling back to the operating system resolver.

    `aiohttp` uses `AsyncResolver` whenever `aiodns` can be imported, which hands DNS for the entire
    process to c-ares. c-ares discovers nameservers itself rather than delegating to the operating
    system, and where that discovery yields nothing it answers every lookup with
    `Could not contact DNS servers` while the operating system resolves the same names normally.

    A name the operating system can answer and c-ares cannot means the channel is unusable rather
    than the record being absent, so the fallback latches for the life of the resolver. When neither
    can answer, the operating system error propagates and c-ares is kept for genuine negative
    answers.
    """

    _primary: AbstractResolver | None
    _fallback: AbstractResolver | None

    def __init__(self) -> None:
        """Initialise the resolver without creating either backing resolver.

        Both backing resolvers bind to the running event loop when constructed, so they are created
        on first use rather than here.
        """
        self._primary = None
        self._fallback = None
        self._primary_usable = DefaultResolver is AsyncResolver

    @override
    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        """Return the addresses for `host`.

        Args:
            host: The hostname to resolve.
            port: The port to report alongside each address.
            family: The address family to resolve for.

        Returns:
            The resolved addresses.
        """
        if self._fallback is None:
            self._fallback = ThreadedResolver()

        if not self._primary_usable:
            return await self._fallback.resolve(host, port, family)

        primary = self._primary
        try:
            if primary is None:
                primary = self._primary = AsyncResolver()
        except (OSError, RuntimeError) as primary_error:
            logger.warning(
                f"The asynchronous DNS resolver could not be initialized ({primary_error}). "
                "The operating system resolver will be used for all further lookups.",
            )
            self._primary_usable = False
            return await self._fallback.resolve(host, port, family)

        try:
            return await primary.resolve(host, port, family)
        except OSError as primary_error:
            resolved = await self._fallback.resolve(host, port, family)

            logger.warning(
                f"The asynchronous DNS resolver could not resolve {host} ({primary_error}), which "
                "the operating system resolver then resolved. The operating system resolver will "
                "be used for all further lookups.",
            )

            self._primary_usable = False
            self._primary = None
            await primary.close()

            return resolved

    @override
    async def close(self) -> None:
        """Release both backing resolvers."""
        for resolver in (self._primary, self._fallback):
            if resolver is not None:
                await resolver.close()

        self._primary = None
        self._fallback = None


class _ResolverOwnedTCPConnector(aiohttp.TCPConnector):
    """Close an internally created resolver when its connector closes."""

    def __init__(self, resolver: AbstractResolver) -> None:
        """Take ownership of the given resolver.

        Args:
            resolver: The resolver to release alongside this connector.
        """
        super().__init__(resolver=resolver)
        self._owned_resolver: AbstractResolver | None = resolver

    @override
    async def close(self, **kwargs: Any) -> None:
        """Close connections and release the resolver.

        Args:
            **kwargs: Passed through to the installed aiohttp connector's close method.
        """
        try:
            await super().close(**kwargs)
        finally:
            resolver = self._owned_resolver
            self._owned_resolver = None
            if resolver is not None:
                await resolver.close()


def create_aiohttp_client_session(
    *,
    resolver: AbstractResolver | None = None,
    **client_session_kwargs: Any,  # noqa: ANN401
) -> aiohttp.ClientSession:
    """Create a `ClientSession` whose DNS resolver is chosen rather than inferred.

    `aiohttp` picks its resolver from whether `aiodns` is importable anywhere in the environment, so
    an unrelated install decides DNS behavior for every session in the process. Sessions created
    here pin the resolver instead.

    The session closes an internally created resolver along with its connector. A resolver supplied
    by the caller remains caller-owned and must be closed by the caller.

    Args:
        resolver: The resolver to use. A `HordeDNSResolver` is created when this is omitted.
        **client_session_kwargs: Passed through to `aiohttp.ClientSession`.

    Returns:
        A session bound to the given resolver. A running event loop is required.
    """
    connector = (
        aiohttp.TCPConnector(resolver=resolver)
        if resolver is not None
        else _ResolverOwnedTCPConnector(HordeDNSResolver())
    )

    return aiohttp.ClientSession(connector=connector, **client_session_kwargs)


# It is important to load `horde_sdk.consts` here (and before `horde_sdk.generic_api`), after env vars are loaded
# so the CI will work as intended. See `get_default_frozen_model_config_dict` for more details.
from horde_sdk.consts import (
    KNOWN_DISPATCH_SOURCE,
    PAYLOAD_HTTP_METHODS,
    HTTPMethod,
    HTTPStatusCode,
    get_all_error_status_codes,
    get_all_success_status_codes,
    get_default_frozen_model_config_dict,
    is_error_status_code,
    is_success_status_code,
)
from horde_sdk.exceptions import HordeException
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIData,
    HordeAPIMessage,
    HordeAPIObject,
    HordeRequest,
    MessageSpecifiesUserIDMixin,
    RequestErrorResponse,
    RequestUsesWorkerMixin,
    ResponseRequiringFollowUpMixin,
    ResponseWithProgressMixin,
)
from horde_sdk.generic_api.consts import ANON_API_KEY
from horde_sdk.utils import create_bridge_agent_string

__all__ = [
    "ANON_API_KEY",
    "COMPLETE_LOGGER_LABEL",
    "KNOWN_DISPATCH_SOURCE",
    "PAYLOAD_HTTP_METHODS",
    "PROGRESS_LOGGER_LABEL",
    "APIKeyAllowedInRequestMixin",
    "ContainsMessageResponseMixin",
    "HTTPMethod",
    "HTTPStatusCode",
    "HordeAPIData",
    "HordeAPIMessage",
    "HordeAPIObject",
    "HordeDNSResolver",
    "HordeException",
    "HordeRequest",
    "MessageSpecifiesUserIDMixin",
    "RequestErrorResponse",
    "RequestUsesWorkerMixin",
    "ResponseRequiringFollowUpMixin",
    "ResponseWithProgressMixin",
    "_async_client_exceptions",
    "_default_sslcontext",
    "create_aiohttp_client_session",
    "create_bridge_agent_string",
    "get_all_error_status_codes",
    "get_all_success_status_codes",
    "get_default_frozen_model_config_dict",
    "is_error_status_code",
    "is_success_status_code",
]
