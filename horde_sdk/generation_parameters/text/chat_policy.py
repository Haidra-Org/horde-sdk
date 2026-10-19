"""Chat completion capability, fidelity, and conformance vocabulary shared by the AI-Horde and its workers.

A chat worker declares, on each job pop, the names it supports and the numeric limits it operates within. A chat
request is routed only to workers whose declarations cover what the request needs. The vocabulary separates three
kinds of declaration:

- A capability ([`ChatFeature`][horde_sdk.generation_parameters.text.chat_policy.ChatFeature]) states that the
  backend can act on a request input at all, such as a seed or tool definitions.
- A guarantee ([`ChatGuarantee`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee]) states that the
  backend follows one part of the OpenAI chat completions contract exactly, where a backend may otherwise
  deliberately deviate from it.
- A limit ([`ChatWorkerLimits`][horde_sdk.generation_parameters.text.chat_policy.ChatWorkerLimits]) bounds the values
  the backend applies as sent.

Capabilities and guarantees share one declared namespace on the wire, so their names never overlap.
[`parse_chat_declaration`][horde_sdk.generation_parameters.text.chat_policy.parse_chat_declaration] resolves a
declared name to either enum.

Each request carries a [`ChatConformance`][horde_sdk.generation_parameters.text.chat_policy.ChatConformance] mode.
[`required_chat_guarantees`][horde_sdk.generation_parameters.text.chat_policy.required_chat_guarantees] derives the
guarantees a request needs under that mode from its
[`ChatRequestTraits`][horde_sdk.generation_parameters.text.chat_policy.ChatRequestTraits], and
[`violated_chat_limit`][horde_sdk.generation_parameters.text.chat_policy.violated_chat_limit] checks the limits that
depend on request traits. Required capabilities depend on message content and are derived by the server.

Operator configuration narrows a worker's declarations and never widens them: a worker declares a guarantee only when
its backend implements the behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from strenum import StrEnum

__all__ = [
    "DEFAULT_CHAT_CONFORMANCE",
    "KNOWN_CHAT_DECLARATION_NAMES",
    "ChatConformance",
    "ChatFeature",
    "ChatGuarantee",
    "ChatLimitName",
    "ChatRequestTraits",
    "ChatResponseFormatType",
    "ChatToolChoiceMode",
    "ChatWorkerLimits",
    "parse_chat_declaration",
    "required_chat_guarantees",
    "violated_chat_limit",
]


class ChatFeature(StrEnum):
    """Identify one chat capability a worker declares and a request can require.

    The vocabulary grows by adding names. A name never changes meaning once published, because workers and servers
    built against different SDK releases compare the same strings.
    """

    SEED = "seed"
    """The backend honours a sampling seed."""

    PRESENCE_PENALTY = "presence_penalty"
    """The backend applies OpenAI's presence penalty."""

    FREQUENCY_PENALTY = "frequency_penalty"
    """The backend applies OpenAI's frequency penalty."""

    VISION = "vision"
    """The loaded model reads image parts. A worker also declares an image transport to receive them."""

    TOOLS = "tools"
    """The worker renders tool definitions and tool turns into its template and submits the model's tool calls."""

    JSON_OBJECT = "json_object"
    """The backend constrains the reply to a JSON object."""

    JSON_SCHEMA = "json_schema"
    """The backend constrains the reply to a client-supplied JSON Schema."""


class ChatGuarantee(StrEnum):
    """Identify one atomic promise that a backend follows part of the OpenAI chat contract exactly.

    A backend that does not declare a guarantee may deviate from the corresponding behavior. Like
    [`ChatFeature`][horde_sdk.generation_parameters.text.chat_policy.ChatFeature], the vocabulary grows by adding names
    and a name never changes meaning.
    """

    TOOL_CHOICE_ENFORCED = "tool_choice_enforced"
    """Under ``tool_choice: required`` the reply carries a call to an offered function, never prose alone.

    Under a named ``tool_choice`` the reply carries a call to the named function, never prose alone. Under
    ``tool_choice: none`` the reply carries no tool call.
    """

    SINGLE_TOOL_CALL_ENFORCED = "single_tool_call_enforced"
    """Under ``parallel_tool_calls: false`` the reply carries at most one tool call."""

    STRUCTURED_OUTPUT_ENFORCED = "structured_output_enforced"
    """A ``json_schema`` reply satisfies the schema or the job is faulted.

    The backend does not fall back to unconstrained text when it cannot apply the schema.
    """

    PROMPT_OVERFLOW_REFUSED = "prompt_overflow_refused"
    """A prompt that does not fit the declared context length faults the job instead of being trimmed."""


KNOWN_CHAT_DECLARATION_NAMES: Final[frozenset[str]] = frozenset(
    {
        *(feature.value for feature in ChatFeature),
        *(guarantee.value for guarantee in ChatGuarantee),
    },
)
"""Every capability and guarantee name this SDK release defines, as declared in one wire list."""


def parse_chat_declaration(declared_name: str) -> ChatFeature | ChatGuarantee | None:
    """Parse one declared chat name into the capability or guarantee it identifies.

    A worker built against a newer SDK release can declare names this release does not define. Such names resolve
    to ``None`` so the caller can ignore them; an undefined name never satisfies a requirement.

    Args:
        declared_name: One entry of a worker's declared chat feature list.

    Returns:
        The matching capability or guarantee, or ``None`` when this SDK release does not define the name.
    """
    if declared_name in ChatFeature.__members__.values():
        return ChatFeature(declared_name)
    if declared_name in ChatGuarantee.__members__.values():
        return ChatGuarantee(declared_name)
    return None


class ChatConformance(StrEnum):
    """Identify how closely a chat request requires the backend to follow the OpenAI chat contract."""

    STRICT = "strict"
    """Every guarantee the request needs must be declared by the worker, and the server verifies replies."""

    BEST_EFFORT = "best_effort"
    """Capabilities and limits still apply; guarantees are not required and replies pass through unverified."""


DEFAULT_CHAT_CONFORMANCE: Final[ChatConformance] = ChatConformance.STRICT
"""The conformance mode of a request that does not select one."""


class ChatToolChoiceMode(StrEnum):
    """Identify the backend-neutral form of an OpenAI ``tool_choice`` value."""

    NONE = "none"
    """The model must not call a tool."""

    AUTO = "auto"
    """The model decides whether to call an offered tool."""

    REQUIRED = "required"
    """The model must call at least one offered tool."""

    NAMED = "named"
    """The model must call the one function the request specifies."""


class ChatResponseFormatType(StrEnum):
    """Identify an OpenAI ``response_format`` type that constrains the reply.

    The unconstrained ``text`` type has no member; it is represented by ``None`` where a response format is optional.
    """

    JSON_OBJECT = "json_object"
    """The reply must be a JSON object."""

    JSON_SCHEMA = "json_schema"
    """The reply must satisfy a client-supplied JSON Schema."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatRequestTraits:
    """Represents the parts of a chat request that decide which guarantees and limits apply.

    The traits are backend-neutral; the server derives them once from the request after applying API defaults.
    """

    offers_tools: bool
    """Whether the request supplies at least one tool definition."""

    tool_choice_mode: ChatToolChoiceMode
    """How the request constrains tool calls. Without offered tools the mode has no effect."""

    parallel_tool_calls: bool
    """Whether the reply may carry more than one tool call."""

    response_format_type: ChatResponseFormatType | None
    """The constraining response format, or ``None`` for unconstrained text."""

    strict_schema: bool
    """Whether a ``json_schema`` response format asks for strict schema adherence."""

    temperature: float
    """The sampling temperature the server forwards to the backend."""

    @property
    def forwards_tools(self) -> bool:
        """Return whether the server forwards tool definitions to the backend.

        The server does not forward tool definitions under ``tool_choice: none``. Without definitions the backend
        cannot produce a tool call, so ``none`` is satisfied without any backend guarantee and no tool-dependent
        backend behavior is triggered.
        """
        return self.offers_tools and self.tool_choice_mode is not ChatToolChoiceMode.NONE


def required_chat_guarantees(
    traits: ChatRequestTraits,
    conformance: ChatConformance,
) -> frozenset[ChatGuarantee]:
    """Return the guarantees a worker must declare to serve a request under ``conformance``.

    Under [`ChatConformance.BEST_EFFORT`][horde_sdk.generation_parameters.text.chat_policy.ChatConformance.BEST_EFFORT]
    no guarantee is required. Under
    [`ChatConformance.STRICT`][horde_sdk.generation_parameters.text.chat_policy.ChatConformance.STRICT]:

    - forwarded tools with a ``required`` or named choice require
      [`TOOL_CHOICE_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.TOOL_CHOICE_ENFORCED];
      ``tool_choice: none`` requires nothing because the server does not forward the definitions;
    - forwarded tools without parallel tool calls require
      [`SINGLE_TOOL_CALL_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED];
    - a strict ``json_schema`` response format requires
      [`STRUCTURED_OUTPUT_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED];
    - every request requires
      [`PROMPT_OVERFLOW_REFUSED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.PROMPT_OVERFLOW_REFUSED].

    Args:
        traits: The request's policy-relevant traits.
        conformance: The conformance mode the request selected.

    Returns:
        The guarantees the serving worker must declare.
    """
    if conformance is ChatConformance.BEST_EFFORT:
        return frozenset()

    required_guarantees = {ChatGuarantee.PROMPT_OVERFLOW_REFUSED}
    if traits.forwards_tools and traits.tool_choice_mode is not ChatToolChoiceMode.AUTO:
        required_guarantees.add(ChatGuarantee.TOOL_CHOICE_ENFORCED)
    if traits.forwards_tools and not traits.parallel_tool_calls:
        required_guarantees.add(ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED)
    if traits.response_format_type is ChatResponseFormatType.JSON_SCHEMA and traits.strict_schema:
        required_guarantees.add(ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED)
    return frozenset(required_guarantees)


class ChatLimitName(StrEnum):
    """Identify one numeric limit a chat worker declares.

    Each value equals the field name in
    [`ChatWorkerLimits`][horde_sdk.generation_parameters.text.chat_policy.ChatWorkerLimits] and the key in the
    worker's declared ``chat_limits``.
    """

    MAX_CONTEXT_LENGTH = "max_context_length"
    """The largest prompt, in tokens, the backend accepts."""

    MAX_LENGTH = "max_length"
    """The largest reply, in tokens, the backend generates."""

    TOOLS_MAX_TEMPERATURE = "tools_max_temperature"
    """The highest temperature the backend applies as sent when tools are present."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatWorkerLimits:
    """Represents the numeric bounds within which a chat worker applies request values as sent."""

    max_context_length: int
    """The largest prompt, in tokens, the backend accepts."""

    max_length: int
    """The largest reply, in tokens, the backend generates."""

    tools_max_temperature: float | None = None
    """The temperature the backend clamps to when tools are present.

    ``None`` means the backend applies the temperature as sent whether or not tools are present.
    """

    def __post_init__(self) -> None:
        """Reject bounds that no request could satisfy."""
        token_bounds = (
            self.max_context_length,
            self.max_length,
        )
        if any(not isinstance(bound, int) or isinstance(bound, bool) or bound < 1 for bound in token_bounds):
            raise ValueError("Chat token limits must be positive integers.")
        if self.tools_max_temperature is not None and self.tools_max_temperature < 0:
            raise ValueError("A tool temperature bound must not be negative.")


def violated_chat_limit(
    traits: ChatRequestTraits,
    limits: ChatWorkerLimits,
) -> ChatLimitName | None:
    """Return the worker limit that would alter a request's values, if any.

    Only limits that depend on request traits are checked here. Context and reply lengths depend on tokenized
    message content and are compared by the server against the declared
    [`MAX_CONTEXT_LENGTH`][horde_sdk.generation_parameters.text.chat_policy.ChatLimitName.MAX_CONTEXT_LENGTH] and
    [`MAX_LENGTH`][horde_sdk.generation_parameters.text.chat_policy.ChatLimitName.MAX_LENGTH].

    Limits apply under every conformance mode, because a clamped value changes the request rather than how faithfully
    the reply follows it.

    Args:
        traits: The request's policy-relevant traits.
        limits: The limits the candidate worker declared.

    Returns:
        The violated limit, or ``None`` when the worker applies the request's values as sent.
    """
    if (
        traits.forwards_tools
        and limits.tools_max_temperature is not None
        and traits.temperature > limits.tools_max_temperature
    ):
        return ChatLimitName.TOOLS_MAX_TEMPERATURE
    return None
