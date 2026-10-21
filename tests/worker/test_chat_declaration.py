"""Tests for the chat worker's pop declaration, backend fact mapping, submit bodies and job payload reading."""

from __future__ import annotations

from typing import Any

import pytest

from horde_sdk.generation_parameters.text.chat_policy import ChatFeature, ChatGuarantee, ChatWorkerLimits
from horde_sdk.worker.chat_declaration import (
    ChatBackendFacts,
    ChatFaultReason,
    ChatFinishReason,
    ChatImageTransport,
    ChatJobPayload,
    ChatToolStrategy,
    ChatUsage,
    ChatWorkerDeclaration,
    build_chat_fault_submit,
    build_chat_reply_submit,
    declare_from_backend,
)

_LIMITS = ChatWorkerLimits(
    max_context_length=8192,
    max_length=512,
)
"""Limits without a tool temperature cap."""

_GRAMMAR_BACKEND = ChatBackendFacts(
    honours_seed=True,
    renders_tools=True,
    tool_strategy=ChatToolStrategy.GRAMMAR,
    constrains_json_object=True,
    constrains_json_schema=True,
    faults_on_unbuildable_schema=True,
    refuses_prompt_overflow=True,
    serves_tools_with_response_format=True,
)
"""A backend that enforces tool calls and schemas with a grammar and faults instead of degrading."""

_SAMPLING_PAYLOAD: dict[str, Any] = {
    "max_length": 512,
    "max_context_length": 8192,
    "temperature": 1.0,
    "top_p": 1.0,
    "frequency_penalty": 0,
    "presence_penalty": 0,
    "rep_pen": 1.0,
    "top_k": 0,
    "min_p": 0,
    "n": 1,
}
"""The sampling and budget fields every chat job payload carries."""


def test_declaration_round_trips_to_pop_fields() -> None:
    """Every declared value reaches the pop body under the key the server reads, lists sorted."""
    declaration = ChatWorkerDeclaration(
        prompt_jobs=False,
        model_id="koboldcpp/Example-VL",
        features=frozenset({ChatGuarantee.PROMPT_OVERFLOW_REFUSED, ChatFeature.VISION, ChatFeature.SEED}),
        limits=ChatWorkerLimits(max_context_length=8192, max_length=512, tools_max_temperature=1.0),
        image_transports=frozenset({ChatImageTransport.URL, ChatImageTransport.BASE64}),
    )

    assert declaration.to_pop_fields() == {
        "chat_jobs": True,
        "prompt_jobs": False,
        "model_id": "koboldcpp/Example-VL",
        "chat_features": ["prompt_overflow_refused", "seed", "vision"],
        "chat_limits": {"max_context_length": 8192, "max_length": 512, "tools_max_temperature": 1.0},
        "image_transports": ["base64", "url"],
    }


def test_unset_tool_temperature_is_left_out_of_chat_limits() -> None:
    """``tools_max_temperature`` is sent only when the worker has one."""
    declaration = ChatWorkerDeclaration(model_id="m", limits=_LIMITS)

    assert declaration.to_pop_fields()["chat_limits"] == {"max_context_length": 8192, "max_length": 512}


def test_text_only_declaration_withdraws_chat() -> None:
    """A worker that does not accept chat jobs sends only the two job flags."""
    assert ChatWorkerDeclaration(chat_jobs=False).to_pop_fields() == {"chat_jobs": False, "prompt_jobs": True}


@pytest.mark.parametrize(
    "declaration_fields",
    [
        {"chat_jobs": False, "features": frozenset({ChatFeature.SEED})},
        {"chat_jobs": False, "prompt_jobs": False},
        {"model_id": "m", "limits": _LIMITS, "features": frozenset({ChatFeature.VISION})},
        {"limits": _LIMITS},
        {"model_id": "m"},
    ],
)
def test_inconsistent_declarations_are_refused(declaration_fields: dict[str, Any]) -> None:
    """Features without chat jobs, a chat-only worker without chat jobs, vision without a transport, and a chat
    declaration without a model or limits are refused."""
    with pytest.raises(ValueError):
        ChatWorkerDeclaration(**declaration_fields)


def test_limits_below_one_are_refused() -> None:
    """Token limits below 1 cannot describe a working backend."""
    with pytest.raises(ValueError):
        ChatWorkerLimits(max_context_length=0, max_length=512)


def test_grammar_strategy_declares_tool_guarantees() -> None:
    """A grammar-constrained backend that faults instead of degrading declares every guarantee it backs."""
    declaration = declare_from_backend(_GRAMMAR_BACKEND, model_id="m", limits=_LIMITS)

    assert declaration.features == frozenset(
        {
            ChatFeature.SEED,
            ChatFeature.TOOLS,
            ChatFeature.JSON_OBJECT,
            ChatFeature.JSON_SCHEMA,
            ChatFeature.TOOLS_WITH_RESPONSE_FORMAT,
            ChatGuarantee.TOOL_CHOICE_ENFORCED,
            ChatGuarantee.SINGLE_TOOL_CALL_ENFORCED,
            ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED,
            ChatGuarantee.PROMPT_OVERFLOW_REFUSED,
        },
    )


def test_template_strategy_declares_tools_without_tool_guarantees() -> None:
    """Calls parsed from a templated reply are not enforced, so neither tool guarantee is declared."""
    facts = ChatBackendFacts(
        renders_tools=True,
        tool_strategy=ChatToolStrategy.TEMPLATE,
        tools_temperature_cap=1.0,
    )

    declaration = declare_from_backend(facts, model_id="m", limits=_LIMITS)

    assert declaration.features == frozenset({ChatFeature.TOOLS})
    assert declaration.limits is not None
    assert declaration.limits.tools_max_temperature == 1.0


def test_backend_without_tools_declares_no_tool_value() -> None:
    """A backend with no tool strategy declares neither tools nor any tool guarantee, even with a response format."""
    facts = ChatBackendFacts(
        constrains_json_schema=True,
        serves_tools_with_response_format=True,
    )

    declaration = declare_from_backend(facts, model_id="m", limits=_LIMITS)

    assert declaration.features == frozenset({ChatFeature.JSON_SCHEMA})


def test_schema_constraint_without_faulting_does_not_guarantee_structured_output() -> None:
    """A backend that falls back to free text on an unbuildable schema does not declare structured output."""
    facts = ChatBackendFacts(constrains_json_schema=True)

    declaration = declare_from_backend(facts, model_id="m", limits=_LIMITS)

    assert ChatGuarantee.STRUCTURED_OUTPUT_ENFORCED not in declaration.features


def test_exclude_removes_declarations_and_their_transports() -> None:
    """Operator exclusions remove declarations; excluding vision also drops the image transports."""
    facts = ChatBackendFacts(
        reads_images=True,
        image_transports=frozenset({ChatImageTransport.URL}),
        refuses_prompt_overflow=True,
    )

    declaration = declare_from_backend(
        facts,
        model_id="m",
        limits=_LIMITS,
        exclude=[ChatFeature.VISION],
    )

    assert declaration.features == frozenset({ChatGuarantee.PROMPT_OVERFLOW_REFUSED})
    assert declaration.image_transports == frozenset()


def test_operator_temperature_cap_narrows_and_never_widens() -> None:
    """The lower of the backend's and the operator's tool temperature caps applies."""
    facts = ChatBackendFacts(renders_tools=True, tool_strategy=ChatToolStrategy.TEMPLATE, tools_temperature_cap=1.0)

    lower_operator_cap = declare_from_backend(
        facts,
        model_id="m",
        limits=ChatWorkerLimits(max_context_length=8192, max_length=512, tools_max_temperature=0.7),
    )
    higher_operator_cap = declare_from_backend(
        facts,
        model_id="m",
        limits=ChatWorkerLimits(max_context_length=8192, max_length=512, tools_max_temperature=1.5),
    )

    assert lower_operator_cap.limits is not None
    assert lower_operator_cap.limits.tools_max_temperature == 0.7
    assert higher_operator_cap.limits is not None
    assert higher_operator_cap.limits.tools_max_temperature == 1.0


@pytest.mark.parametrize(
    "facts_fields",
    [
        {"reads_images": True},
        {"image_transports": frozenset({ChatImageTransport.URL})},
        {"reads_images": True, "image_transports": frozenset({ChatImageTransport.MESSAGES_URL})},
        {"renders_tools": True},
        {"tool_strategy": ChatToolStrategy.GRAMMAR},
    ],
)
def test_contradicting_facts_are_refused(facts_fields: dict[str, Any]) -> None:
    """Image reading without a transport and tool rendering without a strategy, or the reverse, are refused."""
    with pytest.raises(ValueError):
        ChatBackendFacts(**facts_fields)


def test_a_text_only_backend_may_declare_the_messages_url_transport() -> None:
    """``messages_url`` delivers offloaded messages, which a backend that reads no images also receives."""
    facts = ChatBackendFacts(image_transports=frozenset({ChatImageTransport.MESSAGES_URL}))

    assert facts.reads_images is False


def test_fault_submit_shape() -> None:
    """A fault submit carries the job, the faulted state, the model and the reason value."""
    assert build_chat_fault_submit("job-1", "m", ChatFaultReason.PROMPT_OVERFLOW) == {
        "id": "job-1",
        "state": "faulted",
        "model_id": "m",
        "fault_reason": "prompt_overflow",
    }


def test_fault_reason_values_are_the_server_vocabulary() -> None:
    """The five fault reasons hold the exact values the server stores a message for."""
    assert {reason.value for reason in ChatFaultReason} == {
        "prompt_overflow",
        "unbuildable_grammar",
        "tool_violation",
        "reply_refused",
        "generation_error",
    }


def test_reply_submit_shape_with_tool_calls_and_usage() -> None:
    """A tool call reply carries an assistant message, the finish reason and the reported counts."""
    tool_call = {"id": "call_1", "type": "function", "function": {"name": "f", "arguments": "{}"}}

    submit_body = build_chat_reply_submit(
        "job-1",
        "m",
        {"content": None, "tool_calls": [tool_call]},
        ChatFinishReason.TOOL_CALLS,
        ChatUsage(prompt_tokens=10),
        native_finish_reason="eos",
    )

    assert submit_body == {
        "id": "job-1",
        "model_id": "m",
        "message": {"role": "assistant", "content": None, "tool_calls": [tool_call]},
        "finish_reason": "tool_calls",
        "native_finish_reason": "eos",
        "prompt_tokens": 10,
    }


def test_reply_submit_carries_reasoning_beside_the_content_and_its_count() -> None:
    """Reasoning travels in its own field, never inside ``content``."""
    submit_body = build_chat_reply_submit(
        "job-1",
        "m",
        {"content": "Blue.", "reasoning_content": "The user asked for a colour."},
        ChatFinishReason.STOP,
        ChatUsage(completion_tokens=12, reasoning_tokens=9),
    )

    assert submit_body == {
        "id": "job-1",
        "model_id": "m",
        "message": {"role": "assistant", "content": "Blue.", "reasoning_content": "The user asked for a colour."},
        "finish_reason": "stop",
        "completion_tokens": 12,
        "reasoning_tokens": 9,
    }


def test_text_reply_submit_shape() -> None:
    """A text reply without usage carries only the required keys; an empty content is a completed reply."""
    assert build_chat_reply_submit("job-1", "m", {"content": ""}, ChatFinishReason.STOP) == {
        "id": "job-1",
        "model_id": "m",
        "message": {"role": "assistant", "content": ""},
        "finish_reason": "stop",
    }


@pytest.mark.parametrize(
    ("message", "finish_reason"),
    [
        ({"content": None}, ChatFinishReason.STOP),
        ({"content": "text"}, ChatFinishReason.TOOL_CALLS),
    ],
)
def test_reply_the_server_refuses_is_not_built(message: dict[str, Any], finish_reason: ChatFinishReason) -> None:
    """A reply without content or calls, and a ``tool_calls`` finish without calls, are refused locally."""
    with pytest.raises(ValueError):
        build_chat_reply_submit("job-1", "m", message, finish_reason)


def test_tools_job_payload_is_read_with_its_requirements() -> None:
    """A narrowed tool job exposes its tool keys and needs the tools capability."""
    tool = {"type": "function", "function": {"name": "get_weather"}}
    job = {
        "id": "job-1",
        "model": "m",
        "chat": True,
        "payload": {
            **_SAMPLING_PAYLOAD,
            "messages": [{"role": "user", "content": "Weather?"}],
            "tools": [tool],
            "tool_choice": "required",
            "stop_sequence": ["\n\n"],
            "seed": 3,
        },
    }

    chat_job = ChatJobPayload.from_pop(job)

    assert chat_job.job_id == "job-1"
    assert chat_job.tools == (tool,)
    assert chat_job.tool_choice == "required"
    assert chat_job.stop_sequence == ("\n\n",)
    assert chat_job.requirements.features == frozenset({ChatFeature.TOOLS, ChatFeature.SEED})
    declaration = declare_from_backend(
        ChatBackendFacts(renders_tools=True, tool_strategy=ChatToolStrategy.TEMPLATE),
        model_id="m",
        limits=_LIMITS,
    )
    assert chat_job.undeclared_features(declaration) == frozenset({ChatFeature.SEED})


def test_vision_job_payload_needs_vision() -> None:
    """An image job needs vision, which a declaration with a transport covers."""
    job = {
        "id": "job-2",
        "model": "m",
        "chat": True,
        "payload": {
            **_SAMPLING_PAYLOAD,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is this?"},
                        {"type": "image_url", "image_url": {"url": "https://example.com/signed"}},
                    ],
                },
            ],
        },
    }
    declaration = ChatWorkerDeclaration(
        model_id="m",
        limits=_LIMITS,
        features=frozenset({ChatFeature.VISION}),
        image_transports=frozenset({ChatImageTransport.URL}),
    )

    chat_job = ChatJobPayload.from_pop(job)

    assert chat_job.tools is None
    assert chat_job.requirements.features == frozenset({ChatFeature.VISION})
    assert chat_job.undeclared_features(declaration) == frozenset()


def test_text_job_is_not_read_as_chat() -> None:
    """A pop response without ``chat: true`` is a text job."""
    with pytest.raises(ValueError):
        ChatJobPayload.from_pop({"id": "job-3", "payload": {"prompt": "Hi"}})
