from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    default_image_generate_progress_transitions,
    initial_generation_state,
)


def test_base_generate_progress_transitions() -> None:
    transitions = default_image_generate_progress_transitions

    assert (
        GENERATION_PROGRESS.ERROR not in transitions[GENERATION_PROGRESS.NOT_STARTED]
    ), "ERROR should not be a valid next state from NOT_STARTED"


def test_initial_generation_state() -> None:
    assert initial_generation_state == GENERATION_PROGRESS.NOT_STARTED, "Initial state should be NOT_STARTED"
