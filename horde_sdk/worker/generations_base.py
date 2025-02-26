from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from io import BytesIO
from typing import Generic, TypeVar

from loguru import logger

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    base_generate_progress_transitions,
)

GenerationResultType = TypeVar("GenerationResultType")


class HordeSingleGeneration(ABC, Generic[GenerationResultType]):
    """Base class for individual generations.

    **Not to be confused with a *job***, which can contain multiple generations.

    Note that this class is *not* thread-safe as it represents a state machine and should not be handled from multiple
    threads. Many assumptions are made about the linear progression of the generation process, and these assumptions
    would be violated if multiple threads were to interact with the same instance of this class.

    See `GENERATION_PROGRESS` for the possible states a generation can be in.
    """

    _generate_progress_transitions: Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]
    _state_error_limits: Mapping[GENERATION_PROGRESS, int] | None

    @classmethod
    def default_generate_progress_transitions(cls) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        """Get the default generation progress transitions."""
        return base_generate_progress_transitions

    @classmethod
    def does_class_require_generation(cls) -> bool:
        """Whether or not the generation steps are mandatory for this generation class."""
        return True

    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        """Whether or not the generation requires a safety check."""
        return True

    _extra_logging: bool = True

    _result_type: type

    @property
    def result_type(self) -> type:
        """The type of the result of the generation."""
        return self._result_type

    def __init__(
        self,
        *,
        generation_id: GENERATION_ID_TYPES,
        result_type: type,
        requires_generation: bool = True,
        requires_post_processing: bool = False,
        requires_safety_check: bool = True,
        state_error_limits: Mapping[GENERATION_PROGRESS, int] | None = None,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            Iterable[GENERATION_PROGRESS],
        ] = base_generate_progress_transitions,
        extra_logging: bool = True,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (str): The unique identifier for the generation.
            result_type (type): The type of the result of the generation.
            requires_generation (bool, optional): Whether or not the generation requires generation (inference, etc). \
                Defaults to True.
            requires_post_processing (bool, optional): Whether or not the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether or not the generation requires a safety check. \
                Defaults to True.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to None.
            generate_progress_transitions (dict[GenerationProgress, list[GenerationProgress]], optional): The \
                transitions that are allowed between generation states. \
                Defaults to `base_generate_progress_transitions` (found in consts.py).
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.

        Raises:
            ValueError: If generate_progress_transitions is None.
            ValueError: If generation_id is None.
            ValueError: If the generation class requires generation but requires_generation is False.
            ValueError: If the generation class requires a safety check but requires_safety_check is False.
        """
        if generation_id is None:
            raise ValueError("generation_id must not be None")

        self.generation_id = generation_id
        self._result_type = result_type

        self._extra_logging = extra_logging

        if self.does_class_require_generation() and not requires_generation:
            raise ValueError("Generation class requires generation but requires_generation is False")

        self._requires_generation = requires_generation
        self._requires_post_processing = requires_post_processing

        if self.does_class_require_safety_check() and not requires_safety_check:
            raise ValueError("Generation class requires safety check but requires_safety_check is False")

        self._requires_safety_check = requires_safety_check

        if generate_progress_transitions is None:
            raise ValueError("generate_progress_transitions cannot be None")

        self._generate_progress_transitions = generate_progress_transitions

        self._errored_states = []

        self._state_error_limits = state_error_limits
        self._generation_failed_messages = []
        self._generation_failure_exceptions = []

        # This initialization is critical. The first state must be NOT_STARTED and ERROR must not be the next state.
        # Errors are only allowed after the first "action" state where something is done.
        self._progress_history = [(GENERATION_PROGRESS.NOT_STARTED, time.time())]

    generation_id: GENERATION_ID_TYPES

    # TODO
    # FIXME
    # _generation_metadata: list[GenMetadataEntry]

    # @property
    # def generation_metadata(self) -> list[GenMetadataEntry]:
    #     """The metadata for the generation."""
    #     return self._generation_metadata.copy()

    # def add_metadata_entry(self, entry: GenMetadataEntry) -> None:
    #     """Add a metadata entry to the generation.

    #     Generation metadata includes information about the generation process, such as when errors were encountered
    # or
    #     if the generation was censored (either by user request or due to safety checks).
    #     """
    #     self._generation_metadata.append(entry)

    _generation_failure_count: int = 0
    """The number of times the generation has failed."""

    @property
    def generation_failure_count(self) -> int:
        """The number of times the generation has failed during any step of the generation process."""
        return self._generation_failure_count

    def get_generation_progress(self) -> GENERATION_PROGRESS:
        """Return the state of the generation."""
        return self._generation_progress

    _progress_history: list[tuple[GENERATION_PROGRESS, float]]
    """A list of tuples containing all of the generation states and the time they were set."""

    _errored_states: list[tuple[GENERATION_PROGRESS, float]]

    @property
    def errored_states(self) -> list[tuple[GENERATION_PROGRESS, float]]:
        """Return a tuple of states which occurred just before an error state and the time they were set."""
        return self._errored_states

    def get_progress_history(self) -> list[tuple[GENERATION_PROGRESS, float]]:
        """Get the generation progress history."""
        return self._progress_history.copy()

    _generation_progress: GENERATION_PROGRESS = GENERATION_PROGRESS.NOT_STARTED

    _generation_failed_messages: list[str]
    """The reasons the generation failed."""
    _generation_failure_exceptions: list[Exception]
    """The exceptions that caused the generation to fail."""

    _requires_post_processing: bool = False

    @property
    def requires_post_processing(self) -> bool:
        """Whether or not the generation requires post-processing."""
        return self._requires_post_processing

    _requires_generation: bool = False

    @property
    def requires_generation(self) -> bool:
        """Whether or not the generation requires generation."""
        return self._requires_generation

    _requires_safety_check: bool = False

    @property
    def requires_safety_check(self) -> bool:
        """Whether or not the generation requires a safety check."""
        return self._requires_safety_check

    @staticmethod
    @abstractmethod
    def result_to_bytesio(result: GenerationResultType, buffer: BytesIO) -> None:
        """Write the result to a BytesIO buffer."""

    def _extra_log(self) -> Callable[[str], None]:
        """Log a message at debug level if extra logging is enabled or trace level if it is not."""
        if self._extra_logging:
            return logger.debug

        return logger.trace

    def _add_failure_message(self, message: str, exception: Exception | None = None) -> None:
        """Add a message to the list of reasons the generation failed."""
        self._generation_failed_messages.append(message)

        if exception is not None:
            if self._generation_failure_exceptions is None:
                self._generation_failure_exceptions = []
            self._generation_failure_exceptions.append(exception)

    def _set_generation_progress(
        self,
        next_state: GENERATION_PROGRESS,
        *,
        failed_message: str | None = None,
        failure_exception: Exception | None = None,
    ) -> GENERATION_PROGRESS:
        """Set the generation progress to the next state.

        Args:
            next_state (GENERATION_PROGRESS): The state to transition to.
            failed_message (str, optional): The reason the generation failed at this step. \
                Use this for errors that make the current step impossible to complete without intervention.
                For example, if a sub-process is OOM killed.

                Use `add_metadata_entry` for non-critical errors.

                Defaults to None.

            failure_exception (Exception, optional): The exception that caused the generation to fail at this step. \
                Defaults to None.

        Returns:
            GENERATION_PROGRESS: The new state of the generation.

        Raises:
            ValueError: If the transition is invalid.
        """
        if next_state == GENERATION_PROGRESS.ABORTED and failed_message is None:
            logger.error("Faulted reason should be set when transitioning to FAULTED")

        if failed_message is not None:
            self._add_failure_message(failed_message, failure_exception)

        current_state = self._generation_progress

        if current_state == next_state:
            raise ValueError(f"Generation {self.generation_id} is already in state {current_state}")

        transition_log_string = (
            f"Attempting transitioning generation {self.generation_id} from {current_state} to {next_state}. "
        )
        if failed_message is not None:
            transition_log_string += f"Reason: {failed_message}. "
        if failure_exception is not None:
            transition_log_string += f"Exception: {failure_exception}. "

        self._extra_log()(transition_log_string)

        if current_state == GENERATION_PROGRESS.ERROR and len(self._progress_history) < 2:
            raise RuntimeError("Cannot transition from error state without a history!")

        last_non_error_state, last_non_error_state_time = (
            (current_state, 0.0) if current_state != GENERATION_PROGRESS.ERROR else self._progress_history[-2]
        )

        if current_state == GENERATION_PROGRESS.ERROR:
            self._extra_log()(f"Generation {self.generation_id} last non-error state was {last_non_error_state}")
            self._errored_states.append((last_non_error_state, last_non_error_state_time))

        if next_state == last_non_error_state:
            self._extra_log()(f"Retrying state {next_state} after error")
        elif next_state not in self._generate_progress_transitions[last_non_error_state]:
            self._extra_log()(
                f"{self._progress_history=}, {self._generation_progress=}, {next_state=}, "
                f"{self._generate_progress_transitions=}",
            )
            raise ValueError(f"Invalid transition from {current_state} to {next_state}")

        self._extra_log()(f"Generation {self.generation_id} progress history: {self._progress_history}")
        self._generation_progress = next_state
        self._progress_history.append((next_state, time.monotonic()))

        return next_state

    def on_error(self, *, failed_message: str, failure_exception: Exception | None = None) -> None:
        """Call when an error occurs at any point in the generation process, safety checks, or submission.

        This should be reserved for errors which make the current step **impossible** to complete. For example, if the
        a sub-process is OOM killed.

        Contrast with the `add_metadata_entry` method, which is used for non-critical errors. If there is no
        METADATA_TYPE for the error you encountered, you can use `failed_message` and `failure_exception` instead.

        Args:
            failed_message (str): The reason the generation failed.
            failure_exception (Exception, optional): The exception that caused the generation to fail. \
                Defaults to None.
        """
        self._generation_failure_count += 1
        self._set_generation_progress(
            GENERATION_PROGRESS.ERROR,
            failed_message=failed_message,
            failure_exception=failure_exception,
        )

    def on_abort(self, *, failed_message: str, failure_exception: Exception | None = None) -> None:
        """Call when the generation is aborted.

        Args:
            failed_message (str): The reason the generation was aborted.
            failure_exception (Exception, optional): The exception that caused the generation to be aborted. \
                Defaults to None.
        """
        self._set_generation_progress(
            GENERATION_PROGRESS.ABORTED,
            failed_message=failed_message,
            failure_exception=failure_exception,
        )

    def on_preloading(self) -> None:
        """Call when preloading is about to begin."""
        self._set_generation_progress(GENERATION_PROGRESS.PRELOADING)

    def on_preloading_complete(self) -> None:
        """Call after preloading is complete."""
        self._set_generation_progress(GENERATION_PROGRESS.PRELOADING_COMPLETE)

    def _work_complete(self) -> None:

        if GENERATION_PROGRESS.PENDING_SAFETY_CHECK in self._generate_progress_transitions[self._generation_progress]:
            self._set_generation_progress(GENERATION_PROGRESS.PENDING_SAFETY_CHECK)
        else:
            self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)

    def on_generation_work_complete(self) -> None:
        """Call when the generation work is complete, such as when inference is done.

        This does not mean the generation is finalized, as calling this function means that safety checks and
        submission may still be pending. Examples of when this function would be called are when comfyui has
        just returned an image, interrogating an image has just completed or when a text backend has just generated
        text.
        """
        if self.requires_post_processing:
            self._set_generation_progress(GENERATION_PROGRESS.PENDING_POST_PROCESSING)
        else:
            self._work_complete()

    def on_generating(self) -> None:
        """Call when the generation is about to begin."""
        self._set_generation_progress(GENERATION_PROGRESS.GENERATING)

    def on_post_processing(self) -> None:
        """Call when post-processing is about to begin."""
        self._set_generation_progress(GENERATION_PROGRESS.POST_PROCESSING)

    def on_post_processing_complete(self) -> None:
        """Call when post-processing is complete."""
        self._work_complete()

    def set_work_result(self, result: GenerationResultType) -> None:
        """Set the result of the generation work.

        Args:
            result (Any): The result of the generation work.
        """
        self._set_generation_work_result(result)

    _generation_result: GenerationResultType | None = None

    def on_state(
        self,
        state: GENERATION_PROGRESS,
    ) -> None:
        """Call when the generation state is updated.

        Args:
            state (GENERATION_PROGRESS): The new state of the generation.
        """
        match state:
            case GENERATION_PROGRESS.PRELOADING:
                self.on_preloading()
            case GENERATION_PROGRESS.PRELOADING_COMPLETE:
                self.on_preloading_complete()
            case GENERATION_PROGRESS.GENERATING:
                self.on_generating()
            case GENERATION_PROGRESS.POST_PROCESSING:
                self.on_post_processing()
            case GENERATION_PROGRESS.PENDING_POST_PROCESSING:
                self.on_post_processing_complete()
            case GENERATION_PROGRESS.SAFETY_CHECKING:
                self.on_safety_checking()
            case GENERATION_PROGRESS.PENDING_SUBMIT:
                self.on_safety_check_complete(is_nsfw=False, is_csam=False)
            case GENERATION_PROGRESS.SUBMITTING:
                self.on_submitting()
            case GENERATION_PROGRESS.SUBMIT_COMPLETE:
                self.on_submit_complete()
            case _:
                raise ValueError(f"Invalid state {state} (current state: {self._generation_progress})")

    def step(self, state: GENERATION_PROGRESS) -> None:
        """Call when the generation state is updated.

        Args:
            state (GENERATION_PROGRESS): The new state of the generation.
        """
        self.on_state(state)

    @property
    def generation_result(self) -> GenerationResultType | None:
        """Get the result of the generation."""
        return self._generation_result

    def _set_generation_work_result(self, result: GenerationResultType) -> None:
        """Set the result of the generation work.

        Args:
            result (Any): The result of the generation work.
        """
        self._generation_result = result

    _is_nsfw: bool | None = None
    _is_csam: bool | None = None

    @property
    def is_nsfw(self) -> bool | None:
        """Whether or not the generation is NSFW."""
        return self._is_nsfw

    @property
    def is_csam(self) -> bool | None:
        """Whether or not the generation is CSAM."""
        return self._is_csam

    def _set_safety_check_result(
        self,
        *,
        is_nsfw: bool,
        is_csam: bool,
    ) -> None:
        """Set the result of the safety check.

        Args:
            is_nsfw (bool): Whether or not the generation is NSFW.
            is_csam (bool): Whether or not the generation is CSAM.

        Raises:
            ValueError: If is_nsfw or is_csam is not provided or is `None`.
        """
        if is_nsfw is None:
            raise ValueError("is_nsfw must be provided")

        if is_csam is None:
            raise ValueError("is_csam must be provided")

        if self.generation_result is None:
            raise ValueError("Generation result must be set before setting safety check result")

        self._is_nsfw = is_nsfw
        self._is_csam = is_csam

    def on_safety_checking(self) -> None:
        """Call when the safety check is about to start."""
        self._set_generation_progress(GENERATION_PROGRESS.SAFETY_CHECKING)

    def on_safety_check_complete(self, *, is_nsfw: bool, is_csam: bool) -> None:
        """Call when the safety check is complete.

        Args:
            is_nsfw (bool): Whether or not the generation is NSFW.
            is_csam (bool): Whether or not the generation is CSAM.
        """
        self._set_safety_check_result(is_nsfw=is_nsfw, is_csam=is_csam)
        self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)

    def on_submitting(self) -> None:
        """Call when an attempt is going to be made to submit the generation."""
        self._set_generation_progress(GENERATION_PROGRESS.SUBMITTING)

    def on_submit_complete(self) -> None:
        """Call when the generation has been successfully submitted."""
        self._set_generation_progress(GENERATION_PROGRESS.SUBMIT_COMPLETE)

    def on_user_requested_abort(self) -> None:
        """Call when the user requests to abort the generation."""
        self._set_generation_progress(GENERATION_PROGRESS.USER_REQUESTED_ABORT)

    def on_user_abort_complete(self) -> None:
        """Call when the user requested abort is complete."""
        self._set_generation_progress(GENERATION_PROGRESS.USER_ABORT_COMPLETE)
