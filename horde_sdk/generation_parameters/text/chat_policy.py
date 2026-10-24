"""Chat completion capability, fidelity, and conformance vocabulary shared by the AI-Horde and its workers.

A chat worker declares, on each job pop, the capabilities and guarantees it supports and the numeric limits it
operates within. A chat
request is routed only to workers whose declarations cover what the request needs. The vocabulary separates three
kinds of declaration:

- A capability ([`ChatFeature`][horde_sdk.generation_parameters.text.chat_policy.ChatFeature]) states that the
  backend can act on a request input at all, such as a seed or tool definitions.
- A guarantee ([`ChatGuarantee`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee]) states that the
  backend follows one part of the OpenAI chat completions contract exactly, where a backend may otherwise
  deliberately deviate from it.
- A limit ([`ChatWorkerLimits`][horde_sdk.generation_parameters.text.chat_policy.ChatWorkerLimits]) bounds the values
  the backend applies as sent.

Capabilities and guarantees share one declared namespace on the wire, so their values never overlap.
[`parse_chat_declaration`][horde_sdk.generation_parameters.text.chat_policy.parse_chat_declaration] resolves a
declared value to either enum.

Each request carries a [`ChatConformance`][horde_sdk.generation_parameters.text.chat_policy.ChatConformance] mode.
[`required_chat_guarantees`][horde_sdk.generation_parameters.text.chat_policy.required_chat_guarantees] derives the
guarantees a request needs under that mode from its
[`ChatRequestTraits`][horde_sdk.generation_parameters.text.chat_policy.ChatRequestTraits], and
[`violated_chat_limit`][horde_sdk.generation_parameters.text.chat_policy.violated_chat_limit] checks the limits that
depend on request traits.

A client can run the same derivation over an OpenAI-shaped request body before sending it:
[`chat_request_requirements`][horde_sdk.generation_parameters.text.chat_policy.chat_request_requirements] returns the
capabilities and guarantees the request needs, and
[`chat_service_gap`][horde_sdk.generation_parameters.text.chat_policy.chat_service_gap] compares them with a model's
declared feature union and a worker's limits, in the shape the server's ``impossible_reason`` reports.

Operator configuration narrows a worker's declarations and never widens them: a worker declares a guarantee only when
its backend implements the behavior.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from strenum import StrEnum

from horde_sdk.generation_parameters.text.chat_limits import CHAT_SAMPLING_DEFAULTS, DEFAULT_PARALLEL_TOOL_CALLS

__all__ = [
    "DEFAULT_CHAT_CONFORMANCE",
    "KNOWN_CHAT_DECLARATIONS",
    "ChatConformance",
    "ChatFeature",
    "ChatGuarantee",
    "ChatLimitField",
    "ChatReasoningEffort",
    "ChatRequestTraits",
    "ChatRequirements",
    "ChatResponseFormatType",
    "ChatServiceGap",
    "ChatServiceGapKind",
    "ChatToolChoiceMode",
    "ChatWorkerLimits",
    "chat_request_conformance",
    "chat_request_requirements",
    "chat_request_traits",
    "chat_service_gap",
    "parse_chat_declaration",
    "required_chat_guarantees",
    "violated_chat_limit",
]


class ChatFeature(StrEnum):
    """Identify one chat capability a worker declares and a request can require.

    The vocabulary grows by adding values; a value never changes meaning once published, because workers and servers
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

    TOOLS_WITH_RESPONSE_FORMAT = "tools_with_response_format"
    """The backend serves a request that offers tools and sets a response format together, applying the format to the
    final text answer and not to tool calls, as OpenAI does. A capability rather than a guarantee, so a request needs
    it under either conformance mode."""

    REASONING_EFFORT = "reasoning_effort"
    """The backend applies the requested
    [`ChatReasoningEffort`][horde_sdk.generation_parameters.text.chat_policy.ChatReasoningEffort] to the model's
    reasoning; ``none`` disables thinking."""


class ChatGuarantee(StrEnum):
    """Identify one atomic promise that a backend follows part of the OpenAI chat contract exactly.

    A backend that does not declare a guarantee may deviate from the corresponding behavior. Like
    [`ChatFeature`][horde_sdk.generation_parameters.text.chat_policy.ChatFeature], the vocabulary grows by adding
    values; a value never changes meaning.
    """

    TOOL_CHOICE_ENFORCED = "tool_choice_enforced"
    """Under ``tool_choice: required`` the reply carries a call to an offered function, never prose alone.

    Under a ``tool_choice`` that specifies one function the reply carries a call to that function, never prose
    alone. Under
    ``tool_choice: none`` the reply carries no tool call.
    """

    SINGLE_TOOL_CALL_ENFORCED = "single_tool_call_enforced"
    """Under ``parallel_tool_calls: false`` the reply carries at most one tool call.

    A worker may declare it, and no request requires it: under ``strict`` the server reduces a reply's tool calls to
    the first when parallel calls are off, so the client receives at most one call from any worker, and routing on
    the guarantee would only narrow the workers that can serve the request.
    """

    STRUCTURED_OUTPUT_ENFORCED = "structured_output_enforced"
    """A ``json_schema`` reply satisfies the schema or the job is faulted.

    The backend does not fall back to unconstrained text when it cannot apply the schema.
    """

    PROMPT_OVERFLOW_REFUSED = "prompt_overflow_refused"
    """A prompt that does not fit the declared context length faults the job instead of being trimmed."""


KNOWN_CHAT_DECLARATIONS: Final[frozenset[str]] = frozenset(
    {
        *(feature.value for feature in ChatFeature),
        *(guarantee.value for guarantee in ChatGuarantee),
    },
)
"""Every capability and guarantee value this SDK release defines, as declared in one wire list."""


def parse_chat_declaration(declaration: str) -> ChatFeature | ChatGuarantee | None:
    """Parse one declared chat value into the capability or guarantee it identifies.

    A worker built against a newer SDK release can declare values this release does not define. Such values resolve
    to ``None`` so the caller can ignore them; an undefined value never satisfies a requirement.

    Args:
        declaration: One entry of a worker's declared chat feature list.

    Returns:
        The matching capability or guarantee, or ``None`` when this SDK release does not define the value.
    """
    if declaration in ChatFeature.__members__.values():
        return ChatFeature(declaration)
    if declaration in ChatGuarantee.__members__.values():
        return ChatGuarantee(declaration)
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

    FUNCTION = "function"
    """The model must call the one function the request specifies. The value is the ``type`` OpenAI's ``tool_choice``
    object carries for that choice; as a bare string it is not a valid ``tool_choice``."""


class ChatResponseFormatType(StrEnum):
    """Identify an OpenAI ``response_format`` type that constrains the reply.

    The unconstrained ``text`` type has no member; it is represented by ``None`` where a response format is optional.
    """

    JSON_OBJECT = "json_object"
    """The reply must be a JSON object."""

    JSON_SCHEMA = "json_schema"
    """The reply must satisfy a client-supplied JSON Schema."""


class ChatReasoningEffort(StrEnum):
    """Identify an OpenAI ``reasoning_effort`` value, from no reasoning to the most.

    The values are OpenAI's documented set. The server forwards the value unchanged and applies no default, so how
    much reasoning each value buys is the backend's mapping.
    """

    NONE = "none"
    """The model does not reason before answering."""

    MINIMAL = "minimal"
    """The least reasoning short of none."""

    LOW = "low"
    """Little reasoning."""

    MEDIUM = "medium"
    """Moderate reasoning."""

    HIGH = "high"
    """Much reasoning."""

    XHIGH = "xhigh"
    """The most reasoning; OpenAI accepts it only for some models."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatRequestTraits:
    """Represents the parts of a chat request that decide which guarantees and limits apply.

    The traits are backend-neutral; the server derives them once from the request after applying API defaults, and
    [`chat_request_traits`][horde_sdk.generation_parameters.text.chat_policy.chat_request_traits] derives them from a
    request body the same way.
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

    - forwarded tools with a ``required`` choice, or a choice that specifies one function, require
      [`TOOL_CHOICE_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.TOOL_CHOICE_ENFORCED];
      ``tool_choice: none`` requires nothing because the server does not forward the definitions;
    - a strict ``json_schema`` response format requires
      [`STRUCTURED_OUTPUT_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED];
    - every request requires
      [`PROMPT_OVERFLOW_REFUSED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.PROMPT_OVERFLOW_REFUSED].

    Forwarded tools without parallel tool calls do not require
    [`SINGLE_TOOL_CALL_ENFORCED`][horde_sdk.generation_parameters.text.chat_policy.ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED],
    because the server reduces a strict reply's tool calls to the first itself.

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
    if traits.response_format_type is ChatResponseFormatType.JSON_SCHEMA and traits.strict_schema:
        required_guarantees.add(ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED)
    return frozenset(required_guarantees)


class ChatLimitField(StrEnum):
    """Identify one numeric limit a chat worker declares.

    Each value equals a field of
    [`ChatWorkerLimits`][horde_sdk.generation_parameters.text.chat_policy.ChatWorkerLimits] and a key of the
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
) -> ChatLimitField | None:
    """Return the worker limit that would alter a request's values, if any.

    Only limits that depend on request traits are checked here. Context and reply lengths depend on tokenized
    message content and are compared by the server against the declared
    [`MAX_CONTEXT_LENGTH`][horde_sdk.generation_parameters.text.chat_policy.ChatLimitField.MAX_CONTEXT_LENGTH] and
    [`MAX_LENGTH`][horde_sdk.generation_parameters.text.chat_policy.ChatLimitField.MAX_LENGTH].

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
        return ChatLimitField.TOOLS_MAX_TEMPERATURE
    return None


_TOOL_ROLE: Final[str] = "tool"
"""The role of a message answering a tool call."""

_IMAGE_URL_CONTENT_PART_TYPE: Final[str] = "image_url"
"""The content part type carrying an image."""

_TEXT_RESPONSE_FORMAT_TYPE: Final[str] = "text"
"""The unconstrained ``response_format`` type, the same as sending none."""

_PENALTY_FEATURES: Final[tuple[ChatFeature, ...]] = (
    ChatFeature.FREQUENCY_PENALTY,
    ChatFeature.PRESENCE_PENALTY,
)
"""The capabilities whose value equals the request key of the penalty they apply."""


def _tool_choice_mode(tool_choice: object) -> ChatToolChoiceMode:
    """Return the policy mode of a request's ``tool_choice``; an unset choice is OpenAI's ``auto``.

    Raises:
        ValueError: The value is neither an object nor one of OpenAI's mode strings.
    """
    if tool_choice is None:
        return ChatToolChoiceMode.AUTO
    if isinstance(tool_choice, Mapping):
        return ChatToolChoiceMode.FUNCTION
    if isinstance(tool_choice, str) and tool_choice != ChatToolChoiceMode.FUNCTION.value:
        return ChatToolChoiceMode(tool_choice)
    raise ValueError(f"'tool_choice' is not a mode string or a function choice: {tool_choice!r}")


def chat_request_traits(body: Mapping[str, Any]) -> ChatRequestTraits:
    """Derive the traits of an OpenAI chat completions request body, after OpenAI's defaults.

    The derivation matches the server's: ``tool_choice`` and ``parallel_tool_calls`` count only when the request
    offers tools; an unset tool choice is ``auto``; parallel tool calls default to
    [`DEFAULT_PARALLEL_TOOL_CALLS`][horde_sdk.generation_parameters.text.chat_limits.DEFAULT_PARALLEL_TOOL_CALLS]; a
    ``text`` response format is the same as none; an unset temperature is the default in
    [`CHAT_SAMPLING_DEFAULTS`][horde_sdk.generation_parameters.text.chat_limits.CHAT_SAMPLING_DEFAULTS].

    Args:
        body: The request body as a client builds it, such as the keyword arguments of the OpenAI SDK's
            ``chat.completions.create``.

    Returns:
        The request's policy-relevant traits.

    Raises:
        ValueError: ``tool_choice`` or the ``response_format`` type holds a value OpenAI does not define.
    """
    offers_tools = bool(body.get("tools"))
    tool_choice_mode = ChatToolChoiceMode.AUTO
    parallel_tool_calls = DEFAULT_PARALLEL_TOOL_CALLS
    if offers_tools:
        tool_choice_mode = _tool_choice_mode(body.get("tool_choice"))
        requested_parallel_tool_calls = body.get("parallel_tool_calls")
        if requested_parallel_tool_calls is not None:
            parallel_tool_calls = bool(requested_parallel_tool_calls)

    response_format_type: ChatResponseFormatType | None = None
    strict_schema = False
    response_format = body.get("response_format")
    if isinstance(response_format, Mapping) and response_format.get("type") != _TEXT_RESPONSE_FORMAT_TYPE:
        response_format_type = ChatResponseFormatType(str(response_format.get("type")))
        json_schema = response_format.get("json_schema")
        strict_schema = (
            response_format_type is ChatResponseFormatType.JSON_SCHEMA
            and isinstance(json_schema, Mapping)
            and bool(json_schema.get("strict"))
        )

    temperature = body.get("temperature")
    if temperature is None:
        temperature = CHAT_SAMPLING_DEFAULTS["temperature"]

    return ChatRequestTraits(
        offers_tools=offers_tools,
        tool_choice_mode=tool_choice_mode,
        parallel_tool_calls=parallel_tool_calls,
        response_format_type=response_format_type,
        strict_schema=strict_schema,
        temperature=float(temperature),
    )


def chat_request_conformance(body: Mapping[str, Any]) -> ChatConformance:
    """Return the conformance mode a request body selects in ``horde.conformance``.

    Args:
        body: The request body as a client builds it.

    Returns:
        The selected mode, or
        [`DEFAULT_CHAT_CONFORMANCE`][horde_sdk.generation_parameters.text.chat_policy.DEFAULT_CHAT_CONFORMANCE] when
        the body selects none.

    Raises:
        ValueError: ``horde.conformance`` holds a value this SDK release does not define.
    """
    horde_options = body.get("horde")
    if not isinstance(horde_options, Mapping) or horde_options.get("conformance") is None:
        return DEFAULT_CHAT_CONFORMANCE
    return ChatConformance(horde_options["conformance"])


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatRequirements:
    """Represents what a worker must declare to serve one chat request."""

    features: frozenset[ChatFeature]
    """The capabilities the request needs, under every conformance mode."""

    guarantees: frozenset[ChatGuarantee]
    """The guarantees the request needs under its conformance mode; empty under ``best_effort``."""

    conformance: ChatConformance
    """The conformance mode the request selected or defaulted to."""

    traits: ChatRequestTraits
    """The traits the requirements and the trait-dependent limits derive from."""

    @property
    def declarations(self) -> frozenset[str]:
        """Return the capabilities and guarantees together, as the wire values a worker declares."""
        return frozenset(
            {
                *(feature.value for feature in self.features),
                *(guarantee.value for guarantee in self.guarantees),
            },
        )


def _carries_image_part(message: Mapping[str, Any]) -> bool:
    """Return whether a message's content holds an image part."""
    content = message.get("content")
    if not isinstance(content, list):
        return False
    return any(
        isinstance(content_part, Mapping) and content_part.get("type") == _IMAGE_URL_CONTENT_PART_TYPE
        for content_part in content
    )


def _carries_tool_turn(message: Mapping[str, Any]) -> bool:
    """Return whether a message answers a tool call or carries tool calls, which the template has to render."""
    return message.get("role") == _TOOL_ROLE or bool(message.get("tool_calls"))


def chat_request_requirements(body: Mapping[str, Any]) -> ChatRequirements:
    """Derive what a worker must declare to serve an OpenAI chat completions request body.

    The derivation mirrors the server's, so a client's answer and the server's routing agree. A value at its
    documented default needs no capability, so a zero penalty is served by any chat worker. The capabilities are:

    - ``seed`` when a seed is set;
    - ``reasoning_effort`` when a reasoning effort is set, ``none`` included, since a backend that ignores the key
      would reason anyway;
    - each penalty whose value is not zero;
    - ``vision`` when a message carries an ``image_url`` part;
    - ``tools`` when the request forwards tool definitions, or any message is a ``tool`` message or carries tool
      calls, since the worker's template has to render those turns;
    - ``json_object`` or ``json_schema`` by the response format's type;
    - ``tools_with_response_format`` when the request forwards tool definitions and sets a response format.

    The guarantees are those
    [`required_chat_guarantees`][horde_sdk.generation_parameters.text.chat_policy.required_chat_guarantees] derives
    under the body's conformance mode.

    Args:
        body: The request body as a client builds it, such as the keyword arguments of the OpenAI SDK's
            ``chat.completions.create``.

    Returns:
        The capabilities, guarantees, conformance mode and traits of the request.

    Raises:
        ValueError: ``tool_choice``, the ``response_format`` type or ``horde.conformance`` holds a value this SDK
            release does not define.
    """
    traits = chat_request_traits(body)
    conformance = chat_request_conformance(body)
    messages = [message for message in body.get("messages") or () if isinstance(message, Mapping)]

    features: set[ChatFeature] = set()
    if body.get("seed") is not None:
        features.add(ChatFeature.SEED)
    if body.get(ChatFeature.REASONING_EFFORT.value) is not None:
        features.add(ChatFeature.REASONING_EFFORT)
    for penalty_feature in _PENALTY_FEATURES:
        default_penalty = CHAT_SAMPLING_DEFAULTS[penalty_feature.value]
        penalty = body.get(penalty_feature.value)
        if penalty is not None and penalty != default_penalty:
            features.add(penalty_feature)
    if any(_carries_image_part(message) for message in messages):
        features.add(ChatFeature.VISION)
    if traits.forwards_tools or any(_carries_tool_turn(message) for message in messages):
        features.add(ChatFeature.TOOLS)
    if traits.response_format_type is not None:
        features.add(ChatFeature(traits.response_format_type.value))
        if traits.forwards_tools:
            features.add(ChatFeature.TOOLS_WITH_RESPONSE_FORMAT)

    return ChatRequirements(
        features=frozenset(features),
        guarantees=required_chat_guarantees(traits, conformance),
        conformance=conformance,
        traits=traits,
    )


class ChatServiceGapKind(StrEnum):
    """Identify why no worker can serve a chat request, as the server's ``impossible_reason.kind`` reports it."""

    DECLARATION_GAP = "declaration_gap"
    """The workers lack a capability or guarantee the request needs, or apply a declared limit the request exceeds."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatServiceGap:
    """Represents why a set of declarations cannot serve a chat request.

    The fields match the server's chat status ``impossible_reason``, so a client's local answer and the server's
    answer read the same.
    """

    kind: ChatServiceGapKind = ChatServiceGapKind.DECLARATION_GAP
    """The cause."""

    missing_declarations: tuple[str, ...] = ()
    """The capabilities and guarantees the request needs that are not declared, sorted."""

    exceeded_limits: tuple[str, ...] = ()
    """The declared limits the request exceeds, such as ``tools_max_temperature``, sorted."""


def chat_service_gap(
    requirements: ChatRequirements,
    declared: Iterable[str],
    limits: ChatWorkerLimits,
) -> ChatServiceGap | None:
    """Return what keeps a worker's declarations from serving a request, or ``None`` when they serve it.

    ``declared`` is typically a model's declared feature union, as the Horde's model list and the OpenAI-compatible
    front's model cards report it. A union says that some worker declares each value, not that one worker declares
    them all, so ``None`` here is necessary for service and not sufficient.

    The server also reports ``image_transports`` as missing for a worker that declares ``vision`` without a way to
    receive images. A feature list carries no transports, so this check does not report it.

    Args:
        requirements: The request's requirements, from
            [`chat_request_requirements`][horde_sdk.generation_parameters.text.chat_policy.chat_request_requirements].
        declared: The declared capability and guarantee values; values this SDK release does not define are ignored.
        limits: The declared limits checked with
            [`violated_chat_limit`][horde_sdk.generation_parameters.text.chat_policy.violated_chat_limit].

    Returns:
        The missing declarations and exceeded limits, or ``None`` when there are neither.
    """
    missing_declarations = tuple(sorted(requirements.declarations - set(declared)))
    violated_limit = violated_chat_limit(requirements.traits, limits)
    exceeded_limits = () if violated_limit is None else (violated_limit.value,)
    if not missing_declarations and not exceeded_limits:
        return None
    return ChatServiceGap(
        missing_declarations=missing_declarations,
        exceeded_limits=exceeded_limits,
    )
