"""Request metadata specific to the AI-Horde API."""
from horde_sdk.generic_api.metadata import GenericPathFields


class AIHordePathData(GenericPathFields):
    """AI Horde specific path data. See parent class for more information."""

    id_ = "id"
    """A job UUID."""
    user_id = "user_id"
    """The horde user id."""
    filter_id = "filter_id"
    """The ID of a content filter."""
    team_id = "team_id"
    """The UUID of a team."""
    worker_id = "worker_id"
    """The UUID of a worker."""
    sharedkey_id = "sharedkey_id"
    """The UUID representing a shared key."""
