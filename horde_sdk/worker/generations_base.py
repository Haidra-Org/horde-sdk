from __future__ import annotations

import threading
import time
import uuid
from abc import ABC
from collections import OrderedDict
from collections.abc import Callable, Collection, Iterable, Mapping
from typing import Generic, TypeVar

from loguru import logger

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters.generic import ComposedParameterSetBase
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    base_generate_progress_no_submit_transitions,
    base_generate_progress_transitions,
)

GenerationResultTypeVar = TypeVar("GenerationResultTypeVar")


class HordeSingleGeneration(ABC, Generic[GenerationResultTypeVar]):
    """Base class for individual generations. Generations are specific instances of inference or computation.

    This should not be confused with specific results, which are the output of a generation. For example, a generation
    could result in several images, but as the result of a single round of inference. The generation is the process of
    generating the images, while the images are the result of that generation.

    See `GENERATION_PROGRESS` for the possible states a generation can be in.
    """

    _generate_progress_transitions: Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]
    _state_error_limits: Mapping[GENERATION_PROGRESS, int] | None

    @classmethod
    def default_generate_progress_transitions(cls) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        """Get the default generation progress transitions."""
        return base_generate_progress_transitions

    @classmethod
    def default_generate_progress_transitions_no_submit(
        cls,
    ) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        """Get the default generation progress transitions without submission."""
        return base_generate_progress_no_submit_transitions

    @classmethod
    def does_class_require_generation(cls) -> bool:
        """Whether or not the generation steps are mandatory for this generation class."""
        return True

    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        """Whether or not the generation requires a safety check."""
        return True

    _extra_logging: bool = True

    _result_type: type[GenerationResultTypeVar]

    @property
    def result_type(self) -> type[GenerationResultTypeVar]:
        """The type of the result of the generation."""
        return self._result_type

    _batch_size: int = 1
    """The batch size of the generation."""

    @property
    def batch_size(self) -> int:
        """The batch size of the generation."""
        return self._batch_size

    _batch_ids: list[GENERATION_ID_TYPES]

    @property
    def batch_ids(self) -> list[GENERATION_ID_TYPES] | None:
        """The unique identifiers for the generations in the batch."""
        with self._lock:
            return self._batch_ids.copy() if self._batch_ids is not None else None

    _lock: threading.RLock

    _strict_transition_mode: bool

    def __init__(
        self,
        *,
        generation_parameters: ComposedParameterSetBase,
        result_type: type[GenerationResultTypeVar] | None = None,
        generation_id: GENERATION_ID_TYPES | None = None,
        batch_ids: list[GENERATION_ID_TYPES] | None = None,
        requires_generation: bool = True,
        requires_post_processing: bool = False,
        requires_safety_check: bool = True,
        requires_submit: bool = True,
        state_error_limits: Mapping[GENERATION_PROGRESS, int] | None = None,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            Iterable[GENERATION_PROGRESS],
        ] = base_generate_progress_transitions,
        strict_transition_mode: bool = True,
        extra_logging: bool = True,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_parameters (ComposedParameterSetBase): The parameters for the generation.
            result_type (type): The type of the result of the generation.
            generation_id (str | None): The unique identifier for the generation. \
                If None, a new UUID will be generated.
            batch_ids (list[GENERATION_ID_TYPES] | None): The unique identifiers for the results of the generation.
                If None, a new UUID will be generated for each generation in the batch.
            requires_generation (bool, optional): Whether or not the generation requires generation (inference, etc). \
                Defaults to True.
            requires_post_processing (bool, optional): Whether or not the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether or not the generation requires a safety check. \
                Defaults to True.
            requires_submit (bool, optional): Whether or not the generation requires submission. \
                Defaults to True.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to None.
            generate_progress_transitions (dict[GenerationProgress, list[GenerationProgress]], optional): The \
                transitions that are allowed between generation states. \
                Defaults to `base_generate_progress_transitions` (found in consts.py).
            strict_transition_mode (bool, optional): Whether or not to enforce strict transition checking. \
                This prevents setting the same state multiple times in a row. \
                Defaults to True.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.

        Raises:
            ValueError: If result_type is None.
            ValueError: If the result type is not iterable but the batch size is greater than 1.
            ValueError: If batch_ids is not None and its length does not match the batch size.
            ValueError: If generate_progress_transitions is None.
            ValueError: If the generation class requires generation but requires_generation is False.
            ValueError: If the generation class requires a safety check but requires_safety_check is False.
        """
        if result_type is None:
            raise ValueError("result_type cannot be None")

        if generation_id is None:
            logger.debug("Generation ID is None, creating a new one.")
            generation_id = uuid.uuid4()

        self.generation_id = generation_id
        self.generation_parameters = generation_parameters

        self._result_type = result_type
        self._batch_size = generation_parameters.get_number_expected_results()

        if self._batch_size > 1 and not issubclass(
            self._result_type,
            Iterable,
        ):
            raise ValueError(
                f"Result type {self._result_type} is not iterable, but batch size is {self._batch_size}",
            )
        if batch_ids is not None and len(batch_ids) != self._batch_size:
            raise ValueError(
                f"Batch IDs length {len(batch_ids)} does not match batch size {self._batch_size}",
            )

        if batch_ids is None:
            logger.trace("Batch IDs are None, creating new ones.")
            batch_ids = [uuid.uuid4() for _ in range(self._batch_size)]

        self._batch_ids = batch_ids

        self._extra_logging = extra_logging

        if self.does_class_require_generation() and not requires_generation:
            raise ValueError("Generation class requires generation but requires_generation is False")

        self._requires_generation = requires_generation
        self._requires_post_processing = requires_post_processing

        if self.does_class_require_safety_check() and not requires_safety_check:
            raise ValueError("Generation class requires safety check but requires_safety_check is False")

        self._requires_safety_check = requires_safety_check

        self._requires_submit = requires_submit

        if generate_progress_transitions is None:
            raise ValueError("generate_progress_transitions cannot be None")

        self._generate_progress_transitions = generate_progress_transitions

        self._errored_states = []
        self._error_counts = {}

        self._state_error_limits = state_error_limits
        self._generation_failed_messages = []
        self._generation_failure_exceptions = []

        # This initialization is critical. The first state must be NOT_STARTED and ERROR must not be the next state.
        # Errors are only allowed after the first "action" state where something is done.
        self._progress_history = [(GENERATION_PROGRESS.NOT_STARTED, time.time())]

        self._lock = threading.RLock()

        self._strict_transition_mode = strict_transition_mode

    generation_id: GENERATION_ID_TYPES
    """Unique identifier for the generation."""

    generation_parameters: ComposedParameterSetBase
    """The parameters for the generation."""

    _generation_failure_count: int = 0
    """The number of times the generation has failed."""

    @property
    def generation_failure_count(self) -> int:
        """The number of times the generation has failed during any step of the generation process."""
        with self._lock:
            return self._generation_failure_count

    def get_generation_progress(self) -> GENERATION_PROGRESS:
        """Return the state of the generation."""
        with self._lock:
            return self._generation_progress

    _progress_history: list[tuple[GENERATION_PROGRESS, float]]
    """A list of tuples containing all of the generation states and the time they were set."""

    _errored_states: list[tuple[GENERATION_PROGRESS, float]]
    _error_counts: dict[GENERATION_PROGRESS, int]

    @property
    def errored_states(self) -> list[tuple[GENERATION_PROGRESS, float]]:
        """Return a tuple of states which occurred just before an error state and the time they were set."""
        with self._lock:
            return self._errored_states.copy()

    @property
    def error_counts(self) -> dict[GENERATION_PROGRESS, int]:
        """Return a dictionary of states and the number of times they occurred before an error state."""
        with self._lock:
            return self._error_counts.copy()

    def get_progress_history(self) -> list[tuple[GENERATION_PROGRESS, float]]:
        """Get the generation progress history."""
        with self._lock:
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

    _requires_submit: bool = False
    """Whether or not the generation requires submission."""

    @property
    def requires_submit(self) -> bool:
        """Whether or not the generation requires submission."""
        return self._requires_submit

    def _extra_log(self) -> Callable[[str], None]:
        """Log a message at debug level if extra logging is enabled or trace level if it is not."""
        if self._extra_logging:
            return logger.debug

        return logger.trace

    def _add_failure_message(self, message: str, exception: Exception | None = None) -> None:
        """Add a message to the list of reasons the generation failed."""
        with self._lock:
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
        with self._lock:
            if next_state == GENERATION_PROGRESS.ABORTED and failed_message is None:
                logger.error("Faulted reason should be set when transitioning to FAULTED")

            if failed_message is not None:
                self._add_failure_message(failed_message, failure_exception)

            current_state = self._generation_progress

            if current_state == next_state:
                if self._strict_transition_mode:
                    raise ValueError(f"Generation {self.generation_id} is already in state {current_state}")
                logger.debug(
                    f"Generation {self.generation_id} is already in state {current_state}, "
                    f"not transitioning to {next_state}",
                )
                return current_state

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
                self._error_counts[last_non_error_state] = self._error_counts.get(last_non_error_state, 0) + 1
            else:
                if next_state == last_non_error_state:
                    self._extra_log()(f"Retrying state {next_state} after error")
                elif next_state not in self._generate_progress_transitions[last_non_error_state]:
                    self._extra_log()(
                        f"{self._progress_history=}, {self._generation_progress=}, {next_state=}, "
                        f"{self._generate_progress_transitions=}",
                    )
                    raise ValueError(f"Invalid transition from {current_state} to {next_state}")

            error_count_exceeded = False

            if self._state_error_limits is not None:
                error_count_exceeded = self._error_counts.get(next_state, 0) >= self._state_error_limits.get(
                    next_state,
                    float("inf"),
                )

            if error_count_exceeded:
                raise RuntimeError(
                    f"Generation {self.generation_id} has exceeded the maximum number of errors "
                    f"for state {next_state}",
                )

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
        with self._lock:
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
            if self._requires_submit:
                self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)
            else:
                self._set_generation_progress(GENERATION_PROGRESS.COMPLETE)

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

    def set_work_result(self, result: GenerationResultTypeVar | Collection[GenerationResultTypeVar]) -> None:
        """Set the result of the generation work.

        Args:
            result (Any): The result of the generation work.
        """
        self._set_generation_work_result(result)

    _generation_results: OrderedDict[GENERATION_ID_TYPES, GenerationResultTypeVar] | None = None

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
    def generation_results(self) -> OrderedDict[GENERATION_ID_TYPES, GenerationResultTypeVar] | None:
        """Get the result of the generation."""
        with self._lock:
            return self._generation_results.copy() if self._generation_results is not None else None

    def _set_generation_work_result(
        self,
        result: GenerationResultTypeVar | Collection[GenerationResultTypeVar],
    ) -> None:
        """Set the result of the generation work.

        Args:
            result (GenerationResultTypeVar): The result of the generation work.
        """
        if (not isinstance(result, self._result_type)) and isinstance(result, Collection):
            for item in result:
                if not isinstance(item, self.result_type):
                    raise ValueError(
                        f"Result type {type(item)} does not match expected type {self.result_type}",
                    )

        elif not isinstance(result, self.result_type):
            raise ValueError(
                f"Result type {type(result)} does not match expected type {self.result_type}",
            )

        with self._lock:
            if self._generation_results is None:
                self._generation_results = OrderedDict()

            if len(self._generation_results) >= self.batch_size:
                raise ValueError(
                    f"Generation result list is full ({len(self._generation_results)}), cannot add more results",
                )

            if isinstance(result, self._result_type):
                self._generation_results[self._batch_ids[len(self._generation_results)]] = result

            elif isinstance(result, Collection):
                if len(result) + len(self._generation_results) > self.batch_size:
                    raise ValueError(
                        f"Result list is full ({len(self._generation_results)}), cannot add more results",
                    )
                if not all(isinstance(r, self.result_type) for r in result):
                    raise ValueError(
                        f"Result type {type(result)} does not match expected type {self.result_type}",
                    )

                for index, passed_result in enumerate(result):
                    self._generation_results[self._batch_ids[len(self._generation_results) + index]] = passed_result

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

        if self.generation_results is None:
            raise ValueError("Generation result must be set before setting safety check result")

        with self._lock:
            self._is_nsfw = is_nsfw
            self._is_csam = is_csam
            # TODO: Batch addressable results w/ automatic delete

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
        if self._requires_submit:
            self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)
        else:
            self._set_generation_progress(GENERATION_PROGRESS.COMPLETE)

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
