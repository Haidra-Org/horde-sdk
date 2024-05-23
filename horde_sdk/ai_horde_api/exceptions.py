from typing import Any

from loguru import logger

from horde_sdk.ai_horde_api.consts import GENERATION_MAX_LIFE, RC
from horde_sdk.exceptions import HordeException
from horde_sdk.generic_api.apimodels import RequestErrorResponse


class AIHordeRequestError(HordeException):
    """Exception for when the AI Horde API returns an error response."""

    def __init__(self, error_response: RequestErrorResponse) -> None:  # noqa: D107
        logger.error(f"The AI Horde API returned an error response. Response: {error_response.message}")
        super().__init__(error_response.message)
        try:
            RC(error_response.rc)
        except ValueError:
            logger.error(
                f"Failed to parse the RC from the error response. RC: {error_response.rc}. Is the SDK out of date?",
            )


class AIHordePayloadValidationError(HordeException):
    """Exception for when the AI Horde API cannot parse a request payload."""

    def __init__(self, errors: dict[str, Any], message: str) -> None:
        """Exception for when the AI Horde API cannot parse a request payload."""
        logger.error(f"The AI Horde API returned an error response. Response: {message}. Errors: {errors}")
        super().__init__(message)


class AIHordeImageValidationError(AIHordeRequestError):
    """Exception for when the AI Horde API cannot parse a source image for img2img."""


class AIHordeGenerationTimedOutError(HordeException):
    """Exception for when the time limit for a generation request is reached."""

    def __init__(self, error_response: RequestErrorResponse) -> None:  # noqa: D107
        logger.error(
            f"The AI Horde API returned an error response. Response: {error_response.message}. "
            "This is likely because the generation timed out. "
            f"The default timeout is {GENERATION_MAX_LIFE} seconds.",
        )
        super().__init__(error_response)


class AIHordeServerException(HordeException):
    """Base exception for any case where the AI Horde API returns a `RequestErrorResponse` and it was not handled."""

    def __init__(
        self,
        *,
        message: str = "The AI Horde API returned an error response and it wasn't handled.",
        error_response: RequestErrorResponse,
    ) -> None:
        """Initialize the exception.

        Args:
            message: The message to display to the user.
            error_response: The error response returned by the AI Horde API.
        """
        logger.error(f"The AI Horde API returned an error response and it wasn't handled. Response: {error_response}")
        if error_response.object_data is not None:
            logger.error(f"Response object data: {error_response.object_data}")
        super().__init__(message)
