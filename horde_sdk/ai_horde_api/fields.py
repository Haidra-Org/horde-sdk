"""This module contains extra API models that are not part of the official API specification.

However, this module may still assist in the construction of valid requests to the API, primarily
by providing additional type hints for the request and response payloads and validation.
"""

import uuid

from pydantic import BaseModel, field_validator


class UUID_Identifier(BaseModel):
    """Represents a UUID type identifier used by the API."""

    model_config = {"frozen": True}

    id: str | uuid.UUID  # noqa: A003

    @property
    def id_as_uuid(self) -> uuid.UUID:
        """Return the ID as a UUID."""
        if isinstance(self.id, uuid.UUID):
            return self.id

        return uuid.UUID(str(self.id), version=4)

    @field_validator("id")
    def id_must_be_uuid(cls, v: str | uuid.UUID) -> str | uuid.UUID:
        """Ensure that the ID is a valid UUID."""
        if isinstance(v, uuid.UUID):
            return v

        try:
            uuid.UUID(v, version=4)
        except ValueError as e:
            raise ValueError(f"Invalid UUID {v}") from e
        return v

    def __str__(self) -> str:
        """Return the ID as a string."""
        return str(self.id)

    def __eq__(self, other: object) -> bool:
        """Return True if this object string compares equal to the other object string."""
        return str(self) == str(other)

    def __hash__(self) -> int:
        """Return the hash of the string representation of this object."""
        return hash(str(self))


class GenerationID(UUID_Identifier):
    """Represents the ID of a generation job. Instances of this class can be compared with a `str` or a UUID object."""


class WorkerID(UUID_Identifier):
    """Represents the ID of a worker. Instances of this class can be compared with a `str` or a UUID object."""


class ImageID(UUID_Identifier):
    """Represents the ID of an image. Instances of this class can be compared with a `str` or a UUID object."""


class TeamID(UUID_Identifier):
    """Represents the ID of a team. Instances of this class can be compared with a `str` or a UUID object."""
