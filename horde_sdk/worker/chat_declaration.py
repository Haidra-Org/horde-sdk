"""Typed builders over the AI-Horde text chat pop and submit contract, for a worker that serves chat jobs.

A chat worker declares on each text pop what its backend supports
([`ChatWorkerDeclaration`][horde_sdk.worker.chat_declaration.ChatWorkerDeclaration]), reads a popped chat job
([`ChatJobPayload`][horde_sdk.worker.chat_declaration.ChatJobPayload]) and submits either the reply
([`build_chat_reply_submit`][horde_sdk.worker.chat_declaration.build_chat_reply_submit]) or a fault
([`build_chat_fault_submit`][horde_sdk.worker.chat_declaration.build_chat_fault_submit]).
[`declare_from_backend`][horde_sdk.worker.chat_declaration.declare_from_backend] maps what a backend does to what it
may declare, so each worker does not re-derive which facts back which guarantee.

The capability, guarantee and limit vocabulary lives in
[`horde_sdk.generation_parameters.text.chat_policy`][horde_sdk.generation_parameters.text.chat_policy].
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from strenum import StrEnum

from horde_sdk.generation_parameters.text.chat_policy import (
    ChatFeature,
    ChatGuarantee,
    ChatRequirements,
    ChatWorkerLimits,
    chat_request_requirements,
)

__all__ = [
    "IMAGE_PART_TRANSPORTS",
    "ChatBackendFacts",
    "ChatFaultReason",
    "ChatFinishReason",
    "ChatImageTransport",
    "ChatJobPayload",
    "ChatToolStrategy",
    "ChatUsage",
    "ChatWorkerDeclaration",
    "build_chat_fault_submit",
    "build_chat_reply_submit",
    "declare_from_backend",
]


class ChatImageTransport(StrEnum):
    """Identify how a worker accepts a chat job's images and messages, declared in ``image_transports`` on pop."""

    URL = "url"
    """The worker fetches a signed object storage URL for each image. Preferred whenever a worker declares it."""

    BASE64 = "base64"
    """The worker reads a ``data:image/jpeg;base64,`` URL inlined in the pop response."""

    MESSAGES_URL = "messages_url"
    """The worker fetches the whole ``messages`` array, images inlined as ``data:image/jpeg;base64,`` URLs, from the
    signed object storage URL in the payload's ``messages_url``, which then replaces ``messages``. The server sends it
    only for a request whose messages it stored as one object, so a worker declares it beside ``url`` or ``base64``
    rather than in their place. The body is JSON served either plain or with ``Content-Encoding: gzip``; the fetcher
    honours the header."""


IMAGE_PART_TRANSPORTS: Final[frozenset[ChatImageTransport]] = frozenset(
    {
        ChatImageTransport.URL,
        ChatImageTransport.BASE64,
    },
)
"""The transports that deliver every image part. ``messages_url`` applies only to requests whose messages the server
offloaded, so it alone does not let a worker receive images."""


class ChatToolStrategy(StrEnum):
    """Identify how a backend produces tool calls, which decides the tool guarantees it may declare."""

    GRAMMAR = "grammar"
    """The backend constrains calls with a grammar and selects the tool itself, so it enforces ``tool_choice`` and a
    single call."""

    TEMPLATE = "template"
    """The model's chat template renders the tools and calls are parsed from the reply afterwards, so nothing
    enforces ``tool_choice`` or the call count."""

    NONE = "none"
    """The backend does not serve tools."""


class ChatFaultReason(StrEnum):
    """Why a worker faulted a chat job, sent as ``fault_reason`` with its ``faulted`` submit."""

    PROMPT_OVERFLOW = "prompt_overflow"
    """The rendered messages did not fit the worker's context."""

    UNBUILDABLE_GRAMMAR = "unbuildable_grammar"
    """The worker could not build the grammar that enforces the request's ``tool_choice`` or ``response_format``."""

    TOOL_VIOLATION = "tool_violation"
    """The model's reply broke the request's tool controls, and the worker discarded it rather than submit it."""

    REPLY_REFUSED = "reply_refused"
    """The Horde refused the worker's reply. The refusal's own message is kept when the Horde recorded one."""

    GENERATION_ERROR = "generation_error"
    """The backend failed while generating."""


class ChatFinishReason(StrEnum):
    """Why a worker stopped generating a chat reply, normalised by the worker on submit."""

    STOP = "stop"
    """The model ended the reply or hit a stop sequence."""

    LENGTH = "length"
    """Generation reached ``max_length``."""

    CONTENT_FILTER = "content_filter"
    """The backend withheld or cut the reply on a content rule."""

    TOOL_CALLS = "tool_calls"
    """The model called one or more tools; the submitted message carries them."""


_FAULTED_STATE: Final[str] = "faulted"
"""The submit ``state`` of a job the worker could not complete."""

_ASSISTANT_ROLE: Final[str] = "assistant"
"""The role of every submitted reply."""


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatWorkerDeclaration:
    """Represents what a worker declares about chat jobs on a text pop.

    ``model_id`` has to be one of the pop's ``models``. A worker whose declaration changes sends the new one on its
    next pop; a pop without ``chat_jobs`` withdraws the declaration.
    """

    chat_jobs: bool = True
    """Whether the worker accepts chat jobs."""

    prompt_jobs: bool = True
    """Whether the worker accepts text jobs; ``False`` makes the worker chat-only and needs ``chat_jobs``."""

    model_id: str | None = None
    """The model the worker serves chat jobs with; required with ``chat_jobs``."""

    features: frozenset[ChatFeature | ChatGuarantee] = frozenset()
    """The capabilities and guarantees the worker declares."""

    limits: ChatWorkerLimits | None = None
    """The limits chat jobs run under; required with ``chat_jobs``. The text pop's limits bound only text jobs."""

    image_transports: frozenset[ChatImageTransport] = frozenset()
    """How the worker receives images; required with ``vision``."""

    def __post_init__(self) -> None:
        """Refuse a declaration the server would refuse or that declares something the worker cannot receive.

        Raises:
            ValueError: The declaration is inconsistent.
        """
        if not self.prompt_jobs and not self.chat_jobs:
            raise ValueError("A worker that refuses text jobs has to accept chat jobs.")
        if not self.chat_jobs:
            if self.features or self.image_transports or self.model_id is not None or self.limits is not None:
                raise ValueError("A worker that does not accept chat jobs declares no chat model, feature or limit.")
            return
        if not self.model_id:
            raise ValueError("A chat worker has to declare the model it serves chat jobs with.")
        if self.limits is None:
            raise ValueError("A chat worker has to declare the limits its chat jobs run under.")
        if ChatFeature.VISION in self.features and not self.image_transports & IMAGE_PART_TRANSPORTS:
            raise ValueError("A worker that declares vision has to declare the url or base64 image transport.")

    def to_pop_fields(self) -> dict[str, Any]:
        """Return the chat fields of a text pop body, keyed as the AI-Horde text pop reads them.

        Returns:
            ``chat_jobs`` and ``prompt_jobs``, and with chat jobs ``model_id``, ``chat_features`` as a sorted list,
            ``chat_limits`` with ``tools_max_temperature`` only when set, and ``image_transports`` as a sorted list.
        """
        pop_fields: dict[str, Any] = {
            "chat_jobs": self.chat_jobs,
            "prompt_jobs": self.prompt_jobs,
        }
        if not self.chat_jobs or self.limits is None:
            return pop_fields
        chat_limits: dict[str, int | float] = {
            "max_context_length": self.limits.max_context_length,
            "max_length": self.limits.max_length,
        }
        if self.limits.tools_max_temperature is not None:
            chat_limits["tools_max_temperature"] = self.limits.tools_max_temperature
        pop_fields["model_id"] = self.model_id
        pop_fields["chat_features"] = sorted(declaration.value for declaration in self.features)
        pop_fields["chat_limits"] = chat_limits
        pop_fields["image_transports"] = sorted(transport.value for transport in self.image_transports)
        return pop_fields


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatBackendFacts:
    """Represents what a chat backend does, from which the declarations it may make follow.

    Every fact defaults to the conservative answer, so a worker author sets only what the backend implements.
    """

    honours_seed: bool = False
    """The backend applies a sampling seed."""

    applies_presence_penalty: bool = False
    """The backend applies OpenAI's presence penalty."""

    applies_frequency_penalty: bool = False
    """The backend applies OpenAI's frequency penalty."""

    reads_images: bool = False
    """The loaded model reads image parts; needs ``url`` or ``base64`` in ``image_transports``."""

    image_transports: frozenset[ChatImageTransport] = frozenset()
    """How the worker receives images."""

    renders_tools: bool = False
    """The worker renders tool definitions and tool turns and submits the model's tool calls; needs a
    ``tool_strategy`` other than ``none``."""

    tool_strategy: ChatToolStrategy = ChatToolStrategy.NONE
    """How the backend produces tool calls."""

    constrains_json_object: bool = False
    """The backend constrains the reply to a JSON object."""

    constrains_json_schema: bool = False
    """The backend constrains the reply to a client JSON Schema."""

    faults_on_unbuildable_schema: bool = False
    """The worker faults a job whose schema the backend cannot apply, rather than falling back to free text."""

    refuses_prompt_overflow: bool = False
    """The worker faults a job whose rendered prompt does not fit, rather than trimming it."""

    serves_tools_with_response_format: bool = False
    """The backend applies a response format to the final answer and not to tool calls when both are set."""

    tools_temperature_cap: float | None = None
    """The temperature the backend clamps to when tools are present; ``None`` when it applies any temperature."""

    def __post_init__(self) -> None:
        """Refuse facts that contradict each other.

        Raises:
            ValueError: Image reading and transports, or tool rendering and the tool strategy, disagree.
        """
        if self.reads_images != bool(self.image_transports & IMAGE_PART_TRANSPORTS):
            raise ValueError("A backend reads images exactly when the worker has the url or base64 image transport.")
        if self.renders_tools != (self.tool_strategy is not ChatToolStrategy.NONE):
            raise ValueError("A backend renders tools exactly when it has a tool strategy.")


def declare_from_backend(
    facts: ChatBackendFacts,
    *,
    model_id: str,
    limits: ChatWorkerLimits,
    prompt_jobs: bool = True,
    exclude: Iterable[ChatFeature | ChatGuarantee] = (),
) -> ChatWorkerDeclaration:
    """Return the chat declaration a backend's facts support.

    A guarantee is declared only when the fact that backs it is true:

    - ``tool_choice_enforced`` and ``single_tool_call_enforced`` need the ``grammar`` tool strategy;
    - ``structured_output_enforced`` needs ``constrains_json_schema`` and ``faults_on_unbuildable_schema``;
    - ``prompt_overflow_refused`` needs ``refuses_prompt_overflow``.

    Each capability follows its fact, and ``tools_with_response_format`` also needs tools and a JSON constraint.

    Operator configuration may remove declarations and never add them: ``exclude`` drops values from the result, and
    there is no parameter that adds one. A tool temperature cap in ``limits`` narrows the backend's cap and never
    widens it: the lower of the two applies.

    Args:
        facts: What the backend does.
        model_id: The model the worker serves chat jobs with; one of the pop's ``models``.
        limits: The context and reply lengths chat jobs run under, with an optional operator tool temperature cap.
        prompt_jobs: Whether the worker also accepts text jobs.
        exclude: Capabilities and guarantees the operator withholds.

    Returns:
        The declaration to send on each pop.
    """
    backed_declarations: dict[ChatFeature | ChatGuarantee, bool] = {
        ChatFeature.SEED: facts.honours_seed,
        ChatFeature.PRESENCE_PENALTY: facts.applies_presence_penalty,
        ChatFeature.FREQUENCY_PENALTY: facts.applies_frequency_penalty,
        ChatFeature.VISION: facts.reads_images,
        ChatFeature.TOOLS: facts.renders_tools,
        ChatFeature.JSON_OBJECT: facts.constrains_json_object,
        ChatFeature.JSON_SCHEMA: facts.constrains_json_schema,
        ChatFeature.TOOLS_WITH_RESPONSE_FORMAT: (
            facts.serves_tools_with_response_format
            and facts.renders_tools
            and (facts.constrains_json_object or facts.constrains_json_schema)
        ),
        ChatGuarantee.TOOL_CHOICE_ENFORCED: facts.tool_strategy is ChatToolStrategy.GRAMMAR,
        ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED: facts.tool_strategy is ChatToolStrategy.GRAMMAR,
        ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED: facts.constrains_json_schema and facts.faults_on_unbuildable_schema,
        ChatGuarantee.PROMPT_OVERFLOW_REFUSED: facts.refuses_prompt_overflow,
    }
    excluded = frozenset(exclude)
    features = frozenset(
        declaration
        for declaration, is_backed in backed_declarations.items()
        if is_backed and declaration not in excluded
    )

    temperature_caps = [
        temperature_cap
        for temperature_cap in (facts.tools_temperature_cap, limits.tools_max_temperature)
        if temperature_cap is not None
    ]
    return ChatWorkerDeclaration(
        prompt_jobs=prompt_jobs,
        model_id=model_id,
        features=features,
        limits=dataclasses.replace(limits, tools_max_temperature=min(temperature_caps, default=None)),
        image_transports=facts.image_transports if ChatFeature.VISION in features else frozenset(),
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatUsage:
    """Represents the token counts a backend reported for a chat reply; omit a count the backend did not report."""

    prompt_tokens: int | None = None
    """The tokens of the rendered prompt."""

    completion_tokens: int | None = None
    """The tokens of the reply."""


def build_chat_fault_submit(job_id: str, model_id: str, reason: ChatFaultReason) -> dict[str, Any]:
    """Return the submit body of a chat job the worker faulted.

    The Horde stores its own sentence for ``reason`` and never text from the worker.

    Args:
        job_id: The popped job's ``id``.
        model_id: The declared ``model_id`` the job was assigned under.
        reason: Why the worker faulted the job.

    Returns:
        ``id``, ``state`` ``faulted``, ``model_id`` and ``fault_reason``.
    """
    return {
        "id": job_id,
        "state": _FAULTED_STATE,
        "model_id": model_id,
        "fault_reason": reason.value,
    }


def build_chat_reply_submit(
    job_id: str,
    model_id: str,
    message: Mapping[str, Any],
    finish_reason: ChatFinishReason,
    usage: ChatUsage | None = None,
    *,
    native_finish_reason: str | None = None,
) -> dict[str, Any]:
    """Return the submit body of a completed chat reply.

    Args:
        job_id: The popped job's ``id``.
        model_id: The declared ``model_id`` the job was assigned under.
        message: The reply: ``content`` (a string, or null only with tool calls) and optional ``tool_calls`` as the
            backend minted them. The role is always ``assistant``.
        finish_reason: Why the backend stopped.
        usage: The token counts the backend reported, if any.
        native_finish_reason: The backend's own finish reason, at most 32 characters.

    Returns:
        ``id``, ``model_id``, ``message``, ``finish_reason`` and whichever of ``native_finish_reason``,
        ``prompt_tokens`` and ``completion_tokens`` are known.

    Raises:
        ValueError: The reply has neither content nor tool calls, or finishes with ``tool_calls`` without any.
    """
    content = message.get("content")
    tool_calls = message.get("tool_calls")
    if content is None and not tool_calls:
        raise ValueError("A chat reply carries content, tool calls or both.")
    if finish_reason is ChatFinishReason.TOOL_CALLS and not tool_calls:
        raise ValueError("A reply that finishes with 'tool_calls' has to carry tool calls.")

    submitted_message: dict[str, Any] = {
        "role": _ASSISTANT_ROLE,
        "content": content,
    }
    if tool_calls:
        submitted_message["tool_calls"] = [dict(tool_call) for tool_call in tool_calls]
    submit_body: dict[str, Any] = {
        "id": job_id,
        "model_id": model_id,
        "message": submitted_message,
        "finish_reason": finish_reason.value,
    }
    if native_finish_reason is not None:
        submit_body["native_finish_reason"] = native_finish_reason
    if usage is not None and usage.prompt_tokens is not None:
        submit_body["prompt_tokens"] = usage.prompt_tokens
    if usage is not None and usage.completion_tokens is not None:
        submit_body["completion_tokens"] = usage.completion_tokens
    return submit_body


def _optional_tuple(value: object) -> tuple[Any, ...] | None:
    """Return a JSON array as a tuple, or ``None`` when the key is absent."""
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise ValueError(f"Expected a JSON array, got {value!r}.")
    return tuple(value)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatJobPayload:
    """Represents a popped chat job as a worker reads it.

    The tool keys are the ones the server forwards after narrowing them: under ``tool_choice: none`` none of them is
    sent, and a choice that specifies one function arrives as that one tool with ``tool_choice: required``.

    The pop payload carries no conformance mode today, so ``requirements`` is derived as for a ``strict`` request and
    its guarantees may exceed what a ``best_effort`` job needed. Capabilities apply under every mode, so
    [`undeclared_features`][horde_sdk.worker.chat_declaration.ChatJobPayload.undeclared_features] checks only those.
    """

    job_id: str | None
    """The job's ``id``, which the submit echoes."""

    model: str | None
    """The model the job was popped for."""

    messages: tuple[Mapping[str, Any], ...]
    """The conversation, oldest message first, with tool turns and image parts as stored."""

    tools: tuple[Mapping[str, Any], ...] | None
    """The tool definitions forwarded, or ``None``."""

    tool_choice: str | Mapping[str, Any] | None
    """The forwarded ``tool_choice``, or ``None`` for OpenAI's ``auto``."""

    parallel_tool_calls: bool | None
    """The forwarded ``parallel_tool_calls``, or ``None`` for OpenAI's default."""

    response_format: Mapping[str, Any] | None
    """The forwarded response format, or ``None`` for free text."""

    max_length: int
    """The most tokens to generate."""

    max_context_length: int
    """The context the rendered prompt has to fit; a worker faults a job that does not fit."""

    temperature: float
    """The sampling temperature."""

    top_p: float
    """The nucleus sampling probability."""

    frequency_penalty: float
    """OpenAI's frequency penalty."""

    presence_penalty: float
    """OpenAI's presence penalty."""

    rep_pen: float
    """The repetition penalty, neutral unless a native caller set it."""

    top_k: int
    """The top-k sampling bound, neutral unless a native caller set it."""

    min_p: float
    """The min-p sampling bound, neutral unless a native caller set it."""

    stop_sequence: tuple[str, ...] | None
    """The stop sequences, or ``None`` when the client sent none."""

    seed: int | None
    """The sampling seed, or ``None`` when the client sent none."""

    requirements: ChatRequirements
    """What the job needs, derived from the payload as for a ``strict`` request."""

    @classmethod
    def from_pop(cls, job: Mapping[str, Any]) -> ChatJobPayload:
        """Read a chat job from a text pop response.

        Args:
            job: The pop response of a chat job, which carries ``chat: true`` and the job under ``payload``.

        Returns:
            The typed job.

        Raises:
            ValueError: The response is not a chat job or its payload is malformed.
            KeyError: The payload lacks a field the server always sends.
        """
        if job.get("chat") is not True:
            raise ValueError("The pop response is not a chat job.")
        payload = job["payload"]
        if not isinstance(payload, Mapping):
            raise ValueError("A chat job's payload is a JSON object.")

        stop_sequence = _optional_tuple(payload.get("stop_sequence"))
        return cls(
            job_id=job.get("id"),
            model=job.get("model"),
            messages=_optional_tuple(payload["messages"]) or (),
            tools=_optional_tuple(payload.get("tools")),
            tool_choice=payload.get("tool_choice"),
            parallel_tool_calls=payload.get("parallel_tool_calls"),
            response_format=payload.get("response_format"),
            max_length=payload["max_length"],
            max_context_length=payload["max_context_length"],
            temperature=payload["temperature"],
            top_p=payload["top_p"],
            frequency_penalty=payload["frequency_penalty"],
            presence_penalty=payload["presence_penalty"],
            rep_pen=payload["rep_pen"],
            top_k=payload["top_k"],
            min_p=payload["min_p"],
            stop_sequence=stop_sequence,
            seed=payload.get("seed"),
            requirements=chat_request_requirements(payload),
        )

    def undeclared_features(self, declaration: ChatWorkerDeclaration) -> frozenset[ChatFeature]:
        """Return the capabilities the job needs that ``declaration`` does not declare.

        The server routes a job only to a worker that declares what it needs, so a non-empty result points at a
        routing fault, and the worker can fault the job before generating instead of returning a reply that ignores
        part of the request.

        Args:
            declaration: The declaration the worker sent on the pop that returned this job.

        Returns:
            The undeclared capabilities; empty when the worker can serve the job.
        """
        return frozenset(self.requirements.features - declaration.features)
