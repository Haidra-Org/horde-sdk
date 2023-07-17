"""Definitions to help interact with the Ratings API."""
import aiohttp

from horde_sdk.generic_api.generic_clients import GenericHordeAPIManualClient
from horde_sdk.ratings_api.metadata import RatingsAPIPathFields, RatingsAPIQueryFields


class RatingsAPIClient(GenericHordeAPIManualClient):
    """Represent a client specifically configured for the Ratings APi."""

    def __init__(self, aiohttp_session: aiohttp.ClientSession | None = None) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            aiohttp_session=aiohttp_session,
            path_fields=RatingsAPIPathFields,
            query_fields=RatingsAPIQueryFields,
        )
