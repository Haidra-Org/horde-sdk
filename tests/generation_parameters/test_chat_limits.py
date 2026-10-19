"""Tests for the chat route's shared request limits and the local limit check."""

from __future__ import annotations

from typing import Any

import pytest

from horde_sdk.generation_parameters.text.chat_limits import (
    MAX_CHAT_MAX_TOKENS,
    MAX_CHAT_SCHEMA_NESTING,
    MAX_CHAT_STOP_SEQUENCES,
    MAX_CHAT_TEXT_BYTES,
    MAX_CHAT_TOOL_COUNT,
    MAX_CHAT_TOOL_SPEC_BYTES,
    MIN_CHAT_MAX_TOKENS,
    chat_schema_exceeds_nesting,
    check_chat_request_limits,
)

_MINIMAL_BODY: dict[str, Any] = {
    "model": "koboldcpp/Example-8B",
    "messages": [
        {
            "role": "user",
            "content": "Hello.",
        },
    ],
}
"""A request body with every optional field absent."""


def _tool(function_name: str, parameters: object = None) -> dict[str, Any]:
    """Return a function tool definition with the given function and optional ``parameters`` schema."""
    function: dict[str, Any] = {"name": function_name}
    if parameters is not None:
        function["parameters"] = parameters
    return {"type": "function", "function": function}


def _nested_schema(levels: int) -> dict[str, Any]:
    """Return an object schema whose properties nest ``levels`` levels below the root."""
    schema: dict[str, Any] = {"type": "string"}
    for _ in range(levels):
        schema = {"type": "object", "properties": {"inner": schema}}
    return schema


def _violated_params(body: dict[str, Any]) -> list[str]:
    """Return the request paths of every violation the local check reports for ``body``."""
    return [violation.param for violation in check_chat_request_limits(body)]


def test_minimal_body_is_within_every_limit() -> None:
    """A body with every optional field absent exceeds no limit."""
    assert check_chat_request_limits(_MINIMAL_BODY) == ()


def test_values_at_their_bounds_are_within_limits() -> None:
    """Every bound is inclusive."""
    body = {
        **_MINIMAL_BODY,
        "max_tokens": MAX_CHAT_MAX_TOKENS,
        "max_completion_tokens": MIN_CHAT_MAX_TOKENS,
        "stop": ["a"] * MAX_CHAT_STOP_SEQUENCES,
        "temperature": 2,
        "top_p": 0,
        "frequency_penalty": -2,
        "presence_penalty": 2.0,
        "n": 1,
        "tools": [_tool(f"tool_{tool_index}") for tool_index in range(MAX_CHAT_TOOL_COUNT)],
    }

    assert check_chat_request_limits(body) == ()


def test_too_many_tools_are_reported() -> None:
    """A tool list longer than the cap is reported at ``tools``."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_tool(f"tool_{tool_index}") for tool_index in range(MAX_CHAT_TOOL_COUNT + 1)],
    }

    assert _violated_params(body) == ["tools"]


def test_oversized_tool_spec_is_reported() -> None:
    """Tool definitions larger than the spec cap are reported, whatever their count."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_tool("big", {"type": "object", "description": "x" * MAX_CHAT_TOOL_SPEC_BYTES})],
    }

    assert _violated_params(body) == ["tools"]


def test_tool_call_history_counts_toward_text_bytes() -> None:
    """Tool call arguments in the history count against the text cap with the message texts."""
    half_budget = MAX_CHAT_TEXT_BYTES // 2
    body = {
        **_MINIMAL_BODY,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": "x" * half_budget}],
            },
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "f", "arguments": "y" * half_budget},
                    },
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "done",
            },
        ],
    }

    assert _violated_params(body) == ["messages"]


def test_schema_at_nesting_limit_is_within_bounds() -> None:
    """A schema nesting exactly the documented number of levels is accepted."""
    assert chat_schema_exceeds_nesting(_nested_schema(MAX_CHAT_SCHEMA_NESTING)) is False


def test_deeply_nested_schemas_are_reported_where_they_occur() -> None:
    """A tool ``parameters`` schema and a response format schema nested past the limit are reported at their paths."""
    too_deep = _nested_schema(MAX_CHAT_SCHEMA_NESTING + 1)
    body = {
        **_MINIMAL_BODY,
        "tools": [_tool("shallow", {"type": "object"}), _tool("deep", too_deep)],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "schema": too_deep},
        },
    }

    assert _violated_params(body) == ["tools[1].function.parameters", "response_format.json_schema.schema"]


def test_schema_nested_past_recursion_limit_is_measured() -> None:
    """The nesting walk does not recurse, so a pathological schema is reported instead of crashing."""
    assert chat_schema_exceeds_nesting(_nested_schema(5000)) is True


@pytest.mark.parametrize(
    ("request_key", "request_value"),
    [
        ("max_tokens", MIN_CHAT_MAX_TOKENS - 1),
        ("max_completion_tokens", MAX_CHAT_MAX_TOKENS + 1),
        ("stop", ["a"] * (MAX_CHAT_STOP_SEQUENCES + 1)),
        ("temperature", 2.1),
        ("top_p", -0.1),
        ("frequency_penalty", 2.5),
        ("presence_penalty", -3),
        ("n", 2),
    ],
)
def test_value_outside_its_bound_is_reported(request_key: str, request_value: object) -> None:
    """Each bounded value outside its range is reported at its own key, with a sentence stating the bound."""
    violations = check_chat_request_limits({**_MINIMAL_BODY, request_key: request_value})

    assert [violation.param for violation in violations] == [request_key]
    assert violations[0].message.endswith(".")


def test_values_of_the_wrong_type_are_left_to_the_server() -> None:
    """The local check skips values the server refuses during validation instead of guessing at them."""
    body = {
        **_MINIMAL_BODY,
        "temperature": "hot",
        "max_tokens": True,
        "stop": "only one",
    }

    assert check_chat_request_limits(body) == ()
