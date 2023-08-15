"""Definitions to help interact with the AI-Horde API."""
from __future__ import annotations

import asyncio
import base64
import io
import time
import urllib.parse
from abc import ABC, abstractmethod
from collections.abc import Coroutine

import aiohttp
import PIL.Image
import requests
from loguru import logger

from horde_sdk.ai_horde_api.apimodels import (
    AlchemyAsyncRequest,
    AlchemyStatusResponse,
    DeleteImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateCheckRequest,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
    ImageGeneration,
)
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, BaseResponse
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api.apimodels import (
    RequestErrorResponse,
    ResponseRequiringFollowUpMixin,
    ResponseWithProgressMixin,
)
from horde_sdk.generic_api.generic_clients import (
    GenericAsyncHordeAPIManualClient,
    GenericAsyncHordeAPISession,
    GenericHordeAPIManualClient,
    GenericHordeAPISession,
)


class BaseAIHordeClient:
    """Base class for all AI-Horde API clients."""

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
            endpoint_url (str): The URL of the endpoint that was called.
        """
        logger.error("Error response received from the AI-Horde API.")
        logger.error(f"Endpoint: {endpoint_url}")
        logger.error(f"Message: {error_response.message}")


class AIHordeAPIManualClient(GenericHordeAPIManualClient, BaseAIHordeClient):
    """An API client specifically configured for the AI-Horde API."""

    def __init__(self) -> None:
        """Create a new instance of the AIHordeAPIManualClient."""
        super().__init__(
            path_fields=AIHordePathData,
        )

    def get_generate_check(
        self,
        generation_id: GenerationID | str,
    ) -> ImageGenerateCheckResponse | RequestErrorResponse:
        """Check if a pending image request has finished generating from the AI-Horde API.

        Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse | RequestErrorResponse: The response from the API.
        """
        api_request = ImageGenerateCheckRequest(id=generation_id)

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())

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

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
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

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            return api_response

        return api_response


class AIHordeAPIAsyncManualClient(GenericAsyncHordeAPIManualClient, BaseAIHordeClient):
    """An asyncio based API client specifically configured for the AI-Horde API."""

    def __init__(self, aiohttp_session: aiohttp.ClientSession) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            aiohttp_session=aiohttp_session,
            path_fields=AIHordePathData,
        )

    async def get_generate_check(
        self,
        generation_id: GenerationID | str,
    ) -> ImageGenerateCheckResponse | RequestErrorResponse:
        """Asynchronously check if a pending image request has finished generating and return the status of it.

        Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            generation_id (GenerationID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse | RequestErrorResponse: The response from the API.
        """
        api_request = ImageGenerateCheckRequest(id=generation_id)

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())

        return api_response

    async def get_generate_status(
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

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            return api_response

        return api_response

    async def delete_pending_image(
        self,
        generation_id: GenerationID | str,
    ) -> ImageGenerateStatusResponse | RequestErrorResponse:
        """Asynchronously delete a pending image request from the AI-Horde API.

        Args:
            generation_id (GenerationID | str): The ID of the request to delete.

        Returns:
            ImageGenerateStatusResponse | RequestErrorResponse: The response from the API.
        """
        api_request = DeleteImageGenerateRequest(id=generation_id)

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            return api_response

        return api_response


class AIHordeAPIClientSession(GenericHordeAPISession):
    """Context handler representing an API session specifically configured for the AI-Horde API.

    If you make a request which requires follow up (such as a request to generate an image), this will delete the
    generation in progress when the context manager exits. If you want to control this yourself, use
    `AIHordeAPIManualClient` instead.
    """

    def __init__(self) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            path_fields=AIHordePathData,
        )


class AIHordeAPIAsyncClientSession(GenericAsyncHordeAPISession):
    """Context handler representing an API session specifically configured for the AI-Horde API.

    If you make a request which requires follow up (such as a request to generate an image), this will delete the
    generation in progress when the context manager exits. If you want to control this yourself, use
    `AIHordeAPIManualClient` instead.
    """

    def __init__(
        self,
        aiohttp_session: aiohttp.ClientSession,
    ) -> None:
        """Create a new instance of the RatingsAPIClient."""
        super().__init__(
            aiohttp_session=aiohttp_session,
            path_fields=AIHordePathData,
        )


class BaseAIHordeSimpleClient(ABC):
    """The base class for the most straightforward clients which interact with the AI-Horde API."""

    reasonable_minimum_timeout = 15

    def is_timeout_reasonable(self, timeout: int, log_message: bool = False) -> bool:
        """Check if a timeout is reasonable.

        Args:
            timeout (int): The timeout to check.

        Returns:
            bool: True if the timeout is reasonable, False otherwise.
        """
        is_reasonable = timeout > 0 and timeout > self.reasonable_minimum_timeout
        if not is_reasonable and log_message:
            logger.warning(
                f"Timeout is less than {self.reasonable_minimum_timeout} seconds, this is " "probably too short.",
            )

        return is_reasonable

    @abstractmethod
    def generation_to_image(
        self,
        generation: ImageGeneration,
    ) -> PIL.Image.Image | Coroutine[None, None, PIL.Image.Image]:
        """Fetch and parse an image from a response."""


class AIHordeAPISimpleClient(BaseAIHordeSimpleClient):
    """A simple client for the AI-Horde API. This is the easiest way to get started."""

    def generation_to_image(self, generation: ImageGeneration) -> PIL.Image.Image:
        """Fetch and parse an image from a response.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ClientResponseError: If the generation couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        if generation.img is None:
            raise ValueError("Generation has no image")

        image_bytes: bytes | None = None
        if urllib.parse.urlparse(generation.img).scheme in ["http", "https"]:
            response = requests.get(generation.img)
            if response.status_code != 200:
                logger.error(f"Error downloading image: {response.status_code}")
                response.raise_for_status()

            image_bytes = response.content
        else:
            image_bytes = base64.b64decode(generation.img)

        if image_bytes is None:
            raise RuntimeError("Error downloading or parsing image")

        return PIL.Image.open(io.BytesIO(image_bytes))

    def _do_request_with_check(
        self,
        request: BaseAIHordeRequest,
        *,
        number_of_responses: int = 1,
        timeout: int = -1,
    ) -> BaseResponse:
        # Check if the timeout is unreasonably low
        if timeout is not None and timeout != -1 and timeout <= 5:
            logger.warning("Timeout is less than 5 seconds, this may cause unexpected behavior.")

        # This session class will cleanup incomplete requests in the event of an exception
        with AIHordeAPIClientSession() as horde_session:
            # Submit the initial request
            response = horde_session.submit_request(
                api_request=request,
                expected_response_type=request.get_default_success_response_type(),
            )

            # Check for error responses
            if isinstance(response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {response.message}")

            if not isinstance(response, ResponseRequiringFollowUpMixin):
                raise RuntimeError("Response did not need follow up")

            # Get the follow up data from the response
            check_request_type = response.get_follow_up_default_request()
            follow_up_data = response.get_follow_up_returned_params()
            num_follow_up_data = len(follow_up_data)

            # If there is not exactly one follow up request, something has gone wrong (or the API has changed?)
            if num_follow_up_data != 1:
                raise RuntimeError(
                    f"Expected exactly one check request should have been found, found {num_follow_up_data}",
                )

            # Create the check request from the follow up data
            check_request = check_request_type.model_validate(follow_up_data[0])
            # FIXME?

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()

            check_response: BaseResponse
            # Wait for the image generation to complete, checking every 4 seconds
            while True:
                # Submit the check request
                check_response = horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )

                # Check for error responses
                if isinstance(check_response, RequestErrorResponse):
                    raise RuntimeError(f"Error response received: {check_response.message}")

                if not isinstance(check_response, ResponseWithProgressMixin):
                    raise RuntimeError(f"Response did not have progress: {check_response}")

                # If the number of finished images is equal to the number of images requested, we're done
                if check_response.is_job_complete(number_of_responses):
                    break

                # If we've timed out, stop waiting, log a warning, and break out of the loop
                if timeout and timeout > 0 and time.time() - start_time > timeout:
                    logger.warning(
                        f"Timeout reached, cancelling generations still outstanding.: {response}:",
                    )
                    break

                # FIXME: This should be configurable
                time.sleep(4)
            finalize_request_type = check_response.get_finalize_success_request_type()
            final_response: BaseResponse = check_response
            if finalize_request_type:
                status_request = finalize_request_type.model_validate(follow_up_data[0])
                final_response = horde_session.submit_request(
                    api_request=status_request,
                    expected_response_type=status_request.get_default_success_response_type(),
                )

                if isinstance(final_response, RequestErrorResponse):
                    raise RuntimeError(f"Error response received: {final_response.message}")

            return final_response

        logger.error("Something went wrong with the request:")
        logger.error(f"Request: {request}")
        raise RuntimeError("Something went wrong with the request")

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

        Raises:
            ClientResponseError: If the generation couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.
        """

        timeout = timeout if timeout else -1
        self.is_timeout_reasonable(timeout, log_message=True)

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        response = self._do_request_with_check(
            image_gen_request,
            number_of_responses=n,
            timeout=timeout,
        )

        if not isinstance(response, ImageGenerateStatusResponse):
            raise RuntimeError("Response was not an ImageGenerateStatusResponse")

        return response.generations

    def alchemy_request(self, alchemy_request: AlchemyAsyncRequest, timeout: int | None = -1) -> AlchemyStatusResponse:
        """Submit an alchemy request to the AI-Horde API, and wait for it to complete.

        Args:
            alchemy_request (AlchemyAsyncRequest): The request to submit.

        Returns:
            AlchemyStatusResponse: The completed alchemy request(s).
        """
        timeout = timeout if timeout else -1
        self.is_timeout_reasonable(timeout, log_message=True)

        response = self._do_request_with_check(
            alchemy_request,
            number_of_responses=len(alchemy_request.forms),
            timeout=timeout,
        )
        if not isinstance(response, AlchemyStatusResponse):
            raise RuntimeError("Response was not an AlchemyAsyncResponse")

        return response


class AIHordeAPIAsyncSimpleClient(BaseAIHordeSimpleClient):
    """An asyncio based simple client for the AI-Horde API. Start with this class if you want asyncio capabilities.."""

    def __init__(self, aiohttp_session: aiohttp.ClientSession) -> None:
        """Create a new instance of the AIHordeAPISimpleClient."""
        self._aiohttp_session = aiohttp_session

    async def generation_to_image(self, generation: ImageGeneration) -> PIL.Image.Image:
        """Convert an image generation to a PIL image.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ClientResponseError: If the generation couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        if generation.img is None:
            raise ValueError("Generation has no image")

        if self._aiohttp_session is None:
            raise RuntimeError("No aiohttp session provided but an async request was made.")

        image_bytes: bytes | None = None
        if urllib.parse.urlparse(generation.img).scheme in ["http", "https"]:
            async with self._aiohttp_session.get(generation.img) as response:
                if response.status != 200:
                    logger.error(f"Error downloading image: {response.status}")
                    response.raise_for_status()

                image_bytes = await response.read()
        else:
            try:
                image_bytes = base64.b64decode(generation.img)
            except Exception as e:
                logger.error(f"Error parsing image: {e}")
                raise e

        if image_bytes is None:
            raise RuntimeError("Error downloading or parsing image")

        return PIL.Image.open(io.BytesIO(image_bytes))

    async def image_generate_request(
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
            returns any completed images at the end of the timeout. Any value 0 or less will wait indefinitely.
            Defaults to -1.

        Returns:
            list[ImageGeneration]: The completed images.
        """
        # Check if the timeout is unreasonably low
        if timeout is not None and timeout != -1 and timeout <= 5:
            logger.warning("Timeout is less than 5 seconds, this may cause unexpected behavior.")

        # This session class will cleanup incomplete requests in the event of an exception
        async with AIHordeAPIAsyncClientSession(aiohttp_session=self._aiohttp_session) as ai_horde_session:
            # Submit the initial request
            response = await ai_horde_session.submit_request(
                api_request=image_gen_request,
                expected_response_type=image_gen_request.get_default_success_response_type(),
            )

            # Check for error responses
            if isinstance(response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {response.message}")

            # Get the follow up data from the response
            check_request_type = response.get_follow_up_default_request()
            follow_up_data = response.get_follow_up_returned_params()
            num_follow_up_data = len(follow_up_data)

            # If there is not exactly one follow up request, something has gone wrong (or the API has changed?)
            if num_follow_up_data != 1:
                raise RuntimeError(
                    f"Expected exactly one check request should have been found, found {num_follow_up_data}",
                )

            # Create the check request from the follow up data
            check_request = check_request_type.model_validate(follow_up_data[0])

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()

            # Get the number of images to generate from the request
            num_images_request = 1
            if image_gen_request.params is not None and image_gen_request.params.n:
                num_images_request = image_gen_request.params.n

            # Wait for the image generation to complete, checking every 4 seconds
            while True:
                # Submit the check request
                check_response = await ai_horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )

                # Check for error responses
                if isinstance(check_response, RequestErrorResponse):
                    raise RuntimeError(f"Error response received: {check_response.message}")

                # If the number of finished images is equal to the number of images requested, we're done
                if check_response.finished == num_images_request:
                    break

                # If we've timed out, stop waiting, log a warning, and break out of the loop
                if timeout and timeout > 0 and time.time() - start_time > timeout:
                    logger.warning(
                        f" {response.id_}: Timeout reached, cancelling image generations still outstanding.",
                    )
                    break

                await asyncio.sleep(4)  # FIXME: This should be configurable

            # The status request has the images, so we create one of those and submit it
            status_request = ImageGenerateStatusRequest(id=response.id_)
            status_response = await ai_horde_session.submit_request(
                api_request=status_request,
                expected_response_type=status_request.get_default_success_response_type(),
            )

            if isinstance(status_response, RequestErrorResponse):
                raise RuntimeError(f"Error response received: {status_response.message}")

            # Return the images. The helper function `generation_to_image` can be used to convert them to PIL images.
            return status_response.generations

        logger.error("Something went wrong with the request:")
        logger.error(f"Request: {image_gen_request}")
        return []
