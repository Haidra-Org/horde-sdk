from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    initial_generation_state,
)


def test_initial_generation_state() -> None:
    assert initial_generation_state == GENERATION_PROGRESS.NOT_STARTED, "Initial state should be NOT_STARTED"
