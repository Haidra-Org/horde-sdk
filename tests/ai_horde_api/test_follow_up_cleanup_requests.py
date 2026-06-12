"""Tests that every follow-up-requiring response type can construct its failure-cleanup requests.

The session clients build these cleanup requests eagerly after every *successful* response. A
response type with broken cleanup definitions therefore used to destroy successful responses
(e.g. a worker's popped alchemy forms were silently dropped after the pop succeeded server-side).
These tests construct a populated instance of every `ResponseRequiringFollowUpMixin` subclass and
exercise the same call the sessions make.
"""

import uuid
from collections.abc import Callable
from typing import override

import pytest

from horde_sdk.ai_horde_api.apimodels import (
    AlchemyAsyncResponse,
    AlchemyDeleteRequest,
    AlchemyJobPopResponse,
    AlchemyJobSubmitRequest,
    AlchemyPopFormPayload,
    DeleteImageGenerateRequest,
    DeleteTextGenerateRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateJobPopPayload,
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
    ImageGenerationJobSubmitRequest,
    ModelPayloadKobold,
    TextGenerateAsyncResponse,
    TextGenerateJobPopResponse,
    TextGenerationJobSubmitRequest,
)
from horde_sdk.ai_horde_api.consts import GENERATION_STATE
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.generic_api.apimodels import (
    HordeRequest,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)
from horde_sdk.generic_api.generic_clients import _build_cleanup_requests_safely

_EXAMPLE_ID = str(uuid.UUID("00000000-0000-0000-0000-000000000001"))
_EXAMPLE_ID_2 = str(uuid.UUID("00000000-0000-0000-0000-000000000002"))


def _image_async_response() -> ImageGenerateAsyncResponse:
    return ImageGenerateAsyncResponse.model_validate({"id": _EXAMPLE_ID, "kudos": 10.0})


def _image_pop_response() -> ImageGenerateJobPopResponse:
    return ImageGenerateJobPopResponse(
        id=_EXAMPLE_ID,
        ids=[_EXAMPLE_ID],
        payload=ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="1234"),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )


def _text_async_response() -> TextGenerateAsyncResponse:
    return TextGenerateAsyncResponse.model_validate({"id": _EXAMPLE_ID, "kudos": 10.0})


def _text_pop_response() -> TextGenerateJobPopResponse:
    return TextGenerateJobPopResponse(
        payload=ModelPayloadKobold(prompt="tell me about a cat in a hat"),
        id=_EXAMPLE_ID,
        ids=[_EXAMPLE_ID],
        model="some_text_model",
    )


def _alchemy_async_response() -> AlchemyAsyncResponse:
    return AlchemyAsyncResponse.model_validate({"id": _EXAMPLE_ID})


def _alchemy_pop_response() -> AlchemyJobPopResponse:
    return AlchemyJobPopResponse(
        forms=[
            AlchemyPopFormPayload(id=_EXAMPLE_ID, form=KNOWN_ALCHEMY_TYPES.caption),
            AlchemyPopFormPayload(id=_EXAMPLE_ID_2, form=KNOWN_ALCHEMY_TYPES.nsfw),
        ],
    )


_COVERED_RESPONSE_TYPES: dict[
    type[ResponseRequiringFollowUpMixin],
    tuple[Callable[[], ResponseRequiringFollowUpMixin], type[HordeRequest], int],
] = {
    ImageGenerateAsyncResponse: (_image_async_response, DeleteImageGenerateRequest, 1),
    ImageGenerateJobPopResponse: (_image_pop_response, ImageGenerationJobSubmitRequest, 1),
    TextGenerateAsyncResponse: (_text_async_response, DeleteTextGenerateRequest, 1),
    TextGenerateJobPopResponse: (_text_pop_response, TextGenerationJobSubmitRequest, 1),
    AlchemyAsyncResponse: (_alchemy_async_response, AlchemyDeleteRequest, 1),
    AlchemyJobPopResponse: (_alchemy_pop_response, AlchemyJobSubmitRequest, 2),
}


def _all_concrete_follow_up_response_types() -> set[type[ResponseRequiringFollowUpMixin]]:
    discovered: set[type[ResponseRequiringFollowUpMixin]] = set()
    stack: list[type[ResponseRequiringFollowUpMixin]] = list(ResponseRequiringFollowUpMixin.__subclasses__())
    while stack:
        subclass = stack.pop()
        stack.extend(subclass.__subclasses__())
        if subclass.__module__.startswith("horde_sdk"):
            discovered.add(subclass)
    return discovered


def test_all_follow_up_response_types_are_covered() -> None:
    """Force a cleanup-construction test to be added for any new follow-up-requiring response type."""
    uncovered = _all_concrete_follow_up_response_types() - set(_COVERED_RESPONSE_TYPES)
    assert not uncovered, (
        "These ResponseRequiringFollowUpMixin subclasses have no failure-cleanup construction test; "
        f"add them to _COVERED_RESPONSE_TYPES in this file: {sorted(t.__name__ for t in uncovered)}"
    )


@pytest.mark.parametrize(
    ("response_type", "factory", "expected_cleanup_type", "expected_count"),
    [
        (response_type, factory, expected_cleanup_type, expected_count)
        for response_type, (factory, expected_cleanup_type, expected_count) in _COVERED_RESPONSE_TYPES.items()
    ],
    ids=[response_type.__name__ for response_type in _COVERED_RESPONSE_TYPES],
)
def test_failure_cleanup_requests_construct(
    response_type: type[ResponseRequiringFollowUpMixin],
    factory: Callable[[], ResponseRequiringFollowUpMixin],
    expected_cleanup_type: type[HordeRequest],
    expected_count: int,
) -> None:
    """Exercise the same eager construction the session clients perform after a successful response."""
    response = factory()
    assert not response.ignore_failure()

    cleanup_requests = response.get_follow_up_failure_cleanup_request()

    assert len(cleanup_requests) == expected_count
    for cleanup_request in cleanup_requests:
        assert isinstance(cleanup_request, expected_cleanup_type)


def test_alchemy_pop_cleanup_is_faulted_submit() -> None:
    response = _alchemy_pop_response()
    cleanup_requests = response.get_follow_up_failure_cleanup_request()

    submit_requests = [request for request in cleanup_requests if isinstance(request, AlchemyJobSubmitRequest)]
    assert len(submit_requests) == len(cleanup_requests)

    for submit_request in submit_requests:
        assert submit_request.state == GENERATION_STATE.faulted
        assert submit_request.result == {}

    assert {str(submit_request.id_) for submit_request in submit_requests} == {_EXAMPLE_ID, _EXAMPLE_ID_2}


def test_text_pop_cleanup_is_faulted_submit() -> None:
    response = _text_pop_response()
    cleanup_requests = response.get_follow_up_failure_cleanup_request()

    assert len(cleanup_requests) == 1
    cleanup_request = cleanup_requests[0]
    assert isinstance(cleanup_request, TextGenerationJobSubmitRequest)
    assert cleanup_request.state == GENERATION_STATE.faulted
    assert str(cleanup_request.id_) == _EXAMPLE_ID


def test_text_pop_cleanup_falls_back_to_ids() -> None:
    response = TextGenerateJobPopResponse(
        payload=ModelPayloadKobold(prompt="tell me about a cat in a hat"),
        ids=[_EXAMPLE_ID, _EXAMPLE_ID_2],
        model="some_text_model",
    )
    assert not response.ignore_failure()

    cleanup_requests = response.get_follow_up_failure_cleanup_request()

    submit_requests = [request for request in cleanup_requests if isinstance(request, TextGenerationJobSubmitRequest)]
    assert len(submit_requests) == len(cleanup_requests)
    assert {str(submit_request.id_) for submit_request in submit_requests} == {_EXAMPLE_ID, _EXAMPLE_ID_2}


def test_empty_pops_ignore_failure() -> None:
    """Pops that returned no work have nothing to clean up and must not try to build cleanup requests."""
    empty_alchemy_pop = AlchemyJobPopResponse(forms=None)
    assert empty_alchemy_pop.ignore_failure()
    assert empty_alchemy_pop.get_follow_up_failure_cleanup_request() == []

    empty_text_pop = TextGenerateJobPopResponse(payload=ModelPayloadKobold(), ids=[])
    assert empty_text_pop.ignore_failure()
    assert empty_text_pop.get_follow_up_failure_cleanup_request() == []


class _BrokenFollowUpResponse(HordeResponseBaseModel, ResponseRequiringFollowUpMixin):
    """A response type whose cleanup definitions are broken the same way AlchemyJobPopResponse's once were:

    the declared cleanup request type cannot be built from the params the response provides.
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        return [{"id": _EXAMPLE_ID}]

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[AlchemyJobSubmitRequest]:
        return AlchemyJobSubmitRequest


def test_broken_cleanup_definitions_do_not_propagate() -> None:
    """The session-side guard must swallow cleanup-construction errors so successful responses survive."""
    broken_response = _BrokenFollowUpResponse()

    with pytest.raises(Exception, match="validation error"):
        broken_response.get_follow_up_failure_cleanup_request()

    assert _build_cleanup_requests_safely(broken_response) is None
