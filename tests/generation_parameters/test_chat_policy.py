"""Tests for the chat capability, guarantee, conformance, and limit vocabulary."""

from __future__ import annotations

import dataclasses

import pytest

from horde_sdk.generation_parameters.text.chat_policy import (
    DEFAULT_CHAT_CONFORMANCE,
    KNOWN_CHAT_DECLARATION_NAMES,
    ChatConformance,
    ChatFeature,
    ChatGuarantee,
    ChatLimitName,
    ChatRequestTraits,
    ChatResponseFormatType,
    ChatToolChoiceMode,
    ChatWorkerLimits,
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


def test_feature_and_guarantee_names_do_not_overlap() -> None:
    """Capabilities and guarantees share one declared list, so a name resolves to exactly one enum."""
    feature_names = {feature.value for feature in ChatFeature}
    guarantee_names = {guarantee.value for guarantee in ChatGuarantee}

    assert feature_names.isdisjoint(guarantee_names)
    assert feature_names | guarantee_names == KNOWN_CHAT_DECLARATION_NAMES


@pytest.mark.parametrize(
    "declared_name",
    sorted(KNOWN_CHAT_DECLARATION_NAMES),
)
def test_every_known_declaration_parses_to_its_enum_member(declared_name: str) -> None:
    """Every defined name parses to the member carrying that exact value."""
    parsed = parse_chat_declaration(declared_name)

    assert parsed is not None
    assert parsed.value == declared_name
    assert isinstance(parsed, ChatFeature) != isinstance(parsed, ChatGuarantee)


def test_undefined_declaration_parses_to_none() -> None:
    """A name from a newer SDK release is not mistaken for any defined capability or guarantee."""
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
        ChatToolChoiceMode.NAMED,
    ],
)
def test_strict_forced_tool_choice_requires_enforcement(tool_choice_mode: ChatToolChoiceMode) -> None:
    """Required and named tool choices require the backend to enforce the choice."""
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


def test_strict_serial_tool_calls_require_single_call_enforcement() -> None:
    """Offered tools with parallel calls disabled require at most one call per reply."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        parallel_tool_calls=False,
    )

    assert ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED in required_chat_guarantees(traits, ChatConformance.STRICT)


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


def test_limit_names_match_declared_limit_fields() -> None:
    """Each limit name is the field and wire key of the limit it identifies."""
    assert {limit_name.value for limit_name in ChatLimitName} == {
        field.name for field in dataclasses.fields(ChatWorkerLimits)
    }


def test_tool_temperature_above_bound_violates_limit() -> None:
    """A tool request hotter than the declared bound would be clamped by the backend."""
    traits = dataclasses.replace(
        _TOOL_REQUEST,
        temperature=1.5,
    )

    assert violated_chat_limit(traits, _KOBOLDCPP_LIKE_LIMITS) is ChatLimitName.TOOLS_MAX_TEMPERATURE


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
