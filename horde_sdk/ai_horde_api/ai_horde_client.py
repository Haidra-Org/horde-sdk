"""Definitions to help interact with the AI-Horde API."""
from __future__ import annotations

import urllib.parse

from loguru import logger

from horde_sdk.ai_horde_api.apimodels import (
    DeleteImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateCheckRequest,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api.apimodels import RequestErrorResponse
from horde_sdk.generic_api.generic_client import (
    GenericHordeAPISession,
    GenericHordeAPISimpleClient,
)


class AIHordeAPISimpleClient(GenericHordeAPISimpleClient):
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
        api_request = DeleteImageGenerateRequest(id=generation_id)

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
        api_request = DeleteImageGenerateRequest(id=generation_id)

        api_response = await self.async_submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response


class AIHordeAPISession(AIHordeAPISimpleClient, GenericHordeAPISession):
    """Represent an API session specifically configured for the AI-Horde API.

    If you make a request which requires follow up (such as a request to generate an image), this will delete the
    generation in progress when the context manager exits. If you do not want this to happen, use `AIHordeAPIClient`.
    """

    def __enter__(self) -> AIHordeAPISession:
        _self = super().__enter__()
        if not isinstance(_self, AIHordeAPISession):
            raise TypeError("Unexpected type returned from super().__enter__()")

        return _self

    async def __aenter__(self) -> AIHordeAPISession:
        _self = await super().__aenter__()
        if not isinstance(_self, AIHordeAPISession):
            raise TypeError("Unexpected type returned from super().__aenter__()")

        return _self


class AIHordeAPIClient:
    async def image_generate_request(self, image_gen_request: ImageGenerateAsyncRequest) -> ImageGenerateAsyncResponse:
        async with AIHordeAPISession() as image_gen_client:
            response = await image_gen_client.async_submit_request(
                api_request=image_gen_request,
                expected_response_type=image_gen_request.get_success_response_type(),
            )

            if isinstance(response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {response.message}")

            check_request_type = response.get_follow_up_default_request()
            follow_up_data = response.get_follow_up_data()
            check_request = check_request_type.model_validate(follow_up_data)
            async with AIHordeAPISession() as check_client:
                while True:
                    check_response = await check_client.async_submit_request(
                        api_request=check_request,
                        expected_response_type=check_request.get_success_response_type(),
                    )

                    if isinstance(check_response, RequestErrorResponse):
                        raise RuntimeError(f"Error response received: {check_response.message}")
