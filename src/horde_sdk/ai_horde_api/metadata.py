"""Request metadata specific to the AI-Horde API."""
from horde_sdk.generic_api import GenericPathFields


class AIHordePathData(GenericPathFields):
    # TODO docstrings
    id = "id"  # noqa: A003
    """A request GUID as a str."""
    user_id = "user_id"
    filter_id = "filter_id"
    team_id = "team_id"
    worker_id = "worker_id"
    sharedkey_id = "sharedkey_id"
