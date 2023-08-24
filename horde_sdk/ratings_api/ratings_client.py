"""Definitions to help interact with the Ratings API."""

from horde_sdk.generic_api.generic_clients import GenericHordeAPIManualClient
from horde_sdk.ratings_api.metadata import RatingsAPIPathFields, RatingsAPIQueryFields


# TODO: asyncio versions
class RatingsAPIClient(GenericHordeAPIManualClient):
    """Represent a client specifically configured for the Ratings APi."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            path_fields=RatingsAPIPathFields,
            query_fields=RatingsAPIQueryFields,
        )
