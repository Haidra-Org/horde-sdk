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

from horde_sdk import COMPLETE_LOGGER_LABEL, PROGRESS_LOGGER_LABEL
from horde_sdk.ai_horde_api.apimodels import (
    AlchemyAsyncRequest,
    AlchemyStatusResponse,
    DeleteImageGenerateRequest,
    ImageGenerateAsyncDryRunResponse,
    ImageGenerateAsyncRequest,
    ImageGenerateCheckRequest,
    ImageGenerateCheckResponse,
    ImageGenerateStatusRequest,
    ImageGenerateStatusResponse,
    ImageGeneration,
)
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_BASE_URL
from horde_sdk.ai_horde_api.exceptions import AIHordeImageValidationError, AIHordeRequestError
from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.generic_api.apimodels import (
    HordeResponse,
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


def parse_image_from_base64(image_base64: str) -> PIL.Image.Image:
    """Parse an image from base 64.

    Args:
        image_base64 (str): The base 64 encoded image.

    Returns:
        PIL.Image.Image: The parsed image.

    Raises:
        binascii.Error: If the image couldn't be parsed from base 64.
        RuntimeError: If the image couldn't be parsed for any other reason.

    """
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        logger.error(f"Error parsing image: {e}")
        raise e

    if image_bytes is None:
        raise RuntimeError("Error parsing image")

    return PIL.Image.open(io.BytesIO(image_bytes))


def download_image_bytes(url: str) -> io.BytesIO:
    """Download an image from a URL.

    Args:
        url (str): The URL to download the image from.

    Returns:
        PIL.Image.Image: The downloaded image.

    Raises:
        ClientResponseError: If the image couldn't be downloaded.
        binascii.Error: If the image couldn't be parsed from base 64.
        RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

    """
    response = requests.get(url)
    if response.status_code != 200:
        logger.error(f"Error downloading image: {response.status_code}")
        response.raise_for_status()

    logger.debug(f"Downloaded image: {url}")
    return io.BytesIO(response.content)


def download_image_from_url(url: str) -> PIL.Image.Image:
    """Download an image from a URL.

    Args:
        url (str): The URL to download the image from.

    Returns:
        PIL.Image.Image: The downloaded image.

    Raises:
        ClientResponseError: If the image couldn't be downloaded.
        binascii.Error: If the image couldn't be parsed from base 64.
        RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

    """
    return PIL.Image.open(download_image_bytes(url))


def download_image_from_generation(generation: ImageGeneration) -> PIL.Image.Image:
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
        image_bytes = download_image_bytes(generation.img).read()
    else:
        image_bytes = base64.b64decode(generation.img)

    if image_bytes is None:
        raise RuntimeError("Error downloading or parsing image")

    return PIL.Image.open(io.BytesIO(image_bytes))


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
        job_id: JobID,
    ) -> ImageGenerateCheckResponse:
        """Check if a pending image request has finished generating from the AI-Horde API.

        Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            job_id (JobID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse: The response from the API.
        """
        api_request = ImageGenerateCheckRequest(id=job_id)

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

        return api_response

    def get_generate_status(
        self,
        job_id: JobID,
    ) -> ImageGenerateStatusResponse:
        """Get the status and any generated images for a pending image request from the AI-Horde API.

        *Do not use this method more often than is necessary.* The AI-Horde API will rate limit you if you do.
        Use `get_generate_check` instead to check the status of a pending image request.

        Args:
            apikey (str): The API key to use for authentication.
            job_id (JobID): The ID of the request to check.

        Returns:
            tuple[ImageGenerateStatusResponse, JobID]: The final status response and the corresponding job ID.
        """
        api_request = ImageGenerateStatusRequest(id=job_id)

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

        return api_response

    def delete_pending_image(
        self,
        job_id: JobID,
    ) -> ImageGenerateStatusResponse:
        """Delete a pending image request from the AI-Horde API.

        Args:
            job_id (JobID): The ID of the request to delete.

        Returns:
            ImageGenerateStatusResponse: The response from the API.
        """
        api_request = DeleteImageGenerateRequest(id=job_id)

        api_response = self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

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
        job_id: JobID,
    ) -> ImageGenerateCheckResponse:
        """Asynchronously check if a pending image request has finished generating and return the status of it.

        Not to be confused with `get_generate_status` which returns the images too.

        Args:
            apikey (str): The API key to use for authentication.
            job_id (JobID | str): The ID of the request to check.

        Returns:
            ImageGenerateCheckResponse: The response from the API.
        """
        api_request = ImageGenerateCheckRequest(id=job_id)

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

        return api_response

    async def get_generate_status(
        self,
        job_id: JobID,
    ) -> ImageGenerateStatusResponse:
        """Asynchronously get the status and any generated images for a pending image request from the AI-Horde API.

        *Do not use this method more often than is necessary.* The AI-Horde API will rate limit you if you do.
        Use `get_generate_check` instead to check the status of a pending image request.

        Args:
            apikey (str): The API key to use for authentication.
            job_id (JobID): The ID of the request to check.

        Returns:
            ImageGenerateStatusResponse: The response from the API.
        """
        api_request = ImageGenerateStatusRequest(id=job_id)

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

        return api_response

    async def delete_pending_image(
        self,
        job_id: JobID,
    ) -> ImageGenerateStatusResponse:
        """Asynchronously delete a pending image request from the AI-Horde API.

        Args:
            job_id (JobID | str): The ID of the request to delete.

        Returns:
            ImageGenerateStatusResponse: The response from the API.
        """
        api_request = DeleteImageGenerateRequest(id=job_id)

        api_response = await self.submit_request(api_request, api_request.get_default_success_response_type())
        if isinstance(api_response, RequestErrorResponse):  # pragma: no cover
            self._handle_api_error(api_response, api_request.get_api_endpoint_url())
            raise AIHordeRequestError(api_response)

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
        if timeout <= 0:  # No timeout
            return True

        is_reasonable = timeout > self.reasonable_minimum_timeout
        if not is_reasonable and log_message:  # pragma: no cover
            logger.warning(
                f"Timeout is less than {self.reasonable_minimum_timeout} seconds, this is probably too short.",
            )

        return is_reasonable

    @abstractmethod
    def download_image_from_generation(
        self,
        generation: ImageGeneration,
    ) -> PIL.Image.Image | Coroutine[None, None, tuple[PIL.Image.Image, JobID]]:
        """Convert from base64 or download an image from a response."""

    @abstractmethod
    def download_image_from_url(
        self,
        url: str,
    ) -> PIL.Image.Image | Coroutine[None, None, PIL.Image.Image]:
        """Download an image from a URL."""

    @staticmethod
    def parse_image_from_base64(image_base64: str) -> PIL.Image.Image:
        """Parse an image from base 64.

        Args:
            image_base64 (str): The base 64 encoded image.

        Returns:
            PIL.Image.Image: The parsed image.

        Raises:
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be parsed for any other reason.

        """
        return parse_image_from_base64(image_base64)


class AIHordeAPISimpleClient(BaseAIHordeSimpleClient):
    """A simple client for the AI-Horde API. This is the easiest way to get started."""

    def download_image_from_generation(self, generation: ImageGeneration) -> PIL.Image.Image:
        """Synchronously convert from base64 or download an image from a response.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ClientResponseError: If the generation couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        return download_image_from_generation(generation)

    def download_image_from_url(self, url: str) -> PIL.Image.Image:
        """Synchronously download an image from a URL.

        Args:
            url (str): The URL to download the image from.

        Returns:
            PIL.Image.Image: The downloaded image.

        Raises:
            ClientResponseError: If the image couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        return download_image_from_url(url)

    def _do_request_with_check(
        self,
        api_request: BaseAIHordeRequest,
        *,
        number_of_responses: int = 1,
        timeout: int | None = None,
    ) -> tuple[HordeResponse, JobID]:
        # This session class will cleanup incomplete requests in the event of an exception
        with AIHordeAPIClientSession() as horde_session:
            # Submit the initial request
            logger.log(PROGRESS_LOGGER_LABEL, f"Submitting request: {api_request.log_safe_model_dump()}")
            response = horde_session.submit_request(
                api_request=api_request,
                expected_response_type=api_request.get_default_success_response_type(),
            )

            logger.log(PROGRESS_LOGGER_LABEL, f"Response received: {response}")

            # Check for error responses
            if isinstance(response, RequestErrorResponse):  # pragma: no cover
                raise AIHordeRequestError(response)

            if not isinstance(response, ResponseRequiringFollowUpMixin):  # pragma: no cover
                raise RuntimeError(f"Response did not need follow up. Request: {api_request.log_safe_model_dump()}")

            # Get the follow up data from the response
            check_request_type = response.get_follow_up_default_request_type()
            follow_up_data = response.get_follow_up_returned_params()
            num_follow_up_data = len(follow_up_data)

            # If there is not exactly one follow up request, something has gone wrong (or the API has changed?)
            if num_follow_up_data != 1:  # FIXME?  # pragma: no cover
                raise RuntimeError(
                    f"Expected exactly one check request should have been found, found {num_follow_up_data}",
                )

            # Create the check request from the follow up data
            check_request = check_request_type.model_validate(follow_up_data[0])

            if not isinstance(check_request, JobRequestMixin):  # pragma: no cover
                logger.error(f"Check request type is not a JobRequestMixin: {check_request.log_safe_model_dump()}")
                raise RuntimeError(
                    f"Check request type is not a JobRequestMixin: {check_request.log_safe_model_dump()}",
                )

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()

            check_response: HordeResponse

            job_id: JobID = check_request.id_

            # Wait for the image generation to complete, checking every 4 seconds
            check_count = 0
            while True:
                check_count += 1
                # Submit the check request
                check_response = horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )
                if check_count % 5 == 0:
                    logger.log(PROGRESS_LOGGER_LABEL, f"Checking request: {check_request.id_}")
                else:
                    logger.debug(f"Checking request: {check_request.id_}")

                # Check for error responses
                if isinstance(check_response, RequestErrorResponse):  # pragma: no cover
                    raise AIHordeRequestError(check_response)

                if not isinstance(check_response, ResponseWithProgressMixin):  # pragma: no cover
                    raise RuntimeError(f"Response did not have progress: {check_response}")

                # If the number of finished images is equal to the number of images requested, we're done
                if check_response.is_job_complete(number_of_responses):
                    logger.log(PROGRESS_LOGGER_LABEL, f"Job finished and available on the server: {check_request.id_}")
                    break

                # If we've timed out, stop waiting, log a warning, and break out of the loop
                if timeout and timeout > 0 and time.time() - start_time > timeout:
                    logger.warning(
                        f"Timeout reached, cancelling generations still outstanding: {response}:",
                    )
                    break

                # FIXME: This should be configurable
                time.sleep(4)

            finalize_request_type = check_response.get_finalize_success_request_type()

            final_response: HordeResponse = check_response

            if finalize_request_type:
                status_request = finalize_request_type.model_validate(follow_up_data[0])

                if not isinstance(status_request, JobRequestMixin):  # pragma: no cover
                    logger.error(f"Finalize request type is not a JobRequestMixin: {finalize_request_type}")
                    raise RuntimeError(f"Finalize request type is not a JobRequestMixin: {finalize_request_type}")

                final_response = horde_session.submit_request(
                    api_request=status_request,
                    expected_response_type=status_request.get_default_success_response_type(),
                )

                if isinstance(final_response, RequestErrorResponse):  # pragma: no cover
                    raise RuntimeError(f"Error response received: {final_response.message}")

            logger.log(COMPLETE_LOGGER_LABEL, f"Request complete: {check_request.id_}")
            return (final_response, job_id)

        logger.error("Something went wrong with the request:")
        logger.error(f"Request: {api_request}")
        raise RuntimeError("Something went wrong with the request")

    def image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int | None = None,
    ) -> tuple[ImageGenerateStatusResponse, JobID]:
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

        timeout = timeout if timeout else 0
        self.is_timeout_reasonable(timeout, log_message=True)

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        logger.log(PROGRESS_LOGGER_LABEL, f"Requesting {n} images.")
        final_response, JobID = self._do_request_with_check(
            image_gen_request,
            number_of_responses=n,
            timeout=timeout,
        )

        if isinstance(final_response, RequestErrorResponse):  # pragma: no cover
            logger.error(f"Error response received: {final_response.message}")
            raise AIHordeRequestError(final_response)

        if not isinstance(final_response, ImageGenerateStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an ImageGenerateStatusResponse")

        return (final_response, JobID)

    def image_generate_request_dry_run(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
    ) -> ImageGenerateAsyncDryRunResponse:
        if not image_gen_request.dry_run:
            raise RuntimeError("Dry run request must have dry_run set to True")

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        logger.log(PROGRESS_LOGGER_LABEL, f"Requesting dry run for {n} images.")

        with AIHordeAPIClientSession() as horde_session:
            dry_run_response = horde_session.submit_request(image_gen_request, ImageGenerateAsyncDryRunResponse)

            if isinstance(dry_run_response, RequestErrorResponse):  # pragma: no cover
                logger.error(f"Error response received: {dry_run_response.message}")
                raise AIHordeRequestError(dry_run_response)

            return dry_run_response

        raise RuntimeError("Something went wrong with the request")

    def alchemy_request(
        self,
        alchemy_request: AlchemyAsyncRequest,
        timeout: int | None = None,
    ) -> tuple[AlchemyStatusResponse, JobID]:
        """Submit an alchemy request to the AI-Horde API, and wait for it to complete.

        Args:
            alchemy_request (AlchemyAsyncRequest): The request to submit.

        Returns:
            AlchemyStatusResponse: The completed alchemy request(s).

        Raises:
            AIHordeRequestError: If the request failed. The error response is included in the exception.
        """
        if timeout:
            self.is_timeout_reasonable(timeout, log_message=True)

        logger.log(PROGRESS_LOGGER_LABEL, f"Requesting {len(alchemy_request.forms)} alchemy requests.")
        for form in alchemy_request.forms:
            logger.debug(f"Request: {form}")

        response, job_id = self._do_request_with_check(
            alchemy_request,
            number_of_responses=len(alchemy_request.forms),
            timeout=timeout,
        )

        if isinstance(response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(response)

        if not isinstance(response, AlchemyStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an AlchemyAsyncResponse")

        return (response, job_id)


class AIHordeAPIAsyncSimpleClient(BaseAIHordeSimpleClient):
    """An asyncio based simple client for the AI-Horde API. Start with this class if you want asyncio capabilities.."""

    def __init__(self, aiohttp_session: aiohttp.ClientSession) -> None:
        """Create a new instance of the AIHordeAPISimpleClient."""
        self._aiohttp_session = aiohttp_session

    async def download_image_from_generation(self, generation: ImageGeneration) -> tuple[PIL.Image.Image, JobID]:
        """Asynchronously convert from base64 or download an image from a response.

        Args:
            generation (ImageGeneration): The image generation to convert.

        Returns:
            PIL.Image.Image: The converted image.

        Raises:
            ClientResponseError: If the generation couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        if generation.img is None:  # pragma: no cover
            raise ValueError("Generation has no image")

        if self._aiohttp_session is None:  # pragma: no cover
            raise RuntimeError("No aiohttp session provided but an async request was made.")

        image_bytes: bytes | None = None
        if urllib.parse.urlparse(generation.img).scheme in ["http", "https"]:
            async with self._aiohttp_session.get(generation.img) as response:
                if response.status != 200:  # pragma: no cover
                    logger.error(f"Error downloading image: {response.status}")
                    response.raise_for_status()

                image_bytes = await response.read()
        else:
            try:
                image_bytes = base64.b64decode(generation.img)
            except Exception as e:
                logger.error(f"Error parsing image: {e}")
                raise e

        if image_bytes is None:  # pragma: no cover
            raise RuntimeError("Error downloading or parsing image")

        return (PIL.Image.open(io.BytesIO(image_bytes)), generation.id_)

    async def download_image_from_url(self, url: str) -> PIL.Image.Image:
        """Asynchronously download an image from a URL.

        Args:
            url (str): The URL to download the image from.

        Returns:
            PIL.Image.Image: The downloaded image.

        Raises:
            ClientResponseError: If the image couldn't be downloaded.
            binascii.Error: If the image couldn't be parsed from base 64.
            RuntimeError: If the image couldn't be downloaded or parsed for any other reason.

        """
        if self._aiohttp_session is None:
            raise RuntimeError("No aiohttp session provided but an async request was made.")

        async with self._aiohttp_session.get(url) as response:
            if response.status != 200:  # pragma: no cover
                logger.error(f"Error downloading image: {response.status}")
                response.raise_for_status()

            image_bytes = await response.read()

        if image_bytes is None:  # pragma: no cover
            raise RuntimeError("Error downloading or parsing image")

        return PIL.Image.open(io.BytesIO(image_bytes))

    async def _do_request_with_check(
        self,
        api_request: BaseAIHordeRequest,
        *,
        number_of_responses: int = 1,
        timeout: int | None = None,
    ) -> tuple[HordeResponse, JobID]:
        # This session class will cleanup incomplete requests in the event of an exception

        async with AIHordeAPIAsyncClientSession(aiohttp_session=self._aiohttp_session) as ai_horde_session:
            # Submit the initial request
            response = await ai_horde_session.submit_request(
                api_request=api_request,
                expected_response_type=api_request.get_default_success_response_type(),
            )

            # Check for error responses
            if isinstance(response, RequestErrorResponse):  # pragma: no cover
                if "Image validation failed" in response.message:  # TODO: No magic strings!
                    raise AIHordeImageValidationError(response)
                raise AIHordeRequestError(response)

            if not isinstance(response, ResponseRequiringFollowUpMixin):  # pragma: no cover
                raise RuntimeError("Response did not need follow up")

            # Get the follow up data from the response
            check_request_type = response.get_follow_up_default_request_type()
            follow_up_data = response.get_follow_up_returned_params()
            num_follow_up_data = len(follow_up_data)

            # If there is not exactly one follow up request, something has gone wrong (or the API has changed?)
            if num_follow_up_data != 1:  # FIXME?  # pragma: no cover
                raise RuntimeError(
                    f"Expected exactly one check request should have been found, found {num_follow_up_data}",
                )

            # Create the check request from the follow up data
            check_request = check_request_type.model_validate(follow_up_data[0])

            if not isinstance(check_request, JobRequestMixin):  # pragma: no cover
                logger.error(f"Check request type is not a JobRequestMixin: {check_request.log_safe_model_dump()}")
                raise RuntimeError(
                    f"Check request type is not a JobRequestMixin: {check_request.log_safe_model_dump()}",
                )

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()

            check_response: HordeResponse

            job_id: JobID = check_request.id_

            # Wait for the image generation to complete, checking every 4 seconds
            while True:
                # Submit the check request
                check_response = await ai_horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )

                # Check for error responses
                if isinstance(check_response, RequestErrorResponse):  # pragma: no cover
                    raise AIHordeRequestError(check_response)

                if not isinstance(check_response, ResponseWithProgressMixin):  # pragma: no cover
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

                time.sleep(4)  # FIXME: This should be configurable

            finalize_request_type = check_response.get_finalize_success_request_type()

            final_response: HordeResponse = check_response

            if finalize_request_type:
                finalize_request = finalize_request_type.model_validate(follow_up_data[0])

                if not isinstance(finalize_request, JobRequestMixin):  # pragma: no cover
                    logger.error(f"Finalize request type is not a JobRequestMixin: {finalize_request}")
                    raise RuntimeError(f"Finalize request type is not a JobRequestMixin: {finalize_request}")

                final_response = await ai_horde_session.submit_request(
                    api_request=finalize_request,
                    expected_response_type=finalize_request.get_default_success_response_type(),
                )

                if isinstance(final_response, RequestErrorResponse):  # pragma: no cover
                    raise AIHordeRequestError(final_response)

            return (final_response, job_id)

        # logger.error("Something went wrong with the request:")
        logger.error("It looks like this request was cancelled:")
        logger.error(f"Request: {api_request}")
        raise asyncio.CancelledError("Something went wrong with the request")

    async def image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int | None = None,
    ) -> tuple[ImageGenerateStatusResponse, JobID]:
        """Submit an image generation request to the AI-Horde API, and wait for it to complete.

        *Be warned* that using this method too frequently could trigger a rate limit from the AI-Horde API.
        Space concurrent requests apart slightly to allow them to be less than 10/second.

        Args:
            image_gen_request (ImageGenerateAsyncRequest): The request to submit.
            timeout (int, optional): The number of seconds to wait before aborting.
            returns any completed images at the end of the timeout. Any value 0 or less will wait indefinitely.
            Defaults to -1.

        Returns:
            tuple[ImageGenerateStatusResponse, JobID]: The final status response and the corresponding job ID.

        Raises:
            AIHordeRequestError: If the request failed. The error response is included in the exception.
        """

        timeout = timeout if timeout else 0
        self.is_timeout_reasonable(timeout, log_message=True)

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        final_response, job_id = await self._do_request_with_check(
            image_gen_request,
            number_of_responses=n,
            timeout=timeout,
        )

        if isinstance(final_response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(final_response)

        if not isinstance(final_response, ImageGenerateStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an ImageGenerateStatusResponse")

        return (final_response, job_id)

    async def alchemy_request(
        self,
        alchemy_request: AlchemyAsyncRequest,
        timeout: int | None = None,
    ) -> tuple[AlchemyStatusResponse, JobID]:
        """Submit an alchemy request to the AI-Horde API, and wait for it to complete.

        *Be warned* that using this method too frequently could trigger a rate limit from the AI-Horde API.
        Space concurrent requests apart slightly to allow them to be less than 10/second.

        Args:
            alchemy_request (AlchemyAsyncRequest): The request to submit.

        Returns:
            tuple[ImageGenerateStatusResponse, JobID]: The final status response and the corresponding job ID.

        Raises:
            AIHordeRequestError: If the request failed. The error response is included in the exception.
        """
        if timeout:
            self.is_timeout_reasonable(timeout, log_message=True)

        response, job_id = await self._do_request_with_check(
            alchemy_request,
            number_of_responses=len(alchemy_request.forms),
            timeout=timeout,
        )
        if isinstance(response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(response)

        if not isinstance(response, AlchemyStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an AlchemyAsyncResponse")

        return (response, job_id)
