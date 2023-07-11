"""Definitions to help interact with the AI-Horde API."""
import urllib.parse

from loguru import logger

from horde_sdk.ai_horde_api.apimodels import (
    DeleteImageGenerateRequest,
    ImageGenerateCheckRequest,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api import GenericHordeAPIClient, RequestErrorResponse


class AIHordeAPIClient(GenericHordeAPIClient):
    """Represent an API client specifically configured for the AI-Horde API."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(path_fields=AIHordePathData)

    _base_url: str = AI_HORDE_BASE_URL

    @property
    def base_url(self) -> str:
        """Get the base URL for the AI-Horde API."""
        return self.base_url

    @base_url.setter
    def base_url(self, value: str) -> None:
        """Set the base URL for the AI-Horde API."""
        if urllib.parse.urlparse(value).scheme not in ["http", "https"]:
            raise ValueError(f"Invalid scheme in URL: {value}")

        self.base_url = value

    def _handle_api_error(self, error_response: RequestErrorResponse, endpoint_url: str) -> None:
        """Handle an error response from the API.

        Args:
            error_response (RequestErrorResponse): The error response to handle.
        """
        logger.error("Error response received from the AI-Horde API.")
        logger.error(f"Endpoint: {endpoint_url}")
        logger.error(f"Message: {error_response.message}")

    def get_generate_check(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateCheckResponse | RequestErrorResponse:
        """Check if a pending image request has finished generating from the AI-Horde API, and return
        the status of it. Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse | RequestErrorResponse: The response from the API.
        """ """"""
        api_request = ImageGenerateCheckRequest(id=generation_id)

        api_response = self.submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())

        return api_response

    async def async_get_generate_check(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateCheckResponse | RequestErrorResponse:
        """Asynchronously check if a pending image request has finished generating from the AI-Horde API, and return
        the status of it. Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse | RequestErrorResponse: The response from the API.
        """

        api_request = ImageGenerateCheckRequest(id=generation_id)

        api_response = await self.async_submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())

        return api_response

    def get_generate_status(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        """Get the status and any generated images for a pending image request from the AI-Horde API.

        *Do not use this method more often than is necessary.* The AI-Horde API will rate limit you if you do.
        Use `get_generate_check` instead to check the status of a pending image request.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID): The ID of the request to check.
        Returns:
            ImageGenerateStatusResponse | RequestErrorResponse: The response from the API.
        """
        api_request = ImageGenerateStatusRequest(id=generation_id)

        api_response = self.submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response

    async def async_get_generate_status(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        """Asynchronously get the status and any generated images for a pending image request from the AI-Horde API.

        *Do not use this method more often than is necessary.* The AI-Horde API will rate limit you if you do.
        Use `get_generate_check` instead to check the status of a pending image request.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID): The ID of the request to check.
        Returns:
            ImageGenerateStatusResponse | RequestErrorResponse: The response from the API.
        """
        api_request = ImageGenerateStatusRequest(id=generation_id)

        api_response = await self.async_submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response

    def delete_pending_image(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        """Delete a pending image request from the AI-Horde API.

        Args:
            generation_id (GenerationID): The ID of the request to delete.
        """
        api_request = DeleteImageGenerateRequest(id=generation_id, apikey=apikey)

        api_response = self.submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response

    async def async_delete_pending_image(
        self,
        apikey: str,
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        api_request = DeleteImageGenerateRequest(id=generation_id, apikey=apikey)

        api_response = await self.async_submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response
