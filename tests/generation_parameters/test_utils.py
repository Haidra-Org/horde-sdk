from __future__ import annotations

from enum import Enum
from uuid import UUID

import pytest

from horde_sdk.generation_parameters.generic import CompositeParametersBase
from horde_sdk.generation_parameters.utils import (
    ResultIdAllocator,
    compute_parameter_fingerprint,
    ensure_result_id,
    ensure_result_ids,
    finalize_template_for_parameters,
    resolve_result_id_from_payload,
    resolve_result_ids_from_payload,
)


class SampleEnum(Enum):
    """Enum used to validate fingerprint normalisation."""

    FIRST = "first"
    SECOND = 2


class _SimpleTemplate(CompositeParametersBase):
    value: int = 1
    result_id: str | None = None
    result_ids: list[str] | None = None

    def get_number_expected_results(self) -> int:  # pragma: no cover - simple return
        return 1


def test_compute_parameter_fingerprint_deterministic_order() -> None:
    """The fingerprint should stay stable regardless of mapping iteration order."""

    payload_one = {
        "list": [1, {"value": SampleEnum.FIRST}],
        "mapping": {"alpha": True, "beta": 3},
        "number": 42,
    }
    payload_two = {
        "number": 42,
        "mapping": {"beta": 3, "alpha": True},
        "list": [1, {"value": SampleEnum.FIRST}],
    }

    assert compute_parameter_fingerprint(payload_one) == compute_parameter_fingerprint(payload_two)


def test_result_id_allocator_includes_fingerprint() -> None:
    """Allocator derives different identifiers when payload fingerprints diverge."""

    allocator = ResultIdAllocator()
    fingerprint_a = compute_parameter_fingerprint({"value": "alpha"})
    fingerprint_b = compute_parameter_fingerprint({"value": "beta"})

    allocation_a = allocator.allocate(seed="example", index=0, fingerprint=fingerprint_a)
    allocation_a_repeat = allocator.allocate(seed="example", index=0, fingerprint=fingerprint_a)
    allocation_b = allocator.allocate(seed="example", index=0, fingerprint=fingerprint_b)

    assert allocation_a == allocation_a_repeat
    assert allocation_a != allocation_b
    assert UUID(allocation_a)


def test_ensure_result_ids_respects_existing_values() -> None:
    """Existing identifiers should be returned untouched."""

    allocator = ResultIdAllocator()
    result = ensure_result_ids(["existing"], 1, allocator=allocator, seed="seed", fingerprint="fp")
    assert result == ["existing"]


def test_ensure_result_ids_uses_fingerprint() -> None:
    """Generated identifiers should differ when fingerprints do not match."""

    allocator = ResultIdAllocator()
    fingerprint_a = compute_parameter_fingerprint({"index": 1})
    fingerprint_b = compute_parameter_fingerprint({"index": 2})

    ids_a = ensure_result_ids(None, 2, allocator=allocator, seed="seed", fingerprint=fingerprint_a)
    ids_a_repeat = ensure_result_ids(None, 2, allocator=allocator, seed="seed", fingerprint=fingerprint_a)
    ids_b = ensure_result_ids(None, 2, allocator=allocator, seed="seed", fingerprint=fingerprint_b)

    assert ids_a == ids_a_repeat
    assert ids_a != ids_b


def test_ensure_result_ids_length_mismatch() -> None:
    """Providing mismatched identifiers should raise an error."""

    allocator = ResultIdAllocator()

    with pytest.raises(ValueError):
        ensure_result_ids(["only-one"], 2, allocator=allocator, seed="seed", fingerprint="fp")


def test_ensure_result_id_uses_fingerprint() -> None:
    """Single identifier allocation should also depend on fingerprints."""

    allocator = ResultIdAllocator()
    fingerprint_a = compute_parameter_fingerprint({"value": 1})
    fingerprint_b = compute_parameter_fingerprint({"value": 2})

    result_a = ensure_result_id(None, allocator=allocator, seed="seed", fingerprint=fingerprint_a)
    result_a_repeat = ensure_result_id(None, allocator=allocator, seed="seed", fingerprint=fingerprint_a)
    result_b = ensure_result_id(None, allocator=allocator, seed="seed", fingerprint=fingerprint_b)

    assert result_a == result_a_repeat
    assert result_a != result_b


def test_finalize_template_excludes_fields_from_fingerprint() -> None:
    """Excluded fields must not influence the fingerprint."""

    first_snapshot = finalize_template_for_parameters(
        _SimpleTemplate(result_ids=["alpha"]),
        fingerprint_exclude_fields=("result_ids",),
    )
    second_snapshot = finalize_template_for_parameters(
        _SimpleTemplate(result_ids=["beta"]),
        fingerprint_exclude_fields=("result_ids",),
    )

    assert first_snapshot.fingerprint == second_snapshot.fingerprint


def test_resolve_result_ids_from_payload_prefers_explicit_values() -> None:
    """Explicit identifiers should override payload-provided ones."""

    payload_ids = ["payload"]
    explicit_ids = ["explicit"]
    fingerprint = compute_parameter_fingerprint({"value": 42})

    resolved = resolve_result_ids_from_payload(
        explicit_ids=explicit_ids,
        payload_value=payload_ids,
        count=1,
        allocator=None,
        seed="seed",
        fingerprint=fingerprint,
    )
    assert resolved == explicit_ids

    fallback = resolve_result_ids_from_payload(
        explicit_ids=None,
        payload_value=payload_ids,
        count=1,
        allocator=None,
        seed="seed",
        fingerprint=fingerprint,
    )
    assert fallback == payload_ids


def test_resolve_result_id_from_payload_validates_types() -> None:
    """Invalid payload identifiers should raise informative errors."""

    fingerprint = compute_parameter_fingerprint({"value": "x"})

    resolved = resolve_result_id_from_payload(
        explicit_id=None,
        payload_value="payload-id",
        allocator=None,
        seed="seed",
        fingerprint=fingerprint,
    )
    assert resolved == "payload-id"

    with pytest.raises(TypeError):
        resolve_result_id_from_payload(
            explicit_id=None,
            payload_value=123,
            allocator=None,
            seed="seed",
            fingerprint=fingerprint,
        )
