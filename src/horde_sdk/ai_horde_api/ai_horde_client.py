"""Definitions to help interact with the AI-Horde API."""
from loguru import logger

from horde_sdk.ai_horde_api.apimodels.generate import ImageGenerateAsyncRequest, ImageGenerateAsyncResponse
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api import GenericHordeAPIClient, RequestErrorResponse


class AIHordeAPIClient(GenericHordeAPIClient):
    """Represent an API client specifically configured for the AI-Horde API."""

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(path_fields=AIHordePathData)

    def generate_image_async(
        self,
        api_request: ImageGenerateAsyncRequest,
    ) -> ImageGenerateAsyncResponse | RequestErrorResponse:
        """Submit a request to the AI-Horde API to generate an image asynchronously.

        Args:
            api_request (ImageGenerateAsyncRequest): The request to submit.

        Raises:
            RuntimeError: If the response type is not ImageGenerateAsyncResponse.

        Returns:
            ImageGenerateAsyncResponse | RequestErrorResponse: The response from the API.
        """
        api_response = self.post(api_request)
        if isinstance(api_response, RequestErrorResponse):
            logger.error("Error response received from the AI-Horde API.")
            logger.error(f"Endpoint: {api_request.get_endpoint_url()}")
            logger.error(f"Message: {api_response.message}")
            return api_response
        if not isinstance(api_response, ImageGenerateAsyncResponse):
            logger.error("Failed to generate an image asynchronously.")
            logger.error(f"Unexpected response type: {type(api_response)}")
            raise RuntimeError(
                f"Unexpected response type. Expected ImageGenerateAsyncResponse, got {type(api_response)}"
            )

        return api_response

    def delete_pending_image_request(
        self,
        generation_id: GenerationID,
    ):
        """Delete a pending image request from the AI-Horde API.

        Args:
            generation_id (GenerationID): The ID of the request to delete.
        """
