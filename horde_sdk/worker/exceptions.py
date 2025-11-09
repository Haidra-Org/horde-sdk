from horde_sdk.consts import ID_TYPES
from horde_sdk.worker.consts import GENERATION_PROGRESS


class GenerationStateException(Exception):
    """Raised when there is an error in the generation state."""

    def __init__(self, message: str) -> None:
        """Initialize the generation state exception with a given message."""
        super().__init__(message)


class GenerationStateErrorLimitExceeded(GenerationStateException):
    """Raised when the generation state exceeds the allowed error limit."""

    def __init__(
        self,
        generation_id: ID_TYPES,
        error_limit: int,
        last_non_error_state: GENERATION_PROGRESS,
    ) -> None:
        """Initialize the state error limit exceeded exception.

        Args:
            generation_id (ID_TYPES): The unique identifier for the generation.
            error_limit (int): The maximum number of errors allowed.
            last_non_error_state (GENERATION_PROGRESS): The last non-error state of the generation.
        """
        message = (
            f"Generation {generation_id} has exceeded the error limit of {error_limit}. "
            f"Last non-error state was {last_non_error_state}."
        )
        super().__init__(message)
        self.generation_id = generation_id
        self.error_limit = error_limit
        self.last_non_error_state = last_non_error_state
