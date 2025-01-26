import base64
from collections.abc import Callable, Iterable, Mapping
from io import BytesIO
from typing import Any
from uuid import UUID

import pytest
from loguru import logger
from PIL import Image

from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS
from horde_sdk.ai_horde_worker.generations import (
    AlchemySingleGeneration,
    ImageSingleGeneration,
    TextSingleGeneration,
)
from horde_sdk.ai_horde_worker.generations_base import HordeSingleGeneration


class GenerationPermutation:
    """A permutation of possible generation configurations.

    For example, text generation may not require post-processing or safety checks, while image generation may require
    both. For testing, we can create permutations of these configurations to ensure that the generation process works
    as expected across all possible configurations.

    """

    def __init__(
        self,
        *,
        include_safety_check: bool,
        include_preloading: bool,
        include_post_processing: bool,
    ) -> None:
        """Initialize the permutation.

        Args:
            include_safety_check (bool): Whether to include a safety check in the generation process.
            include_preloading (bool): Whether to include preloading in the generation process.
            include_post_processing (bool): Whether to include post-processing in the generation process.

        """

        self.include_safety_check = include_safety_check
        self.include_preloading = include_preloading
        self.include_post_processing = include_post_processing


@pytest.fixture(scope="session")
def image_permutations() -> list[GenerationPermutation]:
    """Return the supported configurations for a `ImageSingleGeneration` object."""
    return [
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=True,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=True,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=False,
            include_post_processing=True,
        ),
    ]


@pytest.fixture(scope="session")
def alchemy_permutations() -> list[GenerationPermutation]:
    """Return the supported configurations for a `AlchemySingleGeneration` object."""
    return [
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=True,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=True,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=False,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=True,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=False,
            include_post_processing=True,
        ),
    ]


@pytest.fixture(scope="session")
def text_permutations() -> list[GenerationPermutation]:
    """Return the supported configurations for a `TextSingleGeneration` object."""
    return [
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=True,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=False,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=True,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=False,
            include_post_processing=False,
        ),
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=True,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=False,
            include_preloading=False,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=True,
            include_post_processing=True,
        ),
        GenerationPermutation(
            include_safety_check=True,
            include_preloading=False,
            include_post_processing=True,
        ),
    ]


class TestHordeSingleGeneration:
    """Test the `HordeSingleGeneration` class."""

    _shared_image: Image.Image

    @pytest.fixture(autouse=True)
    def setup(self, default_testing_image_base64: str) -> None:
        self._shared_image = Image.open(BytesIO(base64.b64decode(default_testing_image_base64)))

    def test_none_generation_init(
        self,
    ) -> None:
        """Test that an exception is raised when a generation is initialized with a `None` ID."""

        with pytest.raises(TypeError):
            ImageSingleGeneration(generation_id=None)  # type: ignore

    @staticmethod
    def shared_check_generation_init(
        generation: HordeSingleGeneration[Any],
        generation_id: GenerationID,
    ) -> None:
        """Confirm that the `HordeSingleGeneration` was initialized correctly."""
        assert generation.generation_id == generation_id

        first_state, _ = generation._progress_history[0]
        assert first_state == GENERATION_PROGRESS.NOT_STARTED

        assert generation._state_error_limits is not None
        assert len(generation.errored_states) == 0
        assert generation.errored_states is not None
        assert len(generation.errored_states) == 0
        assert generation.generation_metadata is not None
        assert len(generation.errored_states) == 0

        assert generation.is_nsfw is None
        assert generation.is_csam is None

        assert generation.generation_result is None

    def test_alchemy_single_generation_init(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test that an `AlchemySingleGeneration` object can be initialized correctly."""

        from horde_sdk.ai_horde_worker.consts import default_alchemy_generate_progress_transitions

        generation = AlchemySingleGeneration(
            generation_id=single_id,
        )

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=single_id,
        )

        assert generation._generate_progress_transitions == default_alchemy_generate_progress_transitions

    def test_image_single_generation_init(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test that an `ImageSingleGeneration` object can be initialized correctly."""

        from horde_sdk.ai_horde_worker.consts import default_image_generate_progress_transitions

        generation = ImageSingleGeneration(
            generation_id=single_id,
        )

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=single_id,
        )

        assert generation._generate_progress_transitions == default_image_generate_progress_transitions

    def test_text_single_generation_init(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test that a `TextSingleGeneration` object can be initialized correctly."""

        from horde_sdk.ai_horde_worker.consts import default_text_generate_progress_transitions

        generation = TextSingleGeneration(
            generation_id=single_id,
        )

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=single_id,
        )

        assert generation._generate_progress_transitions == default_text_generate_progress_transitions

    def test_invalid_step_raises_error(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test that an exception is raised when an invalid step is passed to the generation."""

        generation = ImageSingleGeneration(generation_id=single_id)

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        with pytest.raises(
            ValueError,
            match=f"Invalid state {GENERATION_PROGRESS.PENDING_SAFETY_CHECK} "
            r"\(current state: "
            f"{GENERATION_PROGRESS.NOT_STARTED}"
            r"\)",
        ):
            generation.step(GENERATION_PROGRESS.PENDING_SAFETY_CHECK)

        generation.step(GENERATION_PROGRESS.PRELOADING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

    def test_wrong_order_of_steps(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test that an exception is raised when the generation steps are called in the wrong order.

        - It should not be possible to transition according to the default transition \
            progressions defined in `horde_sdk/ai_horde_worker/consts.py`.
        - It should not be possible to transition to the same state in which the generation is currently in. \
            This is a safety check to prevent infinite loops or bad implementations.
        """

        generation = ImageSingleGeneration(generation_id=single_id)

        def assert_raises_value_error(func: Callable[..., Any], match: str) -> None:
            with pytest.raises(ValueError, match=match):
                func()

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        assert_raises_value_error(
            generation.on_generation_work_complete,
            f"Invalid transition from {GENERATION_PROGRESS.NOT_STARTED} to {GENERATION_PROGRESS.PENDING_SUBMIT}",
        )

        # Normal progression to preloading
        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        assert_raises_value_error(
            generation.on_preloading,
            f"is already in state {GENERATION_PROGRESS.PRELOADING}",
        )

        assert_raises_value_error(
            generation.on_generation_work_complete,
            f"Invalid transition from {GENERATION_PROGRESS.PRELOADING} to {GENERATION_PROGRESS.PENDING_SUBMIT}",
        )

        # Normal progression to preloading complete
        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        assert_raises_value_error(
            generation.on_preloading_complete,
            f"is already in state {GENERATION_PROGRESS.PRELOADING_COMPLETE}",
        )

        # Normal progression to generating
        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        assert_raises_value_error(
            generation.on_generating,
            f"is already in state {GENERATION_PROGRESS.GENERATING}",
        )

        assert_raises_value_error(
            generation.on_preloading,
            f"Invalid transition from {GENERATION_PROGRESS.GENERATING} to {GENERATION_PROGRESS.PRELOADING}",
        )

        assert_raises_value_error(
            generation.on_preloading_complete,
            f"Invalid transition from {GENERATION_PROGRESS.GENERATING} to {GENERATION_PROGRESS.PRELOADING_COMPLETE}",
        )

    def test_set_safety_check_result_without_generation_result(self, single_id: GenerationID) -> None:
        """Test that an exception is raised when setting a safety check result without setting a generation result."""
        generation = ImageSingleGeneration(generation_id=single_id)

        with pytest.raises(ValueError, match="Generation result must be set before setting safety check result"):
            generation._set_safety_check_result(is_nsfw=True, is_csam=False)

    def test_reference_run_generation_process_image(self) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS
        from horde_sdk.ai_horde_worker.generations import ImageSingleGeneration

        dummy_id = GenerationID(UUID("00000000-0000-0000-0000-000000000000"))
        generation = ImageSingleGeneration(generation_id=dummy_id, requires_post_processing=False)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()

        dummy_image = Image.new("RGB", (100, 100))
        generation.set_work_result(dummy_image)

        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

        generation.on_safety_checking()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(is_csam=False, is_nsfw=False)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_reference_run_generation_process_text(self) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS
        from horde_sdk.ai_horde_worker.generations import TextSingleGeneration

        dummy_id = GenerationID(UUID("00000000-0000-0000-0000-000000000000"))
        generation = TextSingleGeneration(generation_id=dummy_id)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()
        generation.set_work_result("This is a test")
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_reference_run_generation_process_alchemy(self) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS
        from horde_sdk.ai_horde_worker.generations import AlchemySingleGeneration

        dummy_id = GenerationID(UUID("00000000-0000-0000-0000-000000000000"))
        generation = AlchemySingleGeneration(generation_id=dummy_id)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        generation.on_post_processing()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        dummy_image = Image.new("RGB", (100, 100))
        generation.set_work_result(dummy_image)

        generation.on_post_processing_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def run_generation_process(
        self,
        generation: HordeSingleGeneration[Any],
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
    ) -> None:
        """Run a generation process from start to finish.

        This function will run the generation process from start to finish, including preloading, generation,
        post-processing, safety checks, and submission. It will also check that the generation progresses through the
        correct states.

        If a step is not requested, it will be skipped.
        """

        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        if include_preloading:
            assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

            generation.on_preloading()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

            generation.on_preloading_complete()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        if include_generation:
            generation.on_generating()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

            if include_post_processing:
                generation.on_generation_work_complete()
            else:
                generation.on_generation_work_complete()
                generation.set_work_result(self._shared_image)

        if include_post_processing:
            generation.on_post_processing()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

            generation.on_post_processing_complete()
            generation.set_work_result(self._shared_image)

        assert generation.generation_result == self._shared_image

        if include_safety_check:
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

            generation.on_safety_checking()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

            generation.on_safety_check_complete(is_csam=False, is_nsfw=False)
            assert generation.is_csam is False
            assert generation.is_nsfw is False
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_happy_path_image_start_to_finish(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `ImageSingleGeneration` from start to finish."""

        generation = ImageSingleGeneration(generation_id=single_id, requires_post_processing=True)

        self.process_generation(
            generation,
            include_preloading=True,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=True,
        )

        generation_no_post_processing = ImageSingleGeneration(generation_id=single_id, requires_post_processing=False)
        self.process_generation(
            generation_no_post_processing,
            include_preloading=True,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=False,
        )

    def test_happy_path_image_no_preloading(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `ImageSingleGeneration` from start to finish without preloading."""

        generation = ImageSingleGeneration(generation_id=single_id, requires_post_processing=True)

        self.run_generation_process(
            generation,
            include_preloading=False,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=True,
        )

        generation_no_post_processing = ImageSingleGeneration(generation_id=single_id, requires_post_processing=False)
        self.run_generation_process(
            generation_no_post_processing,
            include_preloading=False,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=False,
        )

    def test_happy_path_alchemy_start_to_finish(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `AlchemySingleGeneration` from start to finish."""

        generation = AlchemySingleGeneration(generation_id=single_id)

        self.run_generation_process(
            generation,
            include_preloading=True,
            include_safety_check=False,
            include_generation=False,
            include_post_processing=True,
        )

    def test_happy_path_alchemy_no_preloading(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `AlchemySingleGeneration` from start to finish without preloading."""

        generation = AlchemySingleGeneration(generation_id=single_id, requires_post_processing=True)

        self.run_generation_process(
            generation,
            include_preloading=False,
            include_safety_check=False,
            include_generation=False,
            include_post_processing=True,
        )

    def test_happy_path_text_start_to_finish(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `TextSingleGeneration` from start to finish."""

        generation = TextSingleGeneration(generation_id=single_id)

        self.run_generation_process(
            generation,
            include_preloading=True,
            include_safety_check=False,
            include_generation=True,
            include_post_processing=False,
        )

    def test_happy_path_text_no_preloading(
        self,
        single_id: GenerationID,
    ) -> None:
        """Test the happy path for average `TextSingleGeneration` from start to finish without preloading."""

        generation = TextSingleGeneration(generation_id=single_id)

        self.run_generation_process(
            generation,
            include_preloading=False,
            include_safety_check=False,
            include_generation=True,
            include_post_processing=False,
        )

    @staticmethod
    def handle_error(
        generation: HordeSingleGeneration[Any],
        error_message: str,
        error_exception: Exception,
        errors_count: int,
    ) -> None:
        generation.on_error(
            failed_message=error_message,
            failure_exception=error_exception,
        )
        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

    def process_generation(
        self,
        generation: HordeSingleGeneration[Any],
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        error_on_preloading: bool = False,
        error_on_generation: bool = False,
        error_on_post_processing: bool = False,
        error_on_safety_check: bool = False,
        error_on_submit: bool = False,
    ) -> None:
        """Process a generation with the given configurations.

        This will step the `HordeSingleGeneration` through the entire generation process, as requested by the
        arguments. If an error is requested, the generation will be marked as errored and the error count will be
        incremented.

        """

        error_flags = {
            "preloading": error_on_preloading and include_preloading,
            "generation": error_on_generation and include_generation,
            "post_processing": error_on_post_processing and include_post_processing,
            "safety_check": error_on_safety_check and include_safety_check,
            "submit": error_on_submit,
        }

        if not generation.does_class_requires_generation() and not include_generation and not include_post_processing:
            logger.trace(
                f"Skipping generation for {generation.__class__.__name__} as it does not require generation "
                "and generation and post-processing are not included",
            )
            return

        target_errors_count = sum(error_flags.values())
        errors_count = 0

        if include_preloading:
            errors_count = self._simulate_preloading(generation, error_on_preloading, errors_count)

        if include_generation:
            errors_count = self._simulate_generation(
                generation,
                error_on_generation=error_on_generation,
                include_post_processing=include_post_processing,
                errors_count=errors_count,
            )

        if include_post_processing:
            errors_count = self._simulate_post_processing(
                generation,
                error_on_post_processing=error_on_post_processing,
                errors_count=errors_count,
            )

        if include_safety_check:
            errors_count = self._simulate_safety_check(
                generation,
                error_on_safety_check=error_on_safety_check,
                errors_count=errors_count,
            )

        errors_count = self._simulate_submission(
            generation,
            error_on_submit=error_on_submit,
            errors_count=errors_count,
        )

        assert generation.generation_failure_count == target_errors_count

    def _simulate_preloading(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_preloading: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the preloading step for a `HordeSingleGeneration`."""

        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.step(GENERATION_PROGRESS.PRELOADING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        if error_on_preloading:
            errors_count += 1
            generation.on_error(
                failed_message="Failed to preload",
                failure_exception=Exception("Failed to preload exception"),
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.PRELOADING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

            assert generation.generation_failure_count == errors_count
            assert generation.errored_states is not None
            error_state, error_time = generation.errored_states[-1]
            assert error_state == GENERATION_PROGRESS.PRELOADING
            assert error_time != 0

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        return errors_count

    def _simulate_generation(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_generation: bool,
        include_post_processing: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the generation step for a `HordeSingleGeneration`."""

        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        generation.step(GENERATION_PROGRESS.GENERATING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        if error_on_generation:
            errors_count += 1
            generation.on_error(
                failed_message="Failed to generate",
                failure_exception=Exception("Failed to generate exception"),
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.GENERATING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

            assert generation.generation_failure_count == errors_count
            assert generation.errored_states is not None
            error_state, error_time = generation.errored_states[-1]
            assert error_state == GENERATION_PROGRESS.GENERATING
            assert error_time != 0

        if include_post_processing:
            generation.on_generation_work_complete()
        else:
            generation.on_generation_work_complete()
            generation.set_work_result(self._shared_image)

        return errors_count

    def _simulate_post_processing(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_post_processing: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the post-processing step for a `HordeSingleGeneration`."""

        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        generation.step(GENERATION_PROGRESS.POST_PROCESSING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        if error_on_post_processing:
            errors_count += 1
            generation.on_error(
                failed_message="Failed during post-processing",
                failure_exception=Exception("Failed during post-processing exception"),
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.POST_PROCESSING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        generation.on_post_processing_complete()
        generation.set_work_result(self._shared_image)

        assert generation.generation_result == self._shared_image

        return errors_count

    def _simulate_safety_check(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_safety_check: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the safety check step for a `HordeSingleGeneration`."""
        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

        generation.step(GENERATION_PROGRESS.SAFETY_CHECKING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        if error_on_safety_check:
            errors_count += 1
            generation.on_error(
                failed_message="Failed during safety check",
                failure_exception=Exception("Failed during safety check exception"),
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.SAFETY_CHECKING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(is_csam=False, is_nsfw=False)
        assert generation.is_csam is False
        assert generation.is_nsfw is False

        return errors_count

    def _simulate_submission(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_submit: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the submission step for a `HordeSingleGeneration`."""
        from horde_sdk.ai_horde_worker.consts import GENERATION_PROGRESS

        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.step(GENERATION_PROGRESS.SUBMITTING)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        if error_on_submit:
            errors_count += 1
            generation.on_error(
                failed_message="Failed during submission",
                failure_exception=Exception("Failed during submission exception"),
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.SUBMITTING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

        return errors_count

    def run_generation_test_permutations(
        self,
        generation_class: type[HordeSingleGeneration[Any]],
        generation_id: GenerationID | Callable[[], GenerationID],
        permutations: list[GenerationPermutation],
        process_function: Callable[..., None],
        include_generation: bool,
        requires_generation: bool | None = None,
        **kwargs: Any,  # noqa
    ) -> None:
        """Run permutations of generation configurations.

        See the docstring for `GenerationPermutation` for more information on the possible configurations.

        Args:
            generation_class (type[HordeSingleGeneration[Any]]): The generation class to test.
            generation_id (GenerationID | Callable[[], GenerationID]): The generation ID or generation ID factory to\
                use for the test.
            permutations (list[GenerationPermutation]): The permutations to test.
            process_function (Callable[..., None]): The function to process the generation.
            include_generation (bool): Whether to include generation in the process.
            requires_generation (bool | None): Whether the generation requires generation.
            **kwargs (Any): Additional keyword arguments to pass to the process function.

        """
        for permutation in permutations:
            from horde_sdk.ai_horde_worker.consts import base_generate_progress_transitions

            transition_override: Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]] = (
                generation_class.default_generate_progress_transitions()
            )
            if permutation.include_safety_check:
                transition_override = base_generate_progress_transitions
                logger.trace(f"Using safety check transitions for {generation_class.__name__}")
            else:
                logger.trace(
                    f"Using default transitions for {generation_class.__name__} as defined by the class"
                    "function `default_generate_progress_transitions(...)`",
                )

            if requires_generation and not generation_class.does_class_requires_generation():
                generation = generation_class(
                    generation_id=generation_id() if callable(generation_id) else generation_id,
                    requires_post_processing=permutation.include_post_processing,
                    requires_generation=requires_generation,
                    generate_progress_transitions=transition_override,
                    extra_logging=False,
                )
            else:
                generation = generation_class(
                    generation_id=generation_id() if callable(generation_id) else generation_id,
                    requires_post_processing=permutation.include_post_processing,
                    generate_progress_transitions=transition_override,
                    extra_logging=False,
                )

            if generation_class.does_class_requires_generation():
                logger.trace(
                    f"Overriding requires_generation to {requires_generation} for {generation_class.__name__}",
                )
                include_generation = True

            process_function(
                self,
                generation,
                include_generation=include_generation,
                include_safety_check=permutation.include_safety_check,
                include_preloading=permutation.include_preloading,
                include_post_processing=permutation.include_post_processing,
                **kwargs,
            )

    @pytest.mark.parametrize(
        "generation_class,process_function,include_generation,requires_generation",
        [
            (ImageSingleGeneration, process_generation, True, True),
            (ImageSingleGeneration, process_generation, True, False),
            (ImageSingleGeneration, process_generation, False, True),
            (ImageSingleGeneration, process_generation, False, False),
            (AlchemySingleGeneration, process_generation, True, True),
            (AlchemySingleGeneration, process_generation, True, False),
            (AlchemySingleGeneration, process_generation, False, True),
            (AlchemySingleGeneration, process_generation, False, False),
            (TextSingleGeneration, process_generation, True, True),
            (TextSingleGeneration, process_generation, True, False),
            (TextSingleGeneration, process_generation, False, True),
            (TextSingleGeneration, process_generation, False, False),
        ],
    )
    def test_error_handling(
        self,
        generation_class: type[HordeSingleGeneration[Any]],
        process_function: Callable[..., None],
        include_generation: bool,
        requires_generation: bool,
        id_factory: Callable[[], GenerationID],
        image_permutations: list[GenerationPermutation],
        alchemy_permutations: list[GenerationPermutation],
        text_permutations: list[GenerationPermutation],
    ) -> None:
        """Test error handling for all permutations of generation configurations."""
        error_permutations = [
            (a, b, c, d, e)
            for a in [True, False]
            for b in [True, False]
            for c in [True, False]
            for d in [True, False]
            for e in [True, False]
        ]

        permutations_map = {
            ImageSingleGeneration: image_permutations,
            AlchemySingleGeneration: alchemy_permutations,
            TextSingleGeneration: text_permutations,
        }

        for error_permutation in error_permutations:
            permutations = permutations_map.get(generation_class)
            if permutations is None:
                raise ValueError(f"Permutations not found for {generation_class.__name__}")

            try:
                self.run_generation_test_permutations(
                    generation_class,
                    id_factory,
                    permutations,
                    process_function,
                    include_generation=include_generation,
                    requires_generation=requires_generation,
                    error_on_preloading=error_permutation[0],
                    error_on_generation=error_permutation[1],
                    error_on_post_processing=error_permutation[2],
                    error_on_safety_check=error_permutation[3],
                    error_on_submit=error_permutation[4],
                )
            except Exception as e:
                logger.exception(f"Error running permutations for {generation_class.__name__}")
                logger.exception(f"Error permutation: {error_permutation}")
                logger.exception(f"Generation permutations: {permutations}")
                logger.exception(f"included generation: {include_generation}")
                logger.exception(f"requires generation: {requires_generation}")

                raise e
