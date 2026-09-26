"""Tests for the DNS resolution behavior in `horde_sdk`."""

import socket
from typing import override

import pytest
from aiohttp import TCPConnector
from aiohttp.abc import AbstractResolver, ResolveResult

import horde_sdk
from horde_sdk import HordeDNSResolver


class _StubResolver(AbstractResolver):
    """Answers or fails on demand, standing in for a real resolver."""

    def __init__(self, failure: OSError | None = None) -> None:
        """Record what this stub should do when asked to resolve.

        Args:
            failure: Raised by every call to `resolve` when given.
        """
        self.failure = failure
        self.resolved_hosts: list[str] = []
        self.closed = False
        self.close_calls = 0

    @override
    async def resolve(
        self,
        host: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        """Record the call, then answer or raise.

        Args:
            host: The hostname to resolve.
            port: The port to report alongside the address.
            family: The address family to resolve for.

        Returns:
            A single loopback result.
        """
        self.resolved_hosts.append(host)

        if self.failure is not None:
            raise self.failure

        return [
            ResolveResult(
                hostname=host,
                host="127.0.0.1",
                port=port,
                family=socket.AF_INET,
                proto=0,
                flags=0,
            ),
        ]

    @override
    async def close(self) -> None:
        """Record that this stub was closed."""
        self.closed = True
        self.close_calls += 1


def _install_stubs(
    monkeypatch: pytest.MonkeyPatch,
    primary: _StubResolver,
    fallback: _StubResolver,
) -> None:
    """Make `HordeDNSResolver` build the given stubs instead of real resolvers.

    Args:
        monkeypatch: The fixture used to replace the resolver types.
        primary: Used in place of `AsyncResolver`.
        fallback: Used in place of `ThreadedResolver`.
    """

    def _make_primary() -> _StubResolver:
        return primary

    def _make_fallback() -> _StubResolver:
        return fallback

    monkeypatch.setattr(horde_sdk, "AsyncResolver", _make_primary)
    monkeypatch.setattr(horde_sdk, "ThreadedResolver", _make_fallback)
    # `HordeDNSResolver` treats the async resolver as usable when aiohttp would have selected it.
    monkeypatch.setattr(horde_sdk, "DefaultResolver", _make_primary)


@pytest.mark.asyncio
async def test_HordeDNSResolver_prefers_the_async_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a working async resolver is used and the fallback is left alone."""
    primary = _StubResolver()
    fallback = _StubResolver()
    _install_stubs(monkeypatch, primary, fallback)

    resolver = HordeDNSResolver()
    assert await resolver.resolve("example.com")

    assert primary.resolved_hosts == ["example.com"]
    assert fallback.resolved_hosts == []


@pytest.mark.asyncio
async def test_HordeDNSResolver_latches_to_the_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an async resolver failure the system resolver survives disables the former."""
    primary = _StubResolver(OSError(None, "Could not contact DNS servers"))
    fallback = _StubResolver()
    _install_stubs(monkeypatch, primary, fallback)

    resolver = HordeDNSResolver()

    first = await resolver.resolve("example.com")
    assert first[0]["hostname"] == "example.com"
    assert fallback.resolved_hosts == ["example.com"]
    assert primary.closed

    await resolver.resolve("example.org")
    assert primary.resolved_hosts == ["example.com"]
    assert fallback.resolved_hosts == ["example.com", "example.org"]


@pytest.mark.asyncio
async def test_HordeDNSResolver_keeps_the_async_resolver_for_absent_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that a name neither resolver can answer raises without disabling the async resolver."""
    primary = _StubResolver(OSError(None, "Domain name not found"))
    fallback = _StubResolver(OSError(None, "Domain name not found"))
    _install_stubs(monkeypatch, primary, fallback)

    resolver = HordeDNSResolver()

    with pytest.raises(OSError, match="Domain name not found"):
        await resolver.resolve("nonexistent.invalid")

    assert not primary.closed

    with pytest.raises(OSError, match="Domain name not found"):
        await resolver.resolve("nonexistent.invalid")

    assert primary.resolved_hosts == ["nonexistent.invalid", "nonexistent.invalid"]


@pytest.mark.asyncio
async def test_HordeDNSResolver_close_releases_both_resolvers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that closing releases whichever backing resolvers were created."""
    primary = _StubResolver()
    fallback = _StubResolver()
    _install_stubs(monkeypatch, primary, fallback)

    resolver = HordeDNSResolver()
    await resolver.resolve("example.com")
    await resolver.close()

    assert primary.closed
    assert fallback.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("error_type", [OSError, RuntimeError])
async def test_HordeDNSResolver_falls_back_when_initialization_fails(
    monkeypatch: pytest.MonkeyPatch,
    error_type: type[Exception],
) -> None:
    fallback = _StubResolver()
    attempts = 0

    def fail_to_initialize() -> AbstractResolver:
        nonlocal attempts
        attempts += 1
        raise error_type("Async DNS is unavailable")

    monkeypatch.setattr(horde_sdk, "AsyncResolver", fail_to_initialize)
    monkeypatch.setattr(horde_sdk, "DefaultResolver", fail_to_initialize)
    monkeypatch.setattr(horde_sdk, "ThreadedResolver", lambda: fallback)

    resolver = HordeDNSResolver()
    try:
        assert await resolver.resolve("example.com")
        assert await resolver.resolve("example.org")
        assert attempts == 1
        assert fallback.resolved_hosts == ["example.com", "example.org"]
    finally:
        await resolver.close()


@pytest.mark.asyncio
async def test_session_close_releases_its_dns_resolvers(monkeypatch: pytest.MonkeyPatch) -> None:
    primary = _StubResolver()
    fallback = _StubResolver()
    _install_stubs(monkeypatch, primary, fallback)

    session = horde_sdk.create_aiohttp_client_session()
    assert isinstance(session.connector, TCPConnector)
    await session.connector._resolve_host("example.com", 80)
    await session.close()
    await session.close()

    assert primary.close_calls == 1
    assert fallback.close_calls == 1


@pytest.mark.asyncio
async def test_session_context_exception_releases_its_dns_resolvers(monkeypatch: pytest.MonkeyPatch) -> None:
    primary = _StubResolver()
    fallback = _StubResolver()
    _install_stubs(monkeypatch, primary, fallback)

    with pytest.raises(ValueError, match="request failed"):
        async with horde_sdk.create_aiohttp_client_session() as session:
            assert isinstance(session.connector, TCPConnector)
            await session.connector._resolve_host("example.com", 80)
            raise ValueError("request failed")

    assert primary.close_calls == 1
    assert fallback.close_calls == 1


@pytest.mark.asyncio
async def test_session_leaves_supplied_resolvers_caller_owned() -> None:
    resolver = _StubResolver()
    async with horde_sdk.create_aiohttp_client_session(resolver=resolver) as session:
        assert isinstance(session.connector, TCPConnector)
        await session.connector._resolve_host("example.com", 80)

    assert resolver.close_calls == 0
    assert await resolver.resolve("example.org")
    await resolver.close()
