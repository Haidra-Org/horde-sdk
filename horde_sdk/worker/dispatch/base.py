"""Contains the class bases that encapsulate the parameters for the dispatching of a task to a worker.

This includes meta-parameters that are API-specific (ids), pertain to API expectations (time to live, etc),
or otherwise required for the worker to complete the task (such as r2 upload URLs).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from horde_sdk.worker.consts import (
    KNOWN_DISPATCH_SOURCE,
    KNOWN_INFERENCE_BACKEND,
    REQUESTED_BACKEND_CONSTRAINTS,
)


class DispatchParameterBase(BaseModel):
    """Base class for all dispatch parameter sets."""

    generation_ids: list[Any]
    """The identifiers for this generation. The request is expected to yield as many results as there are IDs."""

    dispatch_source: KNOWN_DISPATCH_SOURCE | str = KNOWN_DISPATCH_SOURCE.LOCAL_CUSTOM_3RD_PARTY
    """The source of the dispatch request. Defaults to KNOWN_DISPATCH_SOURCE.LOCAL_CUSTOM_3RD_PARTY."""

    ttl: int | None = None
    """The amount of seconds before this job is considered stale and aborted on the server. Defaults to None."""

    inference_backend: KNOWN_INFERENCE_BACKEND | str | None = None
    """The inference backend to use for this job. Defaults to None."""

    requested_backend_constraints: REQUESTED_BACKEND_CONSTRAINTS | str = REQUESTED_BACKEND_CONSTRAINTS.ANY
    """User/server request constraints on which backend to use. Defaults to REQUESTED_BACKEND_CONSTRAINTS.ANY."""
