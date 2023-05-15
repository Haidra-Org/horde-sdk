"""Definitions to help interact with the Ratings API."""
from ..generic_api import GenericHordeAPIClient
from .metadata import RatingsAPIPathData


class RatingsAPIClient(GenericHordeAPIClient):
    """Represent a client specifically configured for the Ratings APi."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(pathData=RatingsAPIPathData)
