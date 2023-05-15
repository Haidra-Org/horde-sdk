"""Definitions to help interact with the AI-Horde API."""
import pydantic
from typing_extensions import override

from ..generic_api import GenericHordeAPIClient
from ..generic_api.apimodels import BaseRequest
from .metadata import RatingsAPIPathData


class RatingsAPIClient(GenericHordeAPIClient):
    """Represent a client specifically configured for the AI-Horde APi."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(pathData=RatingsAPIPathData)

    @override
    def submitRequest(self, request: BaseRequest) -> pydantic.BaseModel:
        return super().submitRequest(request)
