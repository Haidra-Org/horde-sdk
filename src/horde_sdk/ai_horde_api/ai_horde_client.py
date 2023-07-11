"""Definitions to help interact with the AI-Horde API."""
import urllib.parse

from loguru import logger

from horde_sdk.ai_horde_api.apimodels import (
    CancelImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
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

    def generate_image_async(
        self,
        api_request: ImageGenerateAsyncRequest,
    ) -> ImageGenerateAsyncResponse | RequestErrorResponse:
        """Submit a request to the AI-Horde API to generate an image asynchronously.

        This is a call to the `/v2/generate/async` endpoint.

        Args:
            api_request (ImageGenerateAsyncRequest): The request to submit.

        Raises:
            RuntimeError: If the response type is not ImageGenerateAsyncResponse.

        Returns:
            ImageGenerateAsyncResponse | RequestErrorResponse: The response from the API.
        """
        api_response = self.submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response
        if not isinstance(api_response, ImageGenerateAsyncResponse):
            logger.error("Failed to generate an image asynchronously.")
            logger.error(f"Unexpected response type: {type(api_response)}")
            raise RuntimeError(
                f"Unexpected response type. Expected ImageGenerateAsyncResponse, got {type(api_response)}",
            )

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
        api_request = CancelImageGenerateRequest(id=generation_id, apikey=apikey)

        api_response = self.submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response
