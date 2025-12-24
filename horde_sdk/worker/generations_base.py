from __future__ import annotations

import threading
import time
import uuid
from abc import ABC
from collections import OrderedDict
from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from enum import auto
from typing import TypeVar

from loguru import logger
from strenum import StrEnum

from horde_sdk.consts import ID_TYPES
from horde_sdk.generation_parameters.generic import CompositeParametersBase
from horde_sdk.safety import SafetyResult, SafetyRules, default_safety_rules
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    HordeWorkerConfigDefaults,
    base_generate_progress_no_submit_transitions,
    base_generate_progress_transitions,
    black_box_generate_progress_transitions,
    validate_generation_progress_transitions,
)
from horde_sdk.worker.exceptions import GenerationStateErrorLimitExceeded

GenerationResultTypeVar = TypeVar("GenerationResultTypeVar")


class InputCollectionConstraint(StrEnum):
    """Types of constraints for inputs collections."""

    NONE = auto()
    """No constraints."""
    single_only = auto()
    """Single input only."""
    multiple_only = auto()
    """Multiple inputs only."""
    single_or_multiple = auto()
    """Single or multiple inputs allowed."""


class InputConstraintType(StrEnum):
    """Types of constraints for inputs."""

    IMAGE = auto()
    """Image input only."""
    TEXT = auto()
    """Text input only."""
    AUDIO = auto()
    """Audio input only."""
    VIDEO = auto()
    """Video input only."""
    SPECIFIC_CLASS_TYPE = auto()
    """Specific class type input only."""


class HordeSingleGeneration[GenerationResultTypeVar](ABC):
    """Base class for tracking a generation. Generations are specific instances of inference or computation.

    This should not be confused with specific results, which are the output of a generation. For example, a generation
    could result in several images, but as the result of a single round of inference. The generation is the process of
    generating the images, while the images are the result of that generation.

    See `GENERATION_PROGRESS` for the possible states a generation can be in.
    """

    _generate_progress_transitions: Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]
    _state_error_limits: Mapping[GENERATION_PROGRESS, int]

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
    def default_interrupt_states(cls) -> set[GENERATION_PROGRESS]:
        """Get the default interrupt states."""
        return {GENERATION_PROGRESS.ABORTED, GENERATION_PROGRESS.USER_REQUESTED_ABORT, GENERATION_PROGRESS.ABANDONED}

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

    _result_ids: list[ID_TYPES]

    @property
    def result_ids(self) -> list[ID_TYPES]:
        """The unique identifiers for the generations in the batch."""
        with self._lock:
            return self._result_ids.copy()

    _lock: threading.RLock

    _strict_transition_mode: bool

    _black_box_mode: bool

    @property
    def black_box_mode(self) -> bool:
        """Whether or not the generation is in black box mode."""
        return self._black_box_mode

    _registered_callbacks: dict[GENERATION_PROGRESS, list[Callable[[], None]]]

    def register_callback(
        self,
        state: GENERATION_PROGRESS,
        callback: Callable[[], None],
    ) -> None:
        """Register a callback to be called when the generation state is updated.

        Args:
            state (GENERATION_PROGRESS): The state to register the callback for.
            callback (Callable[[], None]): The callback to call when the state is updated.
        """
        with self._lock:
            self._registered_callbacks[state].append(callback)

    _dispatch_result_ids: list[ID_TYPES] | None

    def __init__(
        self,
        *,
        generation_parameters: CompositeParametersBase,
        result_type: type[GenerationResultTypeVar] | None = None,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        result_ids: list[ID_TYPES] | None = None,
        requires_generation: bool = True,
        requires_post_processing: bool = False,
        requires_safety_check: bool = True,
        requires_submit: bool = True,
        safety_rules: SafetyRules = default_safety_rules,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            Iterable[GENERATION_PROGRESS],
        ] = base_generate_progress_transitions,
        black_box_mode: bool = False,
        strict_transition_mode: bool = True,
        extra_logging: bool = True,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_parameters (ComposedParameterSetBase): The parameters for the generation.
            result_type (type): The type of the result of the generation.
            generation_id (str | None): The unique identifier for the generation. \
                If None, a new UUID will be generated.
            dispatch_result_ids (Sequence[str | uuid.UUID] | None): Identifiers provided by the dispatch system for
                each result slot. Defaults to None when the generation has no remote counterpart yet.
            result_ids (list[ID_TYPES] | None): The unique identifiers for the results of the generation.
                If None, a new UUID will be generated for each generation in the batch.
            requires_generation (bool, optional): Whether or not the generation requires generation (inference, etc). \
                Defaults to True.
            requires_post_processing (bool, optional): Whether or not the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether or not the generation requires a safety check. \
                Defaults to True.
            requires_submit (bool, optional): Whether or not the generation requires submission. \
                Defaults to True.
            safety_rules (SafetyRules, optional): The rules to use for safety checking. \
                Defaults to `default_safety_rules` from `horde_sdk.safety`.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to None.
            generate_progress_transitions (dict[GenerationProgress, list[GenerationProgress]], optional): The \
                transitions that are allowed between generation states. \
                Defaults to `base_generate_progress_transitions` (found in consts.py).
            black_box_mode (bool, optional): Whether the generation is in black box mode. \
                This removes all of the intermediate states between starting and finished states. \
                This should only be used when the backend has no observability into the generation process. \
                Defaults to False.
            strict_transition_mode (bool, optional): Whether or not to enforce strict transition checking. \
                This prevents setting the same state multiple times in a row. \
                Defaults to True.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.

        Raises:
            ValueError: If result_type is None.
            ValueError: If the result type is not iterable but the batch size is greater than 1.
            ValueError: If result_ids is not None and its length does not match the batch size.
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
        self._dispatch_result_ids = list(dispatch_result_ids) if dispatch_result_ids is not None else None
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
        if result_ids is not None and len(result_ids) != self._batch_size:
            raise ValueError(
                f"Batch IDs length {len(result_ids)} does not match batch size {self._batch_size}",
            )

        if result_ids is None:
            logger.trace("Batch IDs are None, creating new ones.")
            result_ids = [uuid.uuid4() for _ in range(self._batch_size)]

        self._result_ids = result_ids

        self._generation_results: OrderedDict[ID_TYPES, GenerationResultTypeVar | None] = OrderedDict()

        self._extra_logging = extra_logging

        if self.does_class_require_generation() and not requires_generation:
            raise ValueError("Generation class requires generation but requires_generation is False")

        self._requires_generation = requires_generation
        self._requires_post_processing = requires_post_processing

        if self.does_class_require_safety_check() and not requires_safety_check:
            raise ValueError("Generation class requires safety check but requires_safety_check is False")

        self._requires_safety_check = requires_safety_check
        self._safety_results: list[SafetyResult | None] = [None] * self._batch_size
        self._safety_rules = safety_rules

        self._requires_submit = requires_submit

        if generate_progress_transitions is None and not black_box_mode:
            raise ValueError("generate_progress_transitions cannot be None")

        self._black_box_mode = black_box_mode

        if black_box_mode:
            if generate_progress_transitions != base_generate_progress_transitions:
                logger.trace(
                    "Black box mode is enabled, overriding generate_progress_transitions with "
                    "black_box_generate_progress_transitions.",
                )
            self._generate_progress_transitions = black_box_generate_progress_transitions
        else:
            if not validate_generation_progress_transitions(generate_progress_transitions):
                raise ValueError(
                    "Invalid generate_progress_transitions provided. "
                    "Please ensure it is a valid mapping of GENERATION_PROGRESS to iterable of GENERATION_PROGRESS."
                    "See horde_sdk.worker.consts for the default transitions.",
                )
            self._generate_progress_transitions = generate_progress_transitions

        self._errored_states = []
        self._error_counts = {}

        self._state_error_limits = state_error_limits or {}
        self._generation_failed_messages = []
        self._generation_failure_exceptions = []

        # This initialization is critical. The first state must be NOT_STARTED and ERROR must not be the next state.
        # Errors are only allowed after the first "action" state where something is done.
        self._progress_history = [(GENERATION_PROGRESS.NOT_STARTED, time.time())]

        self._lock = threading.RLock()

        self._strict_transition_mode = strict_transition_mode

        self._registered_callbacks = {}

        for state in self._generate_progress_transitions:
            self._registered_callbacks[state] = []

    generation_id: ID_TYPES
    """Unique identifier for the generation."""

    @property
    def dispatch_result_ids(self) -> list[ID_TYPES] | None:
        """Identifiers supplied by the dispatch source, if any."""
        with self._lock:
            if self._dispatch_result_ids is None:
                return None
            return self._dispatch_result_ids.copy()

    def set_dispatch_result_ids(self, dispatch_result_ids: Sequence[ID_TYPES] | None) -> None:
        """Bind the generation to the result identifiers supplied by dispatch."""
        with self._lock:
            self._dispatch_result_ids = list(dispatch_result_ids) if dispatch_result_ids is not None else None

    @property
    def short_id(self) -> str:
        """Get a short identifier for the generation."""
        return str(self.generation_id)[:8]

    generation_parameters: CompositeParametersBase
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
    _any_error_count_exceeded: bool = False

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

    def get_last_non_error_state(self) -> GENERATION_PROGRESS:
        """Get the last non-error state."""
        with self._lock:
            for state, _ in reversed(self._progress_history):
                if state != GENERATION_PROGRESS.ERROR:
                    return state
            raise RuntimeError("No non-error state found in progress history")

    def get_last_non_error_state_and_time(self) -> tuple[GENERATION_PROGRESS, float]:
        """Get the last non-error state and the time it was set."""
        with self._lock:
            for state, time_set in reversed(self._progress_history):
                if state != GENERATION_PROGRESS.ERROR:
                    return state, time_set
            raise RuntimeError("No non-error state found in progress history")

    def is_next_state_valid(
        self,
        next_state: GENERATION_PROGRESS,
    ) -> bool:
        """Check if the next state is valid."""
        with self._lock:
            if next_state in self.default_interrupt_states():
                return True

            current_state = self._generation_progress

            if self._strict_transition_mode:
                if current_state == next_state:
                    return False

                if self._any_error_count_exceeded:
                    return False

                if current_state == GENERATION_PROGRESS.ERROR and next_state == GENERATION_PROGRESS.ERROR:
                    return False

            if current_state == GENERATION_PROGRESS.ERROR and len(self._progress_history) < 2:
                return False

            state_error_count = self._error_counts.get(next_state, 0)
            state_error_limit = (
                self._state_error_limits.get(next_state, float("inf")) if self._state_error_limits else float("inf")
            )
            error_count_exceeded = state_error_count >= state_error_limit

            if error_count_exceeded:
                return False

        return True

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
            RuntimeError: If error limits have been exceeded or other state transition constraints are violated.
        """
        with self._lock:
            current_state = self._generation_progress

            # Handle failure messages
            if next_state == GENERATION_PROGRESS.ABORTED and failed_message is None:
                logger.error("Faulted reason should be set when transitioning to FAULTED")

            if failed_message is not None:
                self._add_failure_message(failed_message, failure_exception)

            # Check if state is unchanged
            if current_state == next_state:
                if self._strict_transition_mode:
                    raise ValueError(f"Generation {self.generation_id} is already in state {current_state}")
                logger.debug(
                    f"Generation {self.generation_id} is already in state {current_state}, "
                    f"not transitioning to {next_state}",
                )
                return current_state

            transition_log_message = self._build_transition_log_message(
                current_state,
                next_state,
                failed_message,
                failure_exception,
            )
            self._extra_log()(transition_log_message)

            if current_state == GENERATION_PROGRESS.ERROR and len(self._progress_history) < 2:
                raise RuntimeError("Cannot transition from error state without a history!")

            last_non_error_state, last_non_error_state_time = self._get_last_non_error_state(current_state)

            if self._any_error_count_exceeded:
                if self._strict_transition_mode:
                    if next_state not in self._state_error_limits:
                        raise RuntimeError(
                            f"Generation {self.generation_id} has exceeded the maximum number of errors "
                            f"but there is no limit set for {next_state}. This should be impossible.",
                        )
                    raise GenerationStateErrorLimitExceeded(
                        generation_id=self.generation_id,
                        error_limit=self._state_error_limits[next_state],
                        last_non_error_state=last_non_error_state,
                    )
                logger.debug(
                    f"Generation {self.generation_id} has exceeded the maximum number of errors "
                    f"but is transitioning to {next_state}",
                )

            if next_state == GENERATION_PROGRESS.ERROR:
                self._update_error_tracking(last_non_error_state, last_non_error_state_time)
            elif current_state == GENERATION_PROGRESS.ERROR:
                self._extra_log()(f"Generation {self.generation_id} last non-error state was {last_non_error_state}")
            else:
                self._validate_normal_transition(next_state, last_non_error_state)

            if self._check_error_limit_exceeded(next_state):
                self._any_error_count_exceeded = True
                raise RuntimeError(
                    f"Generation {self.generation_id} has exceeded the maximum number of errors "
                    f"for state {next_state}",
                )

            self._extra_log()(f"Generation {self.generation_id} progress history: {self._progress_history}")
            self._generation_progress = next_state
            self._progress_history.append((next_state, time.monotonic()))

            return next_state

    def _build_transition_log_message(
        self,
        current_state: GENERATION_PROGRESS,
        next_state: GENERATION_PROGRESS,
        failed_message: str | None,
        failure_exception: Exception | None,
    ) -> str:
        """Build a log message describing the state transition."""
        message = f"Attempting transitioning generation {self.generation_id} from {current_state} to {next_state}. "
        if failed_message is not None:
            message += f"Reason: {failed_message}. "
        if failure_exception is not None:
            message += f"Exception: {failure_exception}. "
        return message

    def _get_last_non_error_state(self, current_state: GENERATION_PROGRESS) -> tuple[GENERATION_PROGRESS, float]:
        """Get the relevant previous state for transition logic."""
        for state, time_set in reversed(self._progress_history):
            if state != GENERATION_PROGRESS.ERROR:
                return state, time_set

        return current_state, time.monotonic()

    def _update_error_tracking(self, last_state: GENERATION_PROGRESS, last_state_time: float) -> None:
        """Update error tracking when transitioning to an error state."""
        self._errored_states.append((last_state, last_state_time))
        self._error_counts[last_state] = self._error_counts.get(last_state, 0) + 1

    def _validate_normal_transition(self, next_state: GENERATION_PROGRESS, last_state: GENERATION_PROGRESS) -> None:
        """Validate a normal (non-error) state transition."""
        if next_state in self.default_interrupt_states():
            self._extra_log()(f"Generation {self.generation_id} is being interrupted by {next_state}")
        elif next_state not in self._generate_progress_transitions[last_state]:
            self._extra_log()(
                f"{self._progress_history=}, {self._generation_progress=}, {next_state=}, "
                f"{self._generate_progress_transitions=}",
            )
            raise ValueError(f"Invalid transition from {last_state} to {next_state}")
        elif next_state == last_state:
            self._extra_log()(f"Retrying state {next_state} after error")

    def _check_error_limit_exceeded(self, state: GENERATION_PROGRESS) -> bool:
        """Check if the error limit for a state has been exceeded."""
        if self._state_error_limits is None:
            return False

        state_error_count = self._error_counts.get(state, 0)
        state_error_limit = self._state_error_limits.get(state, float("inf"))
        return state_error_count >= state_error_limit

    def on_error(self, *, failed_message: str, failure_exception: Exception | None = None) -> GENERATION_PROGRESS:
        """Call when an error occurs at any point in the generation process, safety checks, or submission.

        This should be reserved for errors which make the current step **impossible** to complete. For example, if the
        a sub-process is OOM killed.

        Contrast with the `add_metadata_entry` method, which is used for non-critical errors. If there is no
        METADATA_TYPE for the error you encountered, you can use `failed_message` and `failure_exception` instead.

        Args:
            failed_message (str): The reason the generation failed.
            failure_exception (Exception, optional): The exception that caused the generation to fail. \
                Defaults to None.

        Returns:
            GENERATION_PROGRESS: The new state of the generation, which will be set to `GENERATION_PROGRESS.ERROR`.

        Raises:
            RuntimeError: If the generation has exceeded the maximum number of errors for the current state.
            RuntimeError: If the generation is in an error state and has no previous state to transition from.
        """
        with self._lock:
            self._generation_failure_count += 1
            return self._set_generation_progress(
                GENERATION_PROGRESS.ERROR,
                failed_message=failed_message,
                failure_exception=failure_exception,
            )

    def on_abort(self, *, failed_message: str, failure_exception: Exception | None = None) -> GENERATION_PROGRESS:
        """Call when the generation is aborted.

        Args:
            failed_message (str): The reason the generation was aborted.
            failure_exception (Exception, optional): The exception that caused the generation to be aborted. \
                Defaults to None.

        Returns:
            GENERATION_PROGRESS: The new state of the generation, which will be set to `GENERATION_PROGRESS.ABORTED`.

        Raises:
            RuntimeError: If the generation has exceeded the maximum number of errors for the current state.
            RuntimeError: If the generation is in an error state and has no previous state to transition from.

        """
        return self._set_generation_progress(
            GENERATION_PROGRESS.ABORTED,
            failed_message=failed_message,
            failure_exception=failure_exception,
        )

    def on_preloading(self) -> GENERATION_PROGRESS:
        """Call when preloading is about to begin."""
        return self._set_generation_progress(GENERATION_PROGRESS.PRELOADING)

    def on_preloading_complete(self) -> GENERATION_PROGRESS:
        """Call after preloading is complete."""
        return self._set_generation_progress(GENERATION_PROGRESS.PRELOADING_COMPLETE)

    def _work_complete(self) -> GENERATION_PROGRESS:
        if self._black_box_mode:
            return self._generation_progress

        if self._requires_safety_check:
            return self._set_generation_progress(GENERATION_PROGRESS.PENDING_SAFETY_CHECK)

        if self._requires_submit:
            return self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)

        return self._set_generation_progress(GENERATION_PROGRESS.COMPLETE)

    def on_generation_work_complete(
        self,
        result: GenerationResultTypeVar | Collection[GenerationResultTypeVar] | None = None,
    ) -> GENERATION_PROGRESS:
        """Call when the generation work is complete, such as when inference is done.

        This does not mean the generation is finalized, as calling this function means that safety checks and
        submission may still be pending. Examples of when this function would be called are when comfyui has
        just returned an image, interrogating an image has just completed or when a text backend has just generated
        text.
        """
        if self.requires_post_processing and not self._black_box_mode:
            return self._set_generation_progress(GENERATION_PROGRESS.PENDING_POST_PROCESSING)

        work_complete_progress = self._work_complete()
        if result is not None:
            self._set_generation_work_result(result)
        return work_complete_progress

    def on_generating(self) -> GENERATION_PROGRESS:
        """Call when the generation is about to begin."""
        return self._set_generation_progress(GENERATION_PROGRESS.GENERATING)

    def on_post_processing(self) -> GENERATION_PROGRESS:
        """Call when post-processing is about to begin."""
        return self._set_generation_progress(GENERATION_PROGRESS.POST_PROCESSING)

    def on_post_processing_complete(self) -> GENERATION_PROGRESS:
        """Call when post-processing is complete."""
        return self._work_complete()

    def on_pending_safety_check(self) -> GENERATION_PROGRESS:
        """Call when the generation is pending safety check."""
        return self._set_generation_progress(GENERATION_PROGRESS.PENDING_SAFETY_CHECK)

    def set_work_result(self, result: GenerationResultTypeVar | Collection[GenerationResultTypeVar]) -> None:
        """Set the result of the generation work.

        Args:
            result (Any): The result of the generation work.
        """
        self._set_generation_work_result(result)

    def on_complete(self) -> GENERATION_PROGRESS:
        """Call when the generation is complete."""
        return self._set_generation_progress(GENERATION_PROGRESS.COMPLETE)

    _generation_results: OrderedDict[ID_TYPES, GenerationResultTypeVar | None]

    def on_state(
        self,
        state: GENERATION_PROGRESS,
    ) -> GENERATION_PROGRESS:
        """Call when the generation state is updated.

        Args:
            state (GENERATION_PROGRESS): The new state of the generation.
        """
        match state:
            case GENERATION_PROGRESS.PRELOADING:
                return self.on_preloading()
            case GENERATION_PROGRESS.PRELOADING_COMPLETE:
                return self.on_preloading_complete()
            case GENERATION_PROGRESS.GENERATING:
                return self.on_generating()
            case GENERATION_PROGRESS.POST_PROCESSING:
                return self.on_post_processing()
            case GENERATION_PROGRESS.PENDING_POST_PROCESSING:
                return self.on_post_processing_complete()
            case GENERATION_PROGRESS.PENDING_SAFETY_CHECK:
                return self.on_pending_safety_check()
            case GENERATION_PROGRESS.SAFETY_CHECKING:
                return self.on_safety_checking()
            case GENERATION_PROGRESS.PENDING_SUBMIT:
                return self.on_pending_submit()
            case GENERATION_PROGRESS.SUBMITTING:
                return self.on_submitting()
            case GENERATION_PROGRESS.SUBMIT_COMPLETE:
                return self.on_submit_complete()
            case GENERATION_PROGRESS.COMPLETE:
                return self.on_complete()
            case _:
                return self._set_generation_progress(state)

    def step(self, state: GENERATION_PROGRESS) -> GENERATION_PROGRESS:
        """Call when the generation state is updated.

        Args:
            state (GENERATION_PROGRESS): The new state of the generation.
        """
        return self.on_state(state)

    @property
    def generation_results(self) -> OrderedDict[ID_TYPES, GenerationResultTypeVar | None]:
        """Get the result of the generation."""
        with self._lock:
            return self._generation_results.copy()

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
            if len(self._generation_results) >= self.batch_size:
                raise ValueError(
                    f"Generation result list is full ({len(self._generation_results)}), cannot add more results",
                )

            if isinstance(result, self._result_type):
                self._generation_results[self._result_ids[len(self._generation_results)]] = result

            elif isinstance(result, Collection):
                if len(result) + len(self._generation_results) > self.batch_size:
                    raise ValueError(
                        f"Result list is full ({len(self._generation_results)}), cannot add more results",
                    )
                if not all(isinstance(r, self.result_type) for r in result):
                    raise ValueError(
                        f"Result type {type(result)} does not match expected type {self.result_type}",
                    )

                start = len(self._generation_results)
                for index, passed_result in enumerate(result):
                    self._generation_results[self._result_ids[start + index]] = passed_result

    _safety_rules: SafetyRules
    _safety_results: list[SafetyResult | None]

    def _set_safety_check_result(
        self,
        batch_index: int,
        safety_result: SafetyResult,
    ) -> None:
        """Set the result of the safety check.

        Args:
            batch_index (int): The index of the batch to set the safety check result for.
            safety_result (SafetyResult): The result of the safety check.

        Raises:
            ValueError: If is_nsfw or is_csam is not provided or is `None`.
        """
        if len(self._generation_results) == 0 or len(self._generation_results) < batch_index + 1:
            raise ValueError("Generation result must be set before setting safety check result")

        with self._lock:
            if self._safety_results[batch_index] is not None:
                logger.warning(
                    f"Safety check result for batch index {batch_index} has already been set.",
                )

            self._safety_results[batch_index] = safety_result

            if self._safety_rules.should_censor(safety_result):
                logger.trace(
                    f"Safety check result for batch index {batch_index} is unsafe: {safety_result}. "
                    "Censoring result.",
                )

                if self._generation_results[self._result_ids[batch_index]] is None:
                    logger.warning(
                        f"Generation result for batch index {batch_index} is None already",
                    )

                self._generation_results[self._result_ids[batch_index]] = None

    def is_safety_checking_done_on_all_batch(self) -> bool:
        """Check if the safety check is being done on a one-on-all basis.

        Returns:
            bool: True if the safety check is being done on a one-on-all basis, False otherwise.
        """
        all_batch_result_complete = False
        with self._lock:
            if self._safety_results is not None:
                all_batch_result_complete = all(result is not None for result in self._safety_results)

        return all_batch_result_complete

    def get_safety_check_results(self) -> list[SafetyResult | None]:
        """Get the results of the safety checks.

        Returns:
            list[SafetyResult | None]: The results of the safety checks for each batch.
        """
        with self._lock:
            return self._safety_results.copy() if self._safety_results is not None else None

    def on_safety_checking(self) -> GENERATION_PROGRESS:
        """Call when the safety check is about to start."""
        return self._set_generation_progress(GENERATION_PROGRESS.SAFETY_CHECKING)

    def on_safety_check_complete(self, batch_index: int, safety_result: SafetyResult) -> GENERATION_PROGRESS:
        """Call when the safety check is complete.

        Args:
            batch_index (int): The index of the batch to set the safety check result for.
                This is 0-indexed and must match the position of the result_ids provided during initialization.
            safety_result (SafetyResult): The result of the safety check.
        """
        self._set_safety_check_result(
            batch_index=batch_index,
            safety_result=safety_result,
        )

        if not self.is_safety_checking_done_on_all_batch():
            return GENERATION_PROGRESS.SAFETY_CHECKING

        if self._requires_submit:
            return self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)

        return self._set_generation_progress(GENERATION_PROGRESS.COMPLETE)

    def on_pending_submit(self) -> GENERATION_PROGRESS:
        """Call when the generation is pending submission."""
        return self._set_generation_progress(GENERATION_PROGRESS.PENDING_SUBMIT)

    def on_submitting(self) -> GENERATION_PROGRESS:
        """Call when an attempt is going to be made to submit the generation."""
        return self._set_generation_progress(GENERATION_PROGRESS.SUBMITTING)

    def on_submit_complete(self) -> GENERATION_PROGRESS:
        """Call when the generation has been successfully submitted."""
        return self._set_generation_progress(GENERATION_PROGRESS.SUBMIT_COMPLETE)

    def on_user_requested_abort(self) -> GENERATION_PROGRESS:
        """Call when the user requests to abort the generation."""
        return self._set_generation_progress(GENERATION_PROGRESS.USER_REQUESTED_ABORT)

    def on_user_abort_complete(self) -> GENERATION_PROGRESS:
        """Call when the user requested abort is complete."""
        return self._set_generation_progress(GENERATION_PROGRESS.USER_ABORT_COMPLETE)
