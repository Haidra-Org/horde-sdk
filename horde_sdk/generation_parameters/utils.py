from __future__ import annotations

import base64
import hashlib
import json
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final, TypeVar
from uuid import UUID

from pydantic import BaseModel

from horde_sdk.consts import ID_TYPES

_DEFAULT_RESULT_ID_NAMESPACE: Final[uuid.UUID] = uuid.uuid5(
    uuid.NAMESPACE_URL,
    "https://github.com/Haidra-Org/horde-sdk",
)


TemplateT = TypeVar("TemplateT", bound=BaseModel)


@dataclass(frozen=True)
class TemplateFingerprintSnapshot[TemplateT: BaseModel]:
    """Snapshot containing the finalized template payload and its fingerprint."""

    template: TemplateT
    payload: dict[str, object]
    fingerprint: str


@dataclass(frozen=True)
class TemplateFinalization[TemplateT: BaseModel]:
    """Snapshot produced when applying overrides to a template."""

    template: TemplateT
    payload: dict[str, object]


def apply_template_overrides[TemplateT: BaseModel](
    template: TemplateT,
    *,
    overrides: Mapping[str, object] | None = None,
    exclude_none: bool = False,
) -> TemplateFinalization[TemplateT]:
    """Return a template copy with overrides applied alongside its payload snapshot."""
    updated = template if overrides is None or not overrides else template.model_copy(update=dict(overrides))

    payload = updated.model_dump(exclude_none=exclude_none)
    return TemplateFinalization(template=updated, payload=payload)


def finalize_template_for_parameters(
    template: TemplateT,
    *,
    overrides: Mapping[str, object] | None = None,
    exclude_none: bool = False,
    fingerprint_exclude_fields: Collection[str] | None = None,
    fingerprint_transform: Callable[[TemplateFinalization[TemplateT], dict[str, object]], None] | None = None,
) -> TemplateFingerprintSnapshot[TemplateT]:
    """Finalize a template payload and compute a deterministic fingerprint."""
    finalization = apply_template_overrides(
        template,
        overrides=overrides,
        exclude_none=exclude_none,
    )

    fingerprint_payload = dict(finalization.payload)
    if fingerprint_exclude_fields:
        for field in fingerprint_exclude_fields:
            fingerprint_payload.pop(field, None)

    if fingerprint_transform is not None:
        fingerprint_transform(finalization, fingerprint_payload)

    fingerprint = compute_parameter_fingerprint(fingerprint_payload)
    return TemplateFingerprintSnapshot(
        template=finalization.template,
        payload=finalization.payload,
        fingerprint=fingerprint,
    )


def _normalise_for_fingerprint(value: object) -> object:
    """Convert values into JSON-serialisable structures with deterministic ordering."""
    if value is None:
        return None
    if isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, Enum):
        enum_value = value.value
        if isinstance(enum_value, bool | int | float | str):
            return enum_value
        return value.name
    if isinstance(value, UUID | Path):
        return str(value)
    if isinstance(value, bytes):
        encoded = base64.b64encode(value).decode("ascii")
        return {"__type__": "bytes", "base64": encoded}
    if isinstance(value, Mapping):
        return {
            str(key): _normalise_for_fingerprint(value_item)
            for key, value_item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        return [_normalise_for_fingerprint(item) for item in value]
    raise TypeError(f"Unsupported value type for fingerprinting: {type(value)!r}")


def compute_parameter_fingerprint(payload: Mapping[str, object]) -> str:
    """Produce a stable fingerprint for a parameter payload."""
    normalised = _normalise_for_fingerprint(payload)
    serialised = json.dumps(normalised, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialised.encode("utf-8"))
    return digest.hexdigest()


class ResultIdAllocator:
    """Utility that produces deterministic identifiers for generation results."""

    _namespace: uuid.UUID

    def __init__(self, namespace: uuid.UUID | None = None) -> None:
        """Create an allocator bound to the provided namespace."""
        self._namespace = namespace or _DEFAULT_RESULT_ID_NAMESPACE

    def allocate(self, *, seed: str, index: int, fingerprint: str | None = None) -> str:
        """Derive a deterministic identifier from the seed, fingerprint, and positional index."""
        payload = f"{seed}:{fingerprint}:{index}" if fingerprint is not None else f"{seed}:{index}"
        return str(uuid.uuid5(self._namespace, payload))


def ensure_result_ids(
    existing: Sequence[ID_TYPES] | None,
    count: int,
    *,
    allocator: ResultIdAllocator | None,
    seed: str,
    fingerprint: str | None = None,
) -> list[ID_TYPES]:
    """Return a concrete list of result identifiers, allocating when needed."""
    if existing is not None:
        identifiers = list(existing)
        if len(identifiers) != count:
            raise ValueError(f"Expected {count} result identifiers but received {len(identifiers)}.")
        return identifiers

    if allocator is None:
        return [str(uuid.uuid4()) for _ in range(count)]

    return [allocator.allocate(seed=seed, index=index, fingerprint=fingerprint) for index in range(count)]


def ensure_result_id(
    existing: ID_TYPES | None,
    *,
    allocator: ResultIdAllocator | None,
    seed: str,
    fingerprint: str | None = None,
) -> ID_TYPES:
    """Return a concrete result identifier, allocating when missing."""
    if existing is not None:
        return existing

    if allocator is None:
        return str(uuid.uuid4())

    return allocator.allocate(seed=seed, index=0, fingerprint=fingerprint)


def resolve_result_ids_from_payload(
    *,
    explicit_ids: Sequence[ID_TYPES] | None,
    payload_value: object,
    count: int,
    allocator: ResultIdAllocator | None,
    seed: str,
    fingerprint: str,
) -> list[ID_TYPES]:
    """Resolve a concrete list of result identifiers from explicit, payload, or allocated sources."""
    payload_ids = _normalise_result_id_sequence(payload_value)
    return ensure_result_ids(
        explicit_ids or payload_ids,
        count,
        allocator=allocator,
        seed=seed,
        fingerprint=fingerprint,
    )


def resolve_result_id_from_payload(
    *,
    explicit_id: ID_TYPES | None,
    payload_value: object,
    allocator: ResultIdAllocator | None,
    seed: str,
    fingerprint: str,
) -> ID_TYPES:
    """Resolve a single result identifier from explicit, payload, or allocated sources."""
    payload_identifier = _normalise_result_id(payload_value)
    return ensure_result_id(
        explicit_id or payload_identifier,
        allocator=allocator,
        seed=seed,
        fingerprint=fingerprint,
    )


def _normalise_result_id(value: object) -> ID_TYPES | None:
    if value is None:
        return None
    if isinstance(value, str | UUID):
        return value
    raise TypeError("result_id entries must be strings or UUIDs.")


def _normalise_result_id_sequence(value: object) -> list[ID_TYPES] | None:
    if value is None or isinstance(value, str | bytes | bytearray):
        return None
    if not isinstance(value, Sequence):
        return None

    resolved: list[ID_TYPES] = []
    for entry in value:
        if not isinstance(entry, str | UUID):
            raise TypeError("result_ids entries must be strings or UUIDs.")
        resolved.append(entry)
    return resolved
