"""Request metadata specific to the AI-Horde API."""

from enum import auto
from uuid import UUID

from horde_sdk.generic_api.metadata import GenericPathFields, GenericQueryFields


class AIHordePathData(GenericPathFields):
    """AI Horde specific path data. See parent class for more information."""

    id_ = "id"
    """A job UUID."""
    user_id = auto()
    """The horde user id."""
    filter_id = auto()
    """The ID of a content filter."""
    team_id = auto()
    """The UUID of a team."""
    worker_id = auto()
    """The UUID of a worker."""
    worker_name = auto()
    """The name of a worker."""
    sharedkey_id = auto()
    """The UUID representing a shared key."""
    model_name = auto()
    """The name of a model."""
    ipaddr = auto()
    """An IP address."""
    message_id = auto()
    """The ID of a message."""
    style_id = auto()
    """The ID of a style."""
    style_name = auto()
    """The name of a style."""
    collection_id = auto()
    """The ID of a collection."""
    example_id = auto()
    """The ID of an example."""


_dummy_uuid = str(UUID(int=0))

_default_path_values: dict[GenericPathFields, str] = {
    AIHordePathData.id_: _dummy_uuid,
    AIHordePathData.user_id: "1",
    AIHordePathData.filter_id: _dummy_uuid,
    AIHordePathData.team_id: _dummy_uuid,
    AIHordePathData.worker_id: _dummy_uuid,
    AIHordePathData.sharedkey_id: _dummy_uuid,
    AIHordePathData.message_id: _dummy_uuid,
    AIHordePathData.style_id: _dummy_uuid,
    AIHordePathData.collection_id: _dummy_uuid,
    AIHordePathData.example_id: _dummy_uuid,
    AIHordePathData.ipaddr: "8.8.8.8",
    AIHordePathData.model_name: "dummy model name",
    AIHordePathData.worker_name: "dummy worker name",
    AIHordePathData.style_name: "dummy style name",
}


class AIHordeQueryData(GenericQueryFields):
    """AI Horde specific query data. See parent class for more information."""

    api_model_state = "model_state"
    """The level of official support by the API."""
