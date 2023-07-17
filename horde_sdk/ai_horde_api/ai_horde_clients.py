"""Definitions to help interact with the AI-Horde API."""
from __future__ import annotations

import asyncio
import base64
import io
import time
import urllib.parse

import aiohttp
import PIL.Image
import requests
from loguru import logger

from horde_sdk.ai_horde_api.apimodels import (
    DeleteImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateCheckRequest,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
    ImageGeneration,
)
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api.apimodels import RequestErrorResponse
from horde_sdk.generic_api.generic_clients import (
    GenericHordeAPIManualClient,
    GenericHordeAPISession,
)


class AIHordeAPIManualClient(GenericHordeAPIManualClient):
    """Represent an API client specifically configured for the AI-Horde API."""

    def __init__(self, aiohttp_session: aiohttp.ClientSession | None = None) -> None:
        """Create a new instance of the RatingsAPIClient.

        Args:
            aiohttp_session (aiohttp.ClientSession, optional): The aiohttp session to use if you intend to use asyncio.
            Defaults to None.


        """
        super().__init__(
            aiohttp_session=aiohttp_session,
            path_fields=AIHordePathData,
        )

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
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        api_request = DeleteImageGenerateRequest(id=generation_id)

        api_response = await self.async_submit_request(api_request, api_request.get_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_endpoint_url())
            return api_response

        return api_response


class AIHordeAPISession(AIHordeAPIManualClient, GenericHordeAPISession):
    """Context handler representing an API session specifically configured for the AI-Horde API.

    If you make a request which requires follow up (such as a request to generate an image), this will delete the
    generation in progress when the context manager exits. If you want to control this yourself, use
    `AIHordeAPIManualClient` instead.
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


class AIHordeAPISimpleClient:
    _aiohttp_session: aiohttp.ClientSession | None

    def __init__(self, aiohttp_session: aiohttp.ClientSession | None = None) -> None:
        self._aiohttp_session = aiohttp_session

    def generation_to_image(self, generation: ImageGeneration) -> PIL.Image.Image:
        """Convert an image generation to a PIL image.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ValueError: If the generation has no image, or the image could not be downloaded or parsed.

        """

        if generation.img is None:
            raise ValueError("Generation has no image")

        image_bytes: bytes | None = None
        if urllib.parse.urlparse(generation.img).scheme in ["http", "https"]:
            response = requests.get(generation.img)
            if response.status_code != 200:
                raise RuntimeError(f"Error downloading image: {response.status_code}")

            image_bytes = response.content
        else:
            image_bytes = base64.b64decode(generation.img)

        if image_bytes is None:
            raise RuntimeError("Error downloading or parsing image")

        return PIL.Image.open(io.BytesIO(image_bytes))

    async def async_generation_to_image(self, generation: ImageGeneration) -> PIL.Image.Image:
        """Convert an image generation to a PIL image.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ValueError: If the generation has no image, or the image could not be downloaded or parsed.

        """

        if generation.img is None:
            raise ValueError("Generation has no image")

        if self._aiohttp_session is None:
            raise RuntimeError("No aiohttp session provided but an async request was made.")

        image_bytes: bytes | None = None
        if urllib.parse.urlparse(generation.img).scheme in ["http", "https"]:
            async with self._aiohttp_session.get(generation.img) as response:
                if response.status != 200:
                    raise RuntimeError(f"Error downloading image: {response.status}")

                image_bytes = await response.read()
        else:
            image_bytes = base64.b64decode(generation.img)

        if image_bytes is None:
            raise RuntimeError("Error downloading or parsing image")

        return PIL.Image.open(io.BytesIO(image_bytes))

    def image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int | None = -1,
    ) -> list[ImageGeneration]:
        """Submit an image generation request to the AI-Horde API, and wait for it to complete.

        Args:
            image_gen_request (ImageGenerateAsyncRequest): The request to submit.
            timeout (int, optional): The number of seconds to wait before aborting.
            returns any completed images at the end of the timeout. Defaults to -1.

        Returns:
            list[ImageGeneration]: The completed images.
        """
        if timeout is not None and timeout != -1 and timeout <= 5:
            logger.warning("Timeout is less than 5 seconds, this may cause unexpected behavior.")

        with AIHordeAPISession() as horde_session:
            response = horde_session.submit_request(
                api_request=image_gen_request,
                expected_response_type=image_gen_request.get_success_response_type(),
            )

            if isinstance(response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {response.message}")

            check_request_type = response.get_follow_up_default_request()
            follow_up_data = response.get_follow_up_returned_params()
            check_request = check_request_type.model_validate(follow_up_data)

            start_time = time.time()

            num_images_request = 1
            if image_gen_request.params is not None and image_gen_request.params.n:
                num_images_request = image_gen_request.params.n

            while True:
                check_response = horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_success_response_type(),
                )

                if isinstance(check_response, RequestErrorResponse):
                    raise RuntimeError(f"Error response received: {check_response.message}")

                if check_response.finished == num_images_request:
                    break

                if timeout and timeout > 0 and time.time() - start_time > timeout:
                    logger.warning(
                        f" {response.id_}: Timeout reached, cancelling image generations still outstanding.",
                    )
                    break

                time.sleep(4)  # FIXME: This should be configurable

            status_request = ImageGenerateStatusRequest(id=response.id_)

            status_response = horde_session.submit_request(
                api_request=status_request,
                expected_response_type=status_request.get_success_response_type(),
            )

            if isinstance(status_response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {status_response.message}")

            return status_response.generations

    async def async_image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int | None = -1,
    ) -> list[ImageGeneration]:
        """Submit an image generation request to the AI-Horde API, and wait for it to complete.

        *Be warned* that using this method asynchronously could trigger a rate limit from the AI-Horde API.
        Space concurrent requests apart slightly to allow them to be less than 10/second.

        Args:
            image_gen_request (ImageGenerateAsyncRequest): The request to submit.
            timeout (int, optional): The number of seconds to wait before aborting.
            returns any completed images at the end of the timeout. Defaults to -1.

        Returns:
            list[ImageGeneration]: The completed images.
        """

        if timeout is not None and timeout != -1 and timeout <= 5:
            logger.warning("Timeout is less than 5 seconds, this may cause unexpected behavior.")

        async with AIHordeAPISession(self._aiohttp_session) as ai_horde_session:
            response = await ai_horde_session.async_submit_request(
                api_request=image_gen_request,
                expected_response_type=image_gen_request.get_success_response_type(),
            )

            if isinstance(response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {response.message}")

            check_request_type = response.get_follow_up_default_request()
            follow_up_data = response.get_follow_up_returned_params()
            check_request = check_request_type.model_validate(follow_up_data)

            start_time = time.time()

            num_images_request = 1
            if image_gen_request.params is not None and image_gen_request.params.n:
                num_images_request = image_gen_request.params.n

            while True:
                check_response = await ai_horde_session.async_submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_success_response_type(),
                )

                if isinstance(check_response, RequestErrorResponse):
                    raise RuntimeError(f"Error response received: {check_response.message}")

                if check_response.finished == num_images_request:
                    break

                if timeout and timeout > 0 and time.time() - start_time > timeout:
                    logger.warning(
                        f" {response.id_}: Timeout reached, cancelling image generations still outstanding.",
                    )
                    break

                await asyncio.sleep(4)  # FIXME: This should be configurable

            status_request = ImageGenerateStatusRequest(id=response.id_)
            status_response = await ai_horde_session.async_submit_request(
                api_request=status_request,
                expected_response_type=status_request.get_success_response_type(),
            )

            if isinstance(status_response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {status_response.message}")

            return status_response.generations
