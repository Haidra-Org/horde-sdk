"""Definitions to help interact with the Ratings API."""
from horde_sdk.generic_api.generic_client import GenericHordeAPIClient
from horde_sdk.ratings_api.metadata import RatingsAPIPathFields, RatingsAPIQueryFields


class RatingsAPIClient(GenericHordeAPIClient):
    """Represent a client specifically configured for the Ratings APi."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            path_fields=RatingsAPIPathFields,
            query_fields=RatingsAPIQueryFields,
        )
