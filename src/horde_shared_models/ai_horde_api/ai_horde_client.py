"""Definitions to help interact with the AI-Horde API."""
import pydantic
from typing_extensions import override

from horde_shared_models.ai_horde_api.metadata import AIHordePathData
from horde_shared_models.generic_api import GenericHordeAPIClient
from horde_shared_models.generic_api.apimodels import BaseRequest


class RatingsAPIClient(GenericHordeAPIClient):
    """Represent a client specifically configured for the AI-Horde APi."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(path_data=AIHordePathData)

    @override
    def submit_request(self, request: BaseRequest) -> pydantic.BaseModel:
        return super().submit_request(request)
