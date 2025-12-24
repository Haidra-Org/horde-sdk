"""Schema version migration utilities for generation parameter payloads."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from horde_sdk.generation_parameters.generic import CompositeParametersBase

ParameterSchemaMigrationFunc = Callable[[dict[str, object]], dict[str, object]]


class ParameterSchemaMigrationError(RuntimeError):
    """Raised when a parameter payload cannot be migrated to the current schema."""


class _ParameterSchemaMigrationRegistry:
    """Registry that tracks schema migration steps per parameter type."""

    def __init__(self) -> None:
        self._entries: dict[type[CompositeParametersBase], dict[str, tuple[str, ParameterSchemaMigrationFunc]]] = {}

    def register(
        self,
        parameter_type: type[CompositeParametersBase],
        *,
        from_version: str,
        to_version: str,
        migration: ParameterSchemaMigrationFunc,
    ) -> None:
        """Register a migration step for ``parameter_type`` from ``from_version`` to ``to_version``."""
        migration_map = self._entries.setdefault(parameter_type, {})
        if from_version in migration_map:
            raise ValueError(
                f"Migration from version '{from_version}' is already registered for {parameter_type.__qualname__}.",
            )
        migration_map[from_version] = (to_version, migration)

    def apply(
        self,
        parameter_type: type[CompositeParametersBase],
        payload: Mapping[str, object],
    ) -> dict[str, object]:
        """Apply registered migrations to ``payload`` so it matches the current schema version."""
        payload_dict = dict(payload)

        schema_value = payload_dict.get("schema_version")
        if isinstance(schema_value, str) and schema_value:
            current_version = schema_value
        else:
            current_version = parameter_type.legacy_schema_version()

        payload_dict["schema_version"] = current_version
        target_version = parameter_type.current_schema_version()

        if current_version == target_version:
            payload_dict["schema_version"] = target_version
            return payload_dict

        migrations = self._entries.get(parameter_type, {})
        visited_versions: set[str] = set()
        updated_payload = payload_dict

        while current_version != target_version:
            entry = migrations.get(current_version)
            if entry is None:
                raise ParameterSchemaMigrationError(
                    "No migration path from version "
                    f"'{current_version}' to '{target_version}' for {parameter_type.__qualname__}.",
                )

            next_version, migration = entry
            updated_payload = migration(dict(updated_payload))
            updated_payload["schema_version"] = next_version

            if next_version in visited_versions:
                raise ParameterSchemaMigrationError(
                    f"Detected migration cycle when upgrading {parameter_type.__qualname__}.",
                )

            visited_versions.add(next_version)
            current_version = next_version

        return updated_payload


_PARAMETER_SCHEMA_MIGRATIONS = _ParameterSchemaMigrationRegistry()


def register_parameter_schema_migration(
    parameter_type: type[CompositeParametersBase],
    *,
    from_version: str,
    to_version: str,
    migration: ParameterSchemaMigrationFunc,
) -> None:
    """Register a migration step that upgrades ``parameter_type`` payloads."""
    _PARAMETER_SCHEMA_MIGRATIONS.register(
        parameter_type,
        from_version=from_version,
        to_version=to_version,
        migration=migration,
    )


def apply_parameter_schema_migrations(
    parameter_type: type[CompositeParametersBase],
    payload: Mapping[str, object],
) -> dict[str, object]:
    """Upgrade ``payload`` to match ``parameter_type``'s current schema version."""
    return _PARAMETER_SCHEMA_MIGRATIONS.apply(parameter_type, payload)
