"""Tests for the generation progress transition tables and the milestone/retry semantics built on them."""

import pytest

from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.safety import ImageSafetyResult
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    GENERATION_RETRY_KIND,
    base_generate_progress_no_submit_transitions,
    base_generate_progress_transitions,
    black_box_generate_progress_transitions,
    default_alchemy_generate_progress_no_submit_transitions,
    default_alchemy_generate_progress_transitions,
    default_image_generate_progress_no_submit_transitions,
    default_image_generate_progress_transitions,
    default_text_generate_progress_no_submit_transitions,
    default_text_generate_progress_transitions,
    validate_generation_progress_transitions,
)
from horde_sdk.worker.generations import ImageSingleGeneration

_ALL_TRANSITION_TABLES = {
    "base": base_generate_progress_transitions,
    "base_no_submit": base_generate_progress_no_submit_transitions,
    "black_box": black_box_generate_progress_transitions,
    "image": default_image_generate_progress_transitions,
    "image_no_submit": default_image_generate_progress_no_submit_transitions,
    "alchemy": default_alchemy_generate_progress_transitions,
    "alchemy_no_submit": default_alchemy_generate_progress_no_submit_transitions,
    "text": default_text_generate_progress_transitions,
    "text_no_submit": default_text_generate_progress_no_submit_transitions,
}


@pytest.mark.parametrize("table_name", _ALL_TRANSITION_TABLES)
def test_transition_tables_are_valid(table_name: str) -> None:
    """Every published transition table is internally consistent."""
    assert validate_generation_progress_transitions(_ALL_TRANSITION_TABLES[table_name])


def test_milestones_are_mandatory_in_base_table() -> None:
    """Each work stage exits only through its completion milestone; no stage skips ahead directly."""
    table = base_generate_progress_transitions

    assert table[GENERATION_PROGRESS.GENERATING] == [
        GENERATION_PROGRESS.GENERATION_COMPLETE,
        GENERATION_PROGRESS.ERROR,
    ]
    assert table[GENERATION_PROGRESS.POST_PROCESSING] == [
        GENERATION_PROGRESS.POST_PROCESSING_COMPLETE,
        GENERATION_PROGRESS.ERROR,
    ]
    assert table[GENERATION_PROGRESS.SAFETY_CHECKING] == [
        GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE,
        GENERATION_PROGRESS.ERROR,
    ]

    assert GENERATION_PROGRESS.PENDING_POST_PROCESSING in table[GENERATION_PROGRESS.GENERATION_COMPLETE]
    assert GENERATION_PROGRESS.PENDING_SAFETY_CHECK in table[GENERATION_PROGRESS.GENERATION_COMPLETE]
    assert GENERATION_PROGRESS.PENDING_SAFETY_CHECK in table[GENERATION_PROGRESS.POST_PROCESSING_COMPLETE]
    assert GENERATION_PROGRESS.PENDING_SUBMIT in table[GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE]


def test_error_fanout_expresses_retries() -> None:
    """The ERROR state can return to any retryable stage or to a fresh dispatch."""
    error_targets = set(base_generate_progress_transitions[GENERATION_PROGRESS.ERROR])

    assert {
        GENERATION_PROGRESS.ABORTED,
        GENERATION_PROGRESS.NOT_STARTED,
        GENERATION_PROGRESS.PRELOADING,
        GENERATION_PROGRESS.GENERATING,
        GENERATION_PROGRESS.POST_PROCESSING,
        GENERATION_PROGRESS.SAFETY_CHECKING,
        GENERATION_PROGRESS.SUBMITTING,
    } == error_targets


def test_skip_submit_does_not_route_error_to_complete() -> None:
    """Removing the submit stages must not create an ERROR -> COMPLETE edge."""
    for table in (base_generate_progress_no_submit_transitions, default_image_generate_progress_no_submit_transitions):
        assert GENERATION_PROGRESS.COMPLETE not in table[GENERATION_PROGRESS.ERROR]
        assert GENERATION_PROGRESS.SUBMITTING not in table[GENERATION_PROGRESS.ERROR]


def test_milestone_classifier() -> None:
    """is_state_milestone identifies exactly the stage-completion states."""
    milestones = {state for state in GENERATION_PROGRESS if GENERATION_PROGRESS.is_state_milestone(state)}
    assert milestones == {
        GENERATION_PROGRESS.GENERATION_COMPLETE,
        GENERATION_PROGRESS.POST_PROCESSING_COMPLETE,
        GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE,
    }


class TestMilestoneWalks:
    """Full walks through the reshaped state machine using the generation hook API."""

    def test_generation_with_post_processing_walk(
        self,
        simple_image_generation_parameters_post_processing: ImageGenerationParameters,
        default_testing_image_bytes: bytes,
    ) -> None:
        """A generation with embedded post-processing passes through every milestone in order."""
        generation = ImageSingleGeneration(
            generation_parameters=simple_image_generation_parameters_post_processing,
        )

        assert generation.requires_post_processing
        assert generation.post_processing_operations == ("RealESRGAN_x2plus",)

        generation.on_preloading()
        generation.on_preloading_complete()
        generation.on_generating()

        raw_image = default_testing_image_bytes
        progress = generation.on_generation_work_complete(raw_image)
        assert progress == GENERATION_PROGRESS.PENDING_POST_PROCESSING

        intermediate_results = generation.intermediate_results
        assert list(intermediate_results.values()) == [raw_image]
        assert not any(generation.generation_results.values())

        generation.on_post_processing()
        post_processed_image = raw_image + b"-post-processed"
        progress = generation.on_post_processing_complete(post_processed_image)
        assert progress == GENERATION_PROGRESS.PENDING_SAFETY_CHECK
        assert list(generation.generation_results.values()) == [post_processed_image]

        generation.on_safety_checking()
        progress = generation.on_safety_check_complete(
            batch_index=0,
            safety_result=ImageSafetyResult(is_nsfw=False, is_csam=False),
        )
        assert progress == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        generation.on_submit_complete()
        assert generation.on_complete() == GENERATION_PROGRESS.COMPLETE

        walked_states = [state for state, _ in generation.get_progress_history()]
        assert walked_states == [
            GENERATION_PROGRESS.NOT_STARTED,
            GENERATION_PROGRESS.PRELOADING,
            GENERATION_PROGRESS.PRELOADING_COMPLETE,
            GENERATION_PROGRESS.GENERATING,
            GENERATION_PROGRESS.GENERATION_COMPLETE,
            GENERATION_PROGRESS.PENDING_POST_PROCESSING,
            GENERATION_PROGRESS.POST_PROCESSING,
            GENERATION_PROGRESS.POST_PROCESSING_COMPLETE,
            GENERATION_PROGRESS.PENDING_SAFETY_CHECK,
            GENERATION_PROGRESS.SAFETY_CHECKING,
            GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE,
            GENERATION_PROGRESS.PENDING_SUBMIT,
            GENERATION_PROGRESS.SUBMITTING,
            GENERATION_PROGRESS.SUBMIT_COMPLETE,
            GENERATION_PROGRESS.COMPLETE,
        ]

    def test_generation_without_post_processing_walk(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        default_testing_image_bytes: bytes,
    ) -> None:
        """A generation without post-processing routes GENERATION_COMPLETE straight to the safety queue."""
        generation = ImageSingleGeneration(generation_parameters=simple_image_generation_parameters)

        assert not generation.requires_post_processing
        assert generation.post_processing_operations == ()

        generation.on_generating()
        progress = generation.on_generation_work_complete(default_testing_image_bytes)
        assert progress == GENERATION_PROGRESS.PENDING_SAFETY_CHECK
        assert list(generation.generation_results.values()) == [default_testing_image_bytes]
        assert generation.intermediate_results == {}

        walked_states = [state for state, _ in generation.get_progress_history()]
        assert GENERATION_PROGRESS.GENERATION_COMPLETE in walked_states

    def test_retry_returns_to_failed_stage(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        """After an error, the generation can retry the failed stage and record the retry."""
        generation = ImageSingleGeneration(generation_parameters=simple_image_generation_parameters)

        generation.on_generating()
        generation.on_error(failed_message="backend fell over")
        generation.record_retry(GENERATION_RETRY_KIND.NORMAL)
        assert generation.on_generating() == GENERATION_PROGRESS.GENERATING

        generation.on_error(failed_message="backend fell over again")
        generation.record_retry(GENERATION_RETRY_KIND.DEGRADED, error=RuntimeError("OOM"))
        assert generation.on_generating() == GENERATION_PROGRESS.GENERATING

        assert generation.retry_counts == {
            GENERATION_RETRY_KIND.NORMAL: 1,
            GENERATION_RETRY_KIND.DEGRADED: 1,
        }
        retried_states = [state for _, state, _ in generation.retry_events]
        assert retried_states == [GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATING]
        assert generation.generation_failure_count == 2

    def test_retry_limit_still_enforced(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        """Per-state error limits bound the retry loop regardless of the wider ERROR fan-out."""
        generation = ImageSingleGeneration(generation_parameters=simple_image_generation_parameters)

        generation.on_generating()
        # The default limit for GENERATING is 3 errors; the transition engine refuses further re-entry.
        generation.on_error(failed_message="fail 1")
        generation.on_generating()
        generation.on_error(failed_message="fail 2")
        generation.on_generating()
        generation.on_error(failed_message="fail 3")

        with pytest.raises(RuntimeError, match="exceeded the maximum number of errors"):
            generation.on_generating()

    def test_stage_durations_accumulate(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        default_testing_image_bytes: bytes,
    ) -> None:
        """Stage durations are derived from the progress history and cover every visited state."""
        generation = ImageSingleGeneration(generation_parameters=simple_image_generation_parameters)

        generation.on_generating()
        generation.on_generation_work_complete(default_testing_image_bytes)

        durations = generation.get_stage_durations()
        visited_states = {state for state, _ in generation.get_progress_history()}
        assert set(durations) == visited_states
        assert all(duration >= 0.0 for duration in durations.values())
