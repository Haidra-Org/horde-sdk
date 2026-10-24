"""Tests for the chat capability, guarantee, conformance, and limit vocabulary."""

from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from horde_sdk.generation_parameters.text.chat_policy import (
    DEFAULT_CHAT_CONFORMANCE,
    KNOWN_CHAT_DECLARATIONS,
    ChatConformance,
    ChatFeature,
    ChatGuarantee,
    ChatLimitField,
    ChatReasoningEffort,
    ChatRequestTraits,
    ChatResponseFormatType,
    ChatServiceGap,
    ChatToolChoiceMode,
    ChatWorkerLimits,
    chat_request_requirements,
    chat_request_traits,
    chat_service_gap,
    parse_chat_declaration,
    required_chat_guarantees,
    violated_chat_limit,
)

_PLAIN_REQUEST = ChatRequestTraits(
    offers_tools=False,
    tool_choice_mode=ChatToolChoiceMode.AUTO,
    parallel_tool_calls=True,
    response_format_type=None,
    strict_schema=False,
    temperature=1.0,
)
"""A request without tools or a response format, at the OpenAI default temperature."""

_TOOL_REQUEST = dataclasses.replace(
    _PLAIN_REQUEST,
    offers_tools=True,
)
"""A request offering tools with automatic tool choice and parallel calls allowed."""

_KOBOLDCPP_LIKE_LIMITS = ChatWorkerLimits(
    max_context_length=8192,
    max_length=512,
    tools_max_temperature=1.0,
)
"""Limits of a backend that clamps temperature to 1.0 when tools are present."""


def test_feature_and_guarantee_values_do_not_overlap() -> None:
    """Capabilities and guarantees share one declared list, so a value resolves to exactly one enum."""
    feature_values = {feature.value for feature in ChatFeature}
    guarantee_values = {guarantee.value for guarantee in ChatGuarantee}

    assert feature_values.isdisjoint(guarantee_values)
    assert feature_values | guarantee_values == KNOWN_CHAT_DECLARATIONS


@pytest.mark.parametrize(
    "declaration",
    sorted(KNOWN_CHAT_DECLARATIONS),
)
def test_every_known_declaration_parses_to_its_enum_member(declaration: str) -> None:
    """Every defined value parses to the member carrying that exact value."""
    parsed = parse_chat_declaration(declaration)

    assert parsed is not None
    assert parsed.value == declaration
    assert isinstance(parsed, ChatFeature) != isinstance(parsed, ChatGuarantee)


def test_tools_with_response_format_is_a_capability() -> None:
    """Serving tools beside a response format is declared as a capability, which applies under every conformance
    mode, and not as a guarantee."""
    assert parse_chat_declaration("tools_with_response_format") is ChatFeature.TOOLS_WITH_RESPONSE_FORMAT


def test_undefined_declaration_parses_to_none() -> None:
    """A value from a newer SDK release is not mistaken for any defined capability or guarantee."""
    assert parse_chat_declaration("logprobs") is None


def test_request_conformance_defaults_to_strict() -> None:
    """A request that does not select a conformance mode is strict."""
    assert DEFAULT_CHAT_CONFORMANCE is ChatConformance.STRICT


def test_best_effort_requires_no_guarantee() -> None:
    """Best-effort requests are served without any declared guarantee, however constrained the request is."""
    constrained_request = dataclasses.replace(
        _TOOL_REQUEST,
        tool_choice_mode=ChatToolChoiceMode.REQUIRED,
        parallel_tool_calls=False,
        response_format_type=ChatResponseFormatType.JSON_SCHEMA,
        strict_schema=True,
    )

    assert required_chat_guarantees(constrained_request, ChatConformance.BEST_EFFORT) == frozenset()


def test_strict_always_requires_prompt_overflow_refusal() -> None:
    """A strict request without tools or a response format still requires overflow to fault instead of trim."""
    assert required_chat_guarantees(_PLAIN_REQUEST, ChatConformance.STRICT) == frozenset(
        {ChatGuarantee.PROMPT_OVERFLOW_REFUSED},
    )


@pytest.mark.parametrize(
    "tool_choice_mode",
    [
        ChatToolChoiceMode.REQUIRED,
        ChatToolChoiceMode.FUNCTION,
    ],
)
def test_strict_forced_tool_choice_requires_enforcement(tool_choice_mode: ChatToolChoiceMode) -> None:
    """A required tool choice, and one that specifies a function, require the backend to enforce the choice."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        tool_choice_mode=tool_choice_mode,
    )

    assert ChatGuarantee.TOOL_CHOICE_ENFORCED in required_chat_guarantees(traits, ChatConformance.STRICT)


def test_strict_automatic_tool_choice_requires_no_enforcement() -> None:
    """Automatic tool choice leaves the decision to the model, so no enforcement is required."""
    assert ChatGuarantee.TOOL_CHOICE_ENFORCED not in required_chat_guarantees(_TOOL_REQUEST, ChatConformance.STRICT)


def test_strict_none_tool_choice_requires_no_tool_guarantee() -> None:
    """Under ``tool_choice: none`` the definitions are not forwarded, so no tool guarantee is required."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        tool_choice_mode=ChatToolChoiceMode.NONE,
        parallel_tool_calls=False,
    )

    assert required_chat_guarantees(traits, ChatConformance.STRICT) == frozenset(
        {ChatGuarantee.PROMPT_OVERFLOW_REFUSED},
    )


def test_strict_tool_choice_without_offered_tools_requires_no_enforcement() -> None:
    """A tool choice has no effect when the request offers no tools."""
    traits = dataclasses.replace(
        _PLAIN_REQUEST,
        tool_choice_mode=ChatToolChoiceMode.REQUIRED,
        parallel_tool_calls=False,
    )

    assert required_chat_guarantees(traits, ChatConformance.STRICT) == frozenset(
        {ChatGuarantee.PROMPT_OVERFLOW_REFUSED},
    )


def test_strict_serial_tool_calls_require_no_single_call_enforcement() -> None:
    """Offered tools with parallel calls disabled need no guarantee; the server reduces a strict reply to one call."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        parallel_tool_calls=False,
    )

    assert ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED not in required_chat_guarantees(traits, ChatConformance.STRICT)


def test_strict_parallel_tool_calls_require_no_single_call_enforcement() -> None:
    """Offered tools with parallel calls allowed do not limit the call count."""
    assert ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED not in required_chat_guarantees(
        _TOOL_REQUEST,
        ChatConformance.STRICT,
    )


def test_strict_schema_requires_structured_output_enforcement() -> None:
    """A strict JSON Schema response format requires the backend not to fall back to free text."""
    traits = dataclasses.replace(
        _PLAIN_REQUEST,
        response_format_type=ChatResponseFormatType.JSON_SCHEMA,
        strict_schema=True,
    )

    assert ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED in required_chat_guarantees(traits, ChatConformance.STRICT)


@pytest.mark.parametrize(
    ("response_format_type", "strict_schema"),
    [
        (ChatResponseFormatType.JSON_SCHEMA, False),
        (ChatResponseFormatType.JSON_OBJECT, True),
        (None, True),
    ],
)
def test_non_strict_schema_requires_no_structured_output_enforcement(
    response_format_type: ChatResponseFormatType | None,
    strict_schema: bool,
) -> None:
    """Only a strict JSON Schema response format requires structured output enforcement."""
    traits = dataclasses.replace(
        _PLAIN_REQUEST,
        response_format_type=response_format_type,
        strict_schema=strict_schema,
    )

    assert ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED not in required_chat_guarantees(traits, ChatConformance.STRICT)


def test_limit_values_match_declared_limit_fields() -> None:
    """Each limit value is the field and wire key of the limit it identifies."""
    assert {limit_field.value for limit_field in ChatLimitField} == {
        field.name for field in dataclasses.fields(ChatWorkerLimits)
    }


def test_tool_temperature_above_bound_violates_limit() -> None:
    """A tool request hotter than the declared bound would be clamped by the backend."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        temperature=1.5,
    )

    assert violated_chat_limit(traits, _KOBOLDCPP_LIKE_LIMITS) is ChatLimitField.TOOLS_MAX_TEMPERATURE


def test_tool_temperature_at_bound_is_admitted() -> None:
    """A temperature equal to the bound is applied as sent."""
    assert violated_chat_limit(_TOOL_REQUEST, _KOBOLDCPP_LIKE_LIMITS) is None


@pytest.mark.parametrize(
    "traits",
    [
        dataclasses.replace(
            _PLAIN_REQUEST,
            temperature=1.5,
        ),
        dataclasses.replace(
            _TOOL_REQUEST,
            tool_choice_mode=ChatToolChoiceMode.NONE,
            temperature=1.5,
        ),
    ],
)
def test_temperature_bound_ignores_requests_without_forwarded_tools(traits: ChatRequestTraits) -> None:
    """The tool temperature bound applies only when tool definitions reach the backend."""
    assert violated_chat_limit(traits, _KOBOLDCPP_LIKE_LIMITS) is None


def test_unbounded_tool_temperature_admits_any_temperature() -> None:
    """A worker without a tool temperature bound applies the temperature as sent."""
    limits = dataclasses.replace(
        _KOBOLDCPP_LIKE_LIMITS,
        tools_max_temperature=None,
    )
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        temperature=2.0,
    )

    assert violated_chat_limit(traits, limits) is None


@pytest.mark.parametrize(
    ("max_context_length", "max_length", "tools_max_temperature"),
    [
        (0, 512, None),
        (8192, 0, None),
        (8192, 512, -0.1),
    ],
)
def test_unsatisfiable_limits_are_rejected(
    max_context_length: int,
    max_length: int,
    tools_max_temperature: float | None,
) -> None:
    """Non-positive token limits and negative temperature bounds cannot describe a working backend."""
    with pytest.raises(ValueError):
        ChatWorkerLimits(
            max_context_length=max_context_length,
            max_length=max_length,
            tools_max_temperature=tools_max_temperature,
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

_WEATHER_TOOL: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                },
            },
        },
    },
}
"""One function tool definition."""

_TOOL_HISTORY_BODY: dict[str, Any] = {
    "model": "koboldcpp/Example-8B",
    "messages": [
        {
            "role": "user",
            "content": "Weather in Oslo?",
        },
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "arguments": '{"city": "Oslo"}',
                    },
                },
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "4 degrees",
        },
    ],
}
"""A request body replaying a tool call and its answer, without offering tools."""

_IMAGE_BODY: dict[str, Any] = {
    "model": "koboldcpp/Example-VL",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "What is this?",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://example.com/cat.jpg",
                    },
                },
            ],
        },
    ],
}
"""A request body whose user message carries an image part."""


def test_minimal_body_traits_take_openai_defaults() -> None:
    """A body without optional fields offers no tools, constrains nothing, and samples at temperature 1."""
    assert chat_request_traits(_MINIMAL_BODY) == _PLAIN_REQUEST


def test_minimal_body_requires_only_prompt_overflow_refusal() -> None:
    """A plain strict request needs no capability and only the overflow guarantee."""
    requirements = chat_request_requirements(_MINIMAL_BODY)

    assert requirements.features == frozenset()
    assert requirements.guarantees == frozenset({ChatGuarantee.PROMPT_OVERFLOW_REFUSED})
    assert requirements.conformance is ChatConformance.STRICT


def test_best_effort_body_requires_no_guarantee() -> None:
    """``horde.conformance: best_effort`` drops every guarantee and keeps the capabilities."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "tool_choice": "required",
        "horde": {"conformance": "best_effort"},
    }

    requirements = chat_request_requirements(body)

    assert requirements.conformance is ChatConformance.BEST_EFFORT
    assert requirements.guarantees == frozenset()
    assert requirements.features == frozenset({ChatFeature.TOOLS})


def test_strict_tool_body_requires_tool_guarantees() -> None:
    """A strict body forcing one function without parallel calls needs the tool capability and the tool choice
    guarantee, and not the single call guarantee."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "tool_choice": {"type": "function", "function": {"name": "get_weather"}},
        "parallel_tool_calls": False,
    }

    requirements = chat_request_requirements(body)

    assert requirements.traits.tool_choice_mode is ChatToolChoiceMode.FUNCTION
    assert requirements.features == frozenset({ChatFeature.TOOLS})
    assert requirements.guarantees == frozenset(
        {
            ChatGuarantee.PROMPT_OVERFLOW_REFUSED,
            ChatGuarantee.TOOL_CHOICE_ENFORCED,
        },
    )


def test_tool_history_requires_tools_without_offered_tools() -> None:
    """Tool calls and tool answers in the history need a worker whose template renders them."""
    requirements = chat_request_requirements(_TOOL_HISTORY_BODY)

    assert requirements.traits.offers_tools is False
    assert requirements.features == frozenset({ChatFeature.TOOLS})


def test_image_part_requires_vision() -> None:
    """An ``image_url`` part needs a worker that reads images."""
    assert chat_request_requirements(_IMAGE_BODY).features == frozenset({ChatFeature.VISION})


def test_tool_choice_none_forwards_no_tools() -> None:
    """Under ``tool_choice: none`` the definitions are not forwarded, so no tool capability is needed."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "tool_choice": "none",
    }

    assert ChatFeature.TOOLS not in chat_request_requirements(body).features


def test_sampling_and_format_values_require_their_capabilities() -> None:
    """A seed, non-zero penalties, a strict schema format beside forwarded tools each need their declaration."""
    body = {
        **_MINIMAL_BODY,
        "seed": 7,
        "frequency_penalty": 0.5,
        "presence_penalty": -0.5,
        "temperature": 0.2,
        "tools": [_WEATHER_TOOL],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "answer", "strict": True, "schema": {"type": "object"}},
        },
    }

    requirements = chat_request_requirements(body)

    assert requirements.traits.temperature == 0.2
    assert requirements.traits.strict_schema is True
    assert requirements.features == frozenset(
        {
            ChatFeature.SEED,
            ChatFeature.FREQUENCY_PENALTY,
            ChatFeature.PRESENCE_PENALTY,
            ChatFeature.TOOLS,
            ChatFeature.JSON_SCHEMA,
            ChatFeature.TOOLS_WITH_RESPONSE_FORMAT,
        },
    )
    assert ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED in requirements.guarantees


def test_default_valued_penalties_and_text_format_require_nothing() -> None:
    """Values sent at their documented default need no capability."""
    body = {
        **_MINIMAL_BODY,
        "frequency_penalty": 0,
        "presence_penalty": 0.0,
        "response_format": {"type": "text"},
    }

    assert chat_request_requirements(body).features == frozenset()


@pytest.mark.parametrize("reasoning_effort", list(ChatReasoningEffort))
def test_reasoning_effort_requires_its_capability(reasoning_effort: ChatReasoningEffort) -> None:
    """Every reasoning effort needs the capability, ``none`` included, since a backend that ignores it reasons."""
    body = {
        **_MINIMAL_BODY,
        "reasoning_effort": reasoning_effort.value,
    }

    assert chat_request_requirements(body).features == frozenset({ChatFeature.REASONING_EFFORT})


def test_reasoning_effort_values_are_openais() -> None:
    """The accepted values are OpenAI's documented ``reasoning_effort`` set."""
    assert {reasoning_effort.value for reasoning_effort in ChatReasoningEffort} == {
        "none",
        "minimal",
        "low",
        "medium",
        "high",
        "xhigh",
    }


def test_tool_fields_without_tools_are_ignored() -> None:
    """``tool_choice`` and ``parallel_tool_calls`` have no effect without offered tools, as on the server."""
    body = {
        **_MINIMAL_BODY,
        "tool_choice": "required",
        "parallel_tool_calls": False,
    }

    assert chat_request_traits(body) == _PLAIN_REQUEST


def test_unknown_tool_choice_is_refused() -> None:
    """``function`` is the ``type`` of a function choice object, not a ``tool_choice`` string, so it is refused rather
    than read as any mode."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "tool_choice": "function",
    }

    with pytest.raises(ValueError):
        chat_request_traits(body)


def test_full_declaration_union_serves_request() -> None:
    """A model card union that holds every needed value, under a limit the request respects, leaves no gap."""
    requirements = chat_request_requirements(_IMAGE_BODY)

    assert (
        chat_service_gap(requirements, ["vision", "prompt_overflow_refused", "seed"], _KOBOLDCPP_LIKE_LIMITS) is None
    )


def test_union_lacking_a_guarantee_reports_it() -> None:
    """A union that lacks one guarantee the strict request needs reports that guarantee, as the server does."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "tool_choice": "required",
    }
    requirements = chat_request_requirements(body)

    gap = chat_service_gap(requirements, ["tools", "prompt_overflow_refused", "a_later_value"], _KOBOLDCPP_LIKE_LIMITS)

    assert gap == ChatServiceGap(missing_declarations=("tool_choice_enforced",))
    assert gap is not None
    assert gap.kind.value == "declaration_gap"


def test_gap_reports_exceeded_tool_temperature() -> None:
    """A tool request hotter than the declared bound reports the exceeded limit."""
    body = {
        **_MINIMAL_BODY,
        "tools": [_WEATHER_TOOL],
        "temperature": 1.5,
    }
    requirements = chat_request_requirements(body)

    gap = chat_service_gap(requirements, ["tools", "prompt_overflow_refused"], _KOBOLDCPP_LIKE_LIMITS)

    assert gap == ChatServiceGap(exceeded_limits=("tools_max_temperature",))
