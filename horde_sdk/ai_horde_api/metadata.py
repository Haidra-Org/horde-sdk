"""Request metadata specific to the AI-Horde API."""
from horde_sdk.generic_api.metadata import GenericPathFields


class AIHordePathData(GenericPathFields):
    """`StrEnum` for data that is exclusively passed as part of a URL path (not a query string after the `?`)."""

    id_ = "id"
    """A request GUID as a str."""
    user_id = "user_id"
    filter_id = "filter_id"
    team_id = "team_id"
    worker_id = "worker_id"
    sharedkey_id = "sharedkey_id"
