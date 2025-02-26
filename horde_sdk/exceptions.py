from typing import Any

from loguru import logger


class HordeException(Exception):
    """Base exception for all Horde SDK exceptions."""


class PayloadValidationError(HordeException):
    """Exception for when the API cannot parse a request payload."""

    def __init__(self, errors: dict[str, Any], message: str) -> None:
        """Exception for when the AI Horde API cannot parse a request payload."""
        logger.error(f"The AI Horde API returned an error response. Response: {message}. Errors: {errors}")
        super().__init__(message)
