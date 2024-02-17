"""Definitions to help interact with the AI-Horde API."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import inspect
import io
import time
import urllib.parse
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from enum import auto

import aiohttp
import PIL.Image
import requests
from loguru import logger
from strenum import StrEnum

from horde_sdk import COMPLETE_LOGGER_LABEL, PROGRESS_LOGGER_LABEL, ContainsMessageResponseMixin, HordeRequest
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
    ResponseGenerationProgressCombinedMixin,
)
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.consts import GENERATION_MAX_LIFE
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


class _PROGRESS_STATE(StrEnum):
    waiting = auto()
    finished = auto()
    timed_out = auto()


class BaseAIHordeSimpleClient(ABC):
    """The base class for the most straightforward clients which interact with the AI-Horde API."""

    reasonable_minimum_timeout = 20

    def validate_timeout(self, timeout: int, log_message: bool = False) -> int:
        """Check if a timeout is reasonable.

        Args:
            timeout (int): The timeout to check.

        Returns:
            bool: True if the timeout is reasonable, False otherwise.
        """
        if timeout <= 0:  # pragma: no cover
            logger.debug(f"No timeout set. Using default timeout of {GENERATION_MAX_LIFE} seconds.")
            return GENERATION_MAX_LIFE

        if timeout > GENERATION_MAX_LIFE:  # pragma: no cover
            logger.warning(
                f"Timeout ({timeout}) is greater than the maximum possible of {GENERATION_MAX_LIFE} seconds."
                f"Using {GENERATION_MAX_LIFE} for the timeout.",
            )
            return GENERATION_MAX_LIFE

        if timeout < self.reasonable_minimum_timeout and log_message:  # pragma: no cover
            logger.warning(
                f"test_simple_client_async_image_generate_multiple than {self.reasonable_minimum_timeout} seconds, "
                "this is probably too short.",
            )

        return timeout

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

    def _handle_initial_response(
        self,
        initial_response: HordeResponse | RequestErrorResponse,
    ) -> tuple[HordeRequest, JobID, list[dict[str, object]]]:
        # Check for error responses
        if isinstance(initial_response, RequestErrorResponse):  # pragma: no cover
            if "Image validation failed" in initial_response.message:  # TODO: No magic strings!
                raise AIHordeImageValidationError(initial_response)
            raise AIHordeRequestError(initial_response)

        if not isinstance(initial_response, ResponseRequiringFollowUpMixin):  # pragma: no cover
            raise RuntimeError("Response did not need follow up")

        # Get the follow up data from the response
        check_request_type = initial_response.get_follow_up_default_request_type()
        follow_up_data = initial_response.get_follow_up_returned_params()
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

        job_id: JobID = check_request.id_

        logger.log(PROGRESS_LOGGER_LABEL, f"Response received: {initial_response}")
        if isinstance(initial_response, ContainsMessageResponseMixin) and initial_response.message:
            if "warning" in initial_response.message.lower():
                logger.warning(f"{job_id}: {initial_response.message}")
            else:
                logger.info(f"{job_id}: {initial_response.message}")

        return check_request, job_id, follow_up_data

    def _handle_progress_response(
        self,
        check_request: HordeRequest,
        check_response: HordeResponse | RequestErrorResponse,
        job_id: JobID,
        *,
        check_count: int,
        number_of_responses: int,
        start_time: float,
        timeout: int,
        check_callback: Callable | None = None,
        check_callback_type: type[ResponseWithProgressMixin | ResponseGenerationProgressCombinedMixin] | None = None,
    ) -> _PROGRESS_STATE:
        """Handle a response from the API when checking the progress of a request.

        Typically, this is a response from a `check` or `status` request.
        """

        # Check for error responses
        if isinstance(check_response, RequestErrorResponse):
            raise AIHordeRequestError(check_response)

        # Check if the response has progress
        if not isinstance(check_response, ResponseWithProgressMixin):
            raise RuntimeError(f"Response did not have progress: {check_response}")

        # If there is a callback, call it with the response
        if check_callback is not None:
            if check_callback_type and not isinstance(check_response, check_callback_type):
                raise RuntimeError(f"Callback response type mismatch: {check_response}")
            if check_callback_type is None:
                logger.warning("Callback type not specified, skipping type check")
                logger.debug(f"Type of sent response: {type(check_response)}")
            check_callback(check_response)

        # Log a message indicating that the request has been checked
        log_message = f"Checked request: {job_id}, is_possible: {check_response.is_job_possible()}"

        # Log the request if it's the first check or every 5th check
        if check_count == 1 or check_count % 5 == 0:
            logger.log(PROGRESS_LOGGER_LABEL, log_message)
            logger.log(PROGRESS_LOGGER_LABEL, f"{job_id}: {check_response.log_safe_model_dump()}")
            if not check_response.is_job_possible():
                logger.warning(f"Job not possible: {job_id}")
        # Otherwise, just log the message at the debug level
        else:
            logger.debug(log_message)

        # If the number of finished images is equal to the number of images requested, we're done
        if check_response.is_job_complete(number_of_responses):
            logger.log(PROGRESS_LOGGER_LABEL, f"Job finished and available on the server: {job_id}")
            return _PROGRESS_STATE.finished

        # If we've timed out, stop waiting, log a warning, and break out of the loop
        if timeout and timeout > 0 and time.time() - start_time > timeout:
            logger.warning(
                f"Timeout reached, cancelling generations still outstanding: {job_id}: {check_response}:",
            )
            return _PROGRESS_STATE.timed_out

        # If the job is not complete and the timeout has not been reached, continue waiting
        return _PROGRESS_STATE.waiting


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
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable | None = None,
        check_callback_type: type[ResponseWithProgressMixin | ResponseGenerationProgressCombinedMixin] | None = None,
    ) -> tuple[HordeResponse, JobID]:
        """Submit a request which requires check/status polling to the AI-Horde API, and wait for it to complete.

        Args:
            api_request (BaseAIHordeRequest): The request to submit.
            number_of_responses (int, optional): The number of responses to expect. Defaults to 1.
            timeout (int, optional): The number of seconds to wait before aborting.
                returns any completed images at the end of the timeout. Defaults to DEFAULT_GENERATION_TIMEOUT.

        Returns:
            tuple[HordeResponse, JobID]: The final response and the corresponding job ID.
        """

        if check_callback is not None and len(inspect.getfullargspec(check_callback).args) == 0:
            raise ValueError("Callback must take at least one argument")

        # This session class will cleanup incomplete requests in the event of an exception
        with AIHordeAPIClientSession() as horde_session:
            # Submit the initial request
            logger.debug(
                f"Submitting request: {api_request.log_safe_model_dump()} with timeout {timeout}",
            )
            initial_response = horde_session.submit_request(
                api_request=api_request,
                expected_response_type=api_request.get_default_success_response_type(),
            )

            # Handle the initial response to get the check request, job ID, and follow-up data
            check_request, job_id, follow_up_data = self._handle_initial_response(initial_response)

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()
            check_count = 0
            check_response: HordeResponse

            # Wait for the image generation to complete, checking every 4 seconds
            while True:
                check_count += 1

                # Submit the check request
                check_response = horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )

                # Handle the progress response to determine if the job is finished or timed out
                progress_state = self._handle_progress_response(
                    check_request,
                    check_response,
                    job_id,
                    check_count=check_count,
                    number_of_responses=number_of_responses,
                    start_time=start_time,
                    timeout=timeout,
                    check_callback=check_callback,
                    check_callback_type=check_callback_type,
                )

                if progress_state == _PROGRESS_STATE.finished or progress_state == _PROGRESS_STATE.timed_out:
                    break

                # Wait for 4 seconds before checking again
                time.sleep(4)

            # Check if the check response has progress
            if not isinstance(check_response, ResponseWithProgressMixin):
                raise RuntimeError(f"Response did not have progress: {check_response}")

            # Get the finalize request type from the check response
            finalize_request_type = check_response.get_finalize_success_request_type()

            # Set the final response to the check response by default
            final_response: HordeResponse = check_response

            # If there is a finalize request type, submit the finalize request
            if finalize_request_type:
                status_request = finalize_request_type.model_validate(follow_up_data[0])

                if not isinstance(status_request, JobRequestMixin):
                    logger.error(f"Finalize request type is not a JobRequestMixin: {finalize_request_type}")
                    raise RuntimeError(f"Finalize request type is not a JobRequestMixin: {finalize_request_type}")

                final_response = horde_session.submit_request(
                    api_request=status_request,
                    expected_response_type=status_request.get_default_success_response_type(),
                )

                if isinstance(final_response, RequestErrorResponse):
                    raise AIHordeRequestError(final_response)

            # Log a message indicating that the request is complete
            logger.log(COMPLETE_LOGGER_LABEL, f"Request complete: {job_id}")

            # Return the final response and job ID
            return (final_response, job_id)

        # If there is an exception, log an error and raise a RuntimeError
        logger.error("Something went wrong with the request:")
        logger.error(f"Request: {api_request.log_safe_model_dump()}")
        raise RuntimeError("Something went wrong with the request")

    def image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable[[ImageGenerateCheckResponse], None] | None = None,
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

        timeout = self.validate_timeout(timeout, log_message=True)

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        logger.log(PROGRESS_LOGGER_LABEL, f"Requesting {n} images.")
        final_response, JobID = self._do_request_with_check(
            image_gen_request,
            number_of_responses=n,
            timeout=timeout,
            check_callback=check_callback,
            check_callback_type=ImageGenerateCheckResponse,
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
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable[[AlchemyStatusResponse], None] | None = None,
    ) -> tuple[AlchemyStatusResponse, JobID]:
        """Submit an alchemy request to the AI-Horde API, and wait for it to complete.

        Args:
            alchemy_request (AlchemyAsyncRequest): The request to submit.

        Returns:
            AlchemyStatusResponse: The completed alchemy request(s).

        Raises:
            AIHordeRequestError: If the request failed. The error response is included in the exception.
        """
        timeout = self.validate_timeout(timeout, log_message=True)

        logger.log(PROGRESS_LOGGER_LABEL, f"Requesting {len(alchemy_request.forms)} alchemy requests.")
        for form in alchemy_request.forms:
            logger.debug(f"Request: {form}")

        response, job_id = self._do_request_with_check(
            alchemy_request,
            number_of_responses=len(alchemy_request.forms),
            timeout=timeout,
            check_callback=check_callback,
        )

        if isinstance(response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(response)

        if not isinstance(response, AlchemyStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an AlchemyAsyncResponse")

        return (response, job_id)


class AIHordeAPIAsyncSimpleClient(BaseAIHordeSimpleClient):
    """An asyncio based simple client for the AI-Horde API. Start with this class if you want asyncio capabilities.."""

    _horde_client_session: AIHordeAPIAsyncClientSession | None

    def __init__(
        self,
        aiohttp_session: aiohttp.ClientSession | None,
        horde_client_session: AIHordeAPIAsyncClientSession | None = None,
    ) -> None:
        """Create a new instance of the AIHordeAPISimpleClient."""
        if aiohttp_session is not None and horde_client_session is not None:
            raise ValueError("Only one of aiohttp_session or horde_client_session can be provided")

        self._aiohttp_session = aiohttp_session
        self._horde_client_session = horde_client_session

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
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable | None = None,
        check_callback_type: type[ResponseWithProgressMixin | ResponseGenerationProgressCombinedMixin] | None = None,
    ) -> tuple[HordeResponse, JobID]:
        """Submit a request which requires check/status polling to the AI-Horde API, and wait for it to complete.

        Args:
            api_request (BaseAIHordeRequest): The request to submit.
            number_of_responses (int, optional): The number of responses to expect. Defaults to 1.
            timeout (int, optional): The number of seconds to wait before aborting.
                returns any completed images at the end of the timeout. Defaults to DEFAULT_GENERATION_TIMEOUT.

        Returns:
            tuple[HordeResponse, JobID]: The final response and the corresponding job ID.

        Raises:
            AIHordeRequestError: If the request failed. The error response is included in the exception.
        """

        if check_callback is not None and len(inspect.getfullargspec(check_callback).args) == 0:
            raise ValueError("Callback must take at least one argument")

        context: contextlib.AbstractContextManager | AIHordeAPIAsyncClientSession
        ai_horde_session: AIHordeAPIAsyncClientSession

        if self._horde_client_session is not None:
            # Use a dummy context manager to keep the type checker happy
            context = contextlib.nullcontext()
            ai_horde_session = self._horde_client_session
        elif self._aiohttp_session is not None:
            ai_horde_session = AIHordeAPIAsyncClientSession(self._aiohttp_session)
            context = ai_horde_session

        # This session class will cleanup incomplete requests in the event of an exception
        async with context:  # type: ignore
            # Submit the initial request
            logger.debug(
                f"Submitting request: {api_request.log_safe_model_dump()} with timeout {timeout}",
            )
            initial_response = await ai_horde_session.submit_request(
                api_request=api_request,
                expected_response_type=api_request.get_default_success_response_type(),
            )

            # Handle the initial response to get the check request, job ID, and follow-up data
            check_request, job_id, follow_up_data = self._handle_initial_response(initial_response)

            # There is a rate limit, so we start a clock to keep track of how long we've been waiting
            start_time = time.time()
            check_count = 0
            check_response: HordeResponse

            # Wait for the image generation to complete, checking every 4 seconds
            while True:
                check_count += 1

                # Submit the check request
                check_response = await ai_horde_session.submit_request(
                    api_request=check_request,
                    expected_response_type=check_request.get_default_success_response_type(),
                )

                # Handle the progress response to determine if the job is finished or timed out
                progress_state = self._handle_progress_response(
                    check_request,
                    check_response,
                    job_id,
                    check_count=check_count,
                    number_of_responses=number_of_responses,
                    start_time=start_time,
                    timeout=timeout,
                    check_callback=check_callback,
                    check_callback_type=check_callback_type,
                )

                if progress_state == _PROGRESS_STATE.finished or progress_state == _PROGRESS_STATE.timed_out:
                    break

                # Wait for 4 seconds before checking again
                await asyncio.sleep(4)

            # This is for type safety, but should never happen in production
            if not isinstance(check_response, ResponseWithProgressMixin):  # pragma: no cover
                raise RuntimeError(f"Response did not have progress: {check_response}")

            # Get the finalize request type from the check response
            finalize_request_type = check_response.get_finalize_success_request_type()

            # Set the final response to the check response by default
            final_response: HordeResponse = check_response

            # If there is a finalize request type, submit the finalize request
            if finalize_request_type:
                finalize_request = finalize_request_type.model_validate(follow_up_data[0])

                # This is for type safety, but should never happen in production
                if not isinstance(finalize_request, JobRequestMixin):  # pragma: no cover
                    logger.error(
                        f"Finalize request type is not a JobRequestMixin: {finalize_request.log_safe_model_dump()}",
                    )
                    raise RuntimeError(
                        f"Finalize request type is not a JobRequestMixin: {finalize_request.log_safe_model_dump()}",
                    )

                final_response = await ai_horde_session.submit_request(
                    api_request=finalize_request,
                    expected_response_type=finalize_request.get_default_success_response_type(),
                )

                if isinstance(final_response, RequestErrorResponse):
                    raise AIHordeRequestError(final_response)

            # Log a message indicating that the request is complete
            logger.log(COMPLETE_LOGGER_LABEL, f"Request complete: {job_id}")

            # Return the final response and job ID
            return (final_response, job_id)

        # If there we get to this point, something catastrophic has happened
        # Log an error and raise a CancelledError to kill the coroutine task
        logger.error("Something went wrong with the request (was it cancelled?):")
        logger.error(f"Request: {api_request.log_safe_model_dump()}")
        raise asyncio.CancelledError("Something went wrong with the request")

    async def image_generate_request(
        self,
        image_gen_request: ImageGenerateAsyncRequest,
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable[[ImageGenerateCheckResponse], None] | None = None,
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

        timeout = self.validate_timeout(timeout, log_message=True)

        n = image_gen_request.params.n if image_gen_request.params and image_gen_request.params.n else 1
        final_response, job_id = await self._do_request_with_check(
            image_gen_request,
            number_of_responses=n,
            timeout=timeout,
            check_callback=check_callback,
            check_callback_type=ImageGenerateCheckResponse,
        )

        if isinstance(final_response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(final_response)

        if not isinstance(final_response, ImageGenerateStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an ImageGenerateStatusResponse")

        return (final_response, job_id)

    async def alchemy_request(
        self,
        alchemy_request: AlchemyAsyncRequest,
        timeout: int = GENERATION_MAX_LIFE,
        check_callback: Callable[[AlchemyStatusResponse], None] | None = None,
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
        timeout = self.validate_timeout(timeout, log_message=True)

        response, job_id = await self._do_request_with_check(
            alchemy_request,
            number_of_responses=len(alchemy_request.forms),
            timeout=timeout,
            check_callback=check_callback,
            check_callback_type=AlchemyStatusResponse,
        )
        if isinstance(response, RequestErrorResponse):  # pragma: no cover
            raise AIHordeRequestError(response)

        if not isinstance(response, AlchemyStatusResponse):  # pragma: no cover
            raise RuntimeError("Response was not an AlchemyAsyncResponse")

        return (response, job_id)
