"""Request-side limits and defaults of the AI-Horde chat route, shared by the server, workers and clients.

The server refuses a chat request that exceeds one of these limits before dispatching it, and fills these defaults into
a chat job's payload. Defining them once here lets a client check a request body locally with the same values
([`check_chat_request_limits`][horde_sdk.generation_parameters.text.chat_limits.check_chat_request_limits]) and keeps
the server from holding a second copy that could drift.

The server applies further request rules that need its full request models, such as OpenAI's tool history rule and
the structural rules of a strict JSON Schema. Those are not repeated here.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final

__all__ = [
    "CHAT_SAMPLING_DEFAULTS",
    "DEFAULT_PARALLEL_TOOL_CALLS",
    "MAX_CHAT_MAX_TOKENS",
    "MAX_CHAT_SCHEMA_NESTING",
    "MAX_CHAT_STOP_SEQUENCES",
    "MAX_CHAT_TEXT_BYTES",
    "MAX_CHAT_TOOL_COUNT",
    "MAX_CHAT_TOOL_SPEC_BYTES",
    "MIN_CHAT_MAX_TOKENS",
    "OPENAI_MIN_MAX_TOKENS",
    "OPENAI_SAMPLING_RANGES",
    "SUPPORTED_CHAT_CHOICE_COUNT",
    "ChatLimitViolation",
    "chat_schema_exceeds_nesting",
    "check_chat_request_limits",
]

MAX_CHAT_TOOL_COUNT: Final[int] = 128
"""The most tools one request may define, OpenAI's own bound. Each definition is rendered into the worker's prompt,
so the count also bounds how much prompt a request can add outside its messages."""

MAX_CHAT_TOOL_SPEC_BYTES: Final[int] = 256 * 1024
"""The most bytes the compact JSON of ``tools``, ``tool_choice`` and ``response_format`` together may take. The
worker renders these into the prompt or compiles them into a grammar, so an unbounded definition is an unbounded
amount of worker time outside the token budget."""

MAX_CHAT_TEXT_BYTES: Final[int] = 1024 * 1024
"""The most UTF-8 bytes the message texts of one chat request may hold together, counting the function names and
arguments of the tool calls in the history with them. 1 MiB is several times the text of the largest context a worker
serves, so no servable conversation reaches it, while the flattened estimate, moderation and the stored messages stay
bounded. Tool call arguments are copied into the flattened estimate and the worker's prompt like any text, so they
count against the same budget."""

MAX_CHAT_SCHEMA_NESTING: Final[int] = 10
"""The most levels a JSON Schema in a request may nest below its root, OpenAI's documented limit for strict schemas.
It applies to every tool ``parameters`` schema and every ``response_format`` schema, strict or not. A schema OpenAI
serves stays within it, and the bound keeps a small but deeply nested body from exceeding the recursion limit of the
JSON serialisation that stores and forwards it."""

OPENAI_MIN_MAX_TOKENS: Final[int] = 1
"""The smallest token limit OpenAI accepts; a value below it is refused in OpenAI's wording."""

MIN_CHAT_MAX_TOKENS: Final[int] = 16
"""The smallest token limit served; the native minimum for ``max_length``. A smaller limit OpenAI would accept is
refused rather than raised, since raising it would generate more tokens than the client asked for."""

MAX_CHAT_MAX_TOKENS: Final[int] = 4096
"""The largest token limit served; the native cap for ``max_length``."""

MAX_CHAT_STOP_SEQUENCES: Final[int] = 4
"""The most stop sequences a request may carry, as OpenAI documents."""

SUPPORTED_CHAT_CHOICE_COUNT: Final[int] = 1
"""The only ``n`` served: each further choice would need its own pinned model and stored reply."""

OPENAI_SAMPLING_RANGES: Final[Mapping[str, tuple[int, int]]] = MappingProxyType(
    {
        "temperature": (0, 2),
        "top_p": (0, 1),
        "frequency_penalty": (-2, 2),
        "presence_penalty": (-2, 2),
    },
)
"""The inclusive range OpenAI accepts for each sampling parameter; the native route accepts wider ranges for some, so
the front refuses a value OpenAI would refuse before forwarding it."""

CHAT_SAMPLING_DEFAULTS: Final[Mapping[str, float | int]] = MappingProxyType(
    {
        "temperature": 1.0,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "rep_pen": 1.0,
        "top_k": 0,
        "min_p": 0.0,
    },
)
"""The sampling values a chat job's payload carries when the client did not set them. They are OpenAI's defaults,
and neutral for the samplers OpenAI has no key for, so a worker's own defaults never apply to a chat job."""

DEFAULT_PARALLEL_TOOL_CALLS: Final[bool] = True
"""OpenAI's ``parallel_tool_calls`` when a request offers tools without setting it."""

_COMPACT_JSON_SEPARATORS: Final[tuple[str, str]] = (
    ",",
    ":",
)
"""The separators of compact JSON, which the server measures the tool spec in."""

_TEXT_CONTENT_PART_TYPE: Final[str] = "text"
"""The content part type carrying text."""

_JSON_SCHEMA_RESPONSE_FORMAT_TYPE: Final[str] = "json_schema"
"""The ``response_format`` type that carries a client schema."""

_TOKEN_LIMIT_KEYS: Final[tuple[str, ...]] = (
    "max_tokens",
    "max_completion_tokens",
)
"""The request keys holding a token limit; ``max_completion_tokens`` is OpenAI's newer key for ``max_tokens``."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatLimitViolation:
    """Represents one request-side limit a chat request body exceeds."""

    param: str
    """The request path at fault, such as ``tools[2].function.parameters``, as OpenAI's error ``param`` reports it."""

    message: str
    """One sentence stating the limit."""


def chat_schema_exceeds_nesting(schema: object) -> bool:
    """Return whether a JSON Schema nests more levels below its root than the limit allows.

    The limit is [`MAX_CHAT_SCHEMA_NESTING`][horde_sdk.generation_parameters.text.chat_limits.MAX_CHAT_SCHEMA_NESTING].
    Each level adds at most two JSON containers (a keyword's object or array, then the subschema in it), and the
    deepest subschema's own keywords one more, so the root container plus two per level plus one bounds every schema
    within the limit. The walk uses an explicit stack, so a value nested past the interpreter's recursion limit is
    measured too.

    Args:
        schema: The schema as decoded JSON; ``None`` and scalars never exceed the limit.

    Returns:
        True when the schema nests deeper than the limit allows.
    """
    max_container_depth = 1 + 2 * MAX_CHAT_SCHEMA_NESTING + 1
    pending: list[tuple[object, int]] = [(schema, 1)]
    while pending:
        current, depth = pending.pop()
        if isinstance(current, Mapping):
            children: list[object] = list(current.values())
        elif isinstance(current, list):
            children = current
        else:
            continue
        if depth > max_container_depth:
            return True
        pending.extend((child, depth + 1) for child in children)
    return False


def _as_list(value: object) -> list[Any]:
    """Return ``value`` when it is a JSON array, otherwise an empty list."""
    return value if isinstance(value, list) else []


def _as_mapping(value: object) -> Mapping[str, Any]:
    """Return ``value`` when it is a JSON object, otherwise an empty mapping."""
    return value if isinstance(value, Mapping) else {}


def _as_number(value: object) -> float | None:
    """Return ``value`` when it is a JSON number, otherwise ``None``; booleans are not numbers."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return value


def _message_text_bytes(messages: list[Any]) -> int:
    """Return the UTF-8 size of every message text and history tool call, measured as the server measures it."""

    def iter_texts() -> Iterator[str]:
        for message in messages:
            message_fields = _as_mapping(message)
            content = message_fields.get("content")
            if isinstance(content, str):
                yield content
            for content_part in _as_list(content):
                part_fields = _as_mapping(content_part)
                part_text = part_fields.get("text")
                if part_fields.get("type") == _TEXT_CONTENT_PART_TYPE and isinstance(part_text, str):
                    yield part_text
            for tool_call in _as_list(message_fields.get("tool_calls")):
                function_fields = _as_mapping(_as_mapping(tool_call).get("function"))
                for function_text in (function_fields.get("name"), function_fields.get("arguments")):
                    if isinstance(function_text, str):
                        yield function_text

    return sum(len(text.encode()) for text in iter_texts())


def _tool_spec_bytes(body: Mapping[str, Any]) -> int:
    """Return the UTF-8 size of the compact JSON of ``tools``, ``tool_choice`` and ``response_format`` together."""
    tool_spec = {
        "tools": _as_list(body.get("tools")),
        "tool_choice": body.get("tool_choice"),
        "response_format": body.get("response_format"),
    }
    return len(json.dumps(tool_spec, separators=_COMPACT_JSON_SEPARATORS, ensure_ascii=False).encode())


def _schema_violations(body: Mapping[str, Any]) -> Iterator[ChatLimitViolation]:
    """Yield a violation for each tool ``parameters`` schema and response format schema nested too deeply."""
    nesting_message = f"A JSON Schema may nest at most {MAX_CHAT_SCHEMA_NESTING} levels below its root."
    for tool_index, tool in enumerate(_as_list(body.get("tools"))):
        parameters = _as_mapping(_as_mapping(tool).get("function")).get("parameters")
        if chat_schema_exceeds_nesting(parameters):
            yield ChatLimitViolation(param=f"tools[{tool_index}].function.parameters", message=nesting_message)
    response_format = _as_mapping(body.get("response_format"))
    if response_format.get("type") == _JSON_SCHEMA_RESPONSE_FORMAT_TYPE:
        response_schema = _as_mapping(response_format.get("json_schema")).get("schema")
        if chat_schema_exceeds_nesting(response_schema):
            yield ChatLimitViolation(param="response_format.json_schema.schema", message=nesting_message)


def _value_violations(body: Mapping[str, Any]) -> Iterator[ChatLimitViolation]:
    """Yield a violation for each token limit, stop list, sampling value and choice count outside its bound."""
    for token_limit_key in _TOKEN_LIMIT_KEYS:
        token_limit = _as_number(body.get(token_limit_key))
        if token_limit is not None and not MIN_CHAT_MAX_TOKENS <= token_limit <= MAX_CHAT_MAX_TOKENS:
            yield ChatLimitViolation(
                param=token_limit_key,
                message=f"The token limit must be between {MIN_CHAT_MAX_TOKENS} and {MAX_CHAT_MAX_TOKENS}.",
            )
    stop = body.get("stop")
    if isinstance(stop, list) and len(stop) > MAX_CHAT_STOP_SEQUENCES:
        yield ChatLimitViolation(
            param="stop",
            message=f"A chat request may carry at most {MAX_CHAT_STOP_SEQUENCES} stop sequences.",
        )
    for sampling_key, (minimum, maximum) in OPENAI_SAMPLING_RANGES.items():
        sampling_value = _as_number(body.get(sampling_key))
        if sampling_value is not None and not minimum <= sampling_value <= maximum:
            yield ChatLimitViolation(
                param=sampling_key,
                message=f"'{sampling_key}' must be between {minimum} and {maximum}.",
            )
    choice_count = body.get("n")
    if choice_count is not None and choice_count != SUPPORTED_CHAT_CHOICE_COUNT:
        yield ChatLimitViolation(
            param="n",
            message=f"Only {SUPPORTED_CHAT_CHOICE_COUNT} choice is served; 'n' must be 1 or omitted.",
        )


def check_chat_request_limits(body: Mapping[str, Any]) -> tuple[ChatLimitViolation, ...]:
    """Return every limit in this module that an OpenAI chat completions request body exceeds.

    The checks are the ones these constants define: the tool count, the tool spec size, the message text size with
    the tool call history, the schema nesting of tool parameters and the response format, the token limit range, the
    stop sequence count, OpenAI's sampling ranges and the choice count. The server refuses a request that fails any of
    them. It also applies rules that need its full request models, which this check does not repeat, so an empty
    result does not mean the server accepts the request.

    Values of the wrong JSON type are skipped here; the server refuses them when it validates the body.

    Args:
        body: The request body as a client builds it, such as the keyword arguments of the OpenAI SDK's
            ``chat.completions.create``.

    Returns:
        The violations in request order, empty when the body is within every limit.
    """
    violations: list[ChatLimitViolation] = []
    tools = _as_list(body.get("tools"))
    if len(tools) > MAX_CHAT_TOOL_COUNT:
        violations.append(
            ChatLimitViolation(
                param="tools",
                message=f"A chat request may define at most {MAX_CHAT_TOOL_COUNT} tools.",
            ),
        )
    if _tool_spec_bytes(body) > MAX_CHAT_TOOL_SPEC_BYTES:
        violations.append(
            ChatLimitViolation(
                param="tools",
                message=(
                    f"'tools', 'tool_choice' and 'response_format' may take at most {MAX_CHAT_TOOL_SPEC_BYTES} bytes "
                    "together."
                ),
            ),
        )
    if _message_text_bytes(_as_list(body.get("messages"))) > MAX_CHAT_TEXT_BYTES:
        violations.append(
            ChatLimitViolation(
                param="messages",
                message=(
                    "The message text of a chat request, tool call names and arguments included, may be at most "
                    f"{MAX_CHAT_TEXT_BYTES} bytes."
                ),
            ),
        )
    violations.extend(_schema_violations(body))
    violations.extend(_value_violations(body))
    return tuple(violations)
