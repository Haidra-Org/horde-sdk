from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from loguru import logger

from horde_sdk.generation_parameters.alchemy import (
    AlchemyParameters,
    SingleAlchemyParameters,
)
from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.generation_parameters.text import TextGenerationParameters
from horde_sdk.worker.consts import GENERATION_PROGRESS
from horde_sdk.worker.generations import (
    AlchemySingleGeneration,
    ImageSingleGeneration,
    TextSingleGeneration,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration


class GenerationPermutation:
    """A permutation of possible generation configurations.

    For example, text generation may not require post-processing or safety checks, while image generation may require
    both. For testing, we can create permutations of these configurations to ensure that the generation process works
    as expected across all possible configurations.

    """

    def __init__(
        self,
        *,
        include_generation: bool,
        include_safety_check: bool,
        include_preloading: bool,
        include_post_processing: bool,
        underlying_payload: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
    ) -> None:
        """Initialize the permutation.

        Args:
            include_safety_check (bool): Whether to include a safety check in the generation process.
            include_preloading (bool): Whether to include preloading in the generation process.
            include_post_processing (bool): Whether to include post-processing in the generation process.

        """
        self.include_generation = include_generation
        self.include_safety_check = include_safety_check
        self.include_preloading = include_preloading
        self.include_post_processing = include_post_processing
        self.underlying_payload = underlying_payload


def create_permutations(
    payload: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
    required_safety_check: bool = False,
    required_preloading: bool = False,
    required_post_processing: bool = False,
    required_generation: bool = False,
) -> list[GenerationPermutation]:
    permutations = []
    for include_safety_check in [True] if required_safety_check else [False, True]:
        for include_preloading in [True] if required_preloading else [False, True]:
            for include_post_processing in [True] if required_post_processing else [False, True]:
                for include_generation in [True] if required_generation else [False, True]:
                    permutations.append(
                        GenerationPermutation(
                            include_generation=include_generation,
                            include_safety_check=include_safety_check,
                            include_preloading=include_preloading,
                            include_post_processing=include_post_processing,
                            underlying_payload=payload,
                        ),
                    )
    return permutations


@pytest.fixture(scope="function")
def text_permutations(
    simple_text_generation_parameters: TextGenerationParameters,
) -> list[GenerationPermutation]:
    """Return the supported configurations for a `TextSingleGeneration` object."""
    return create_permutations(
        simple_text_generation_parameters,
        required_generation=True,
    )


@pytest.fixture(scope="function")
def image_permutations(
    simple_image_generation_parameters: ImageGenerationParameters,
    simple_image_generation_parameters_post_processing: ImageGenerationParameters,
) -> list[GenerationPermutation]:
    """Return the supported configurations for a `ImageSingleGeneration` object."""
    return create_permutations(
        simple_image_generation_parameters,
        required_generation=True,
        required_safety_check=True,
    ) + create_permutations(
        simple_image_generation_parameters_post_processing,
        required_generation=True,
        required_safety_check=True,
    )


@pytest.fixture(scope="function")
def alchemy_permutations(
    simple_alchemy_generation_parameters: AlchemyParameters,
    simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
) -> list[GenerationPermutation]:
    """Return the supported configurations for a `AlchemySingleGeneration` object."""
    assert len(simple_alchemy_generation_parameters.all_alchemy_operations) == 1
    assert len(simple_alchemy_generation_parameters_nsfw_detect.all_alchemy_operations) == 1
    return create_permutations(
        simple_alchemy_generation_parameters.all_alchemy_operations[0],
    ) + create_permutations(
        simple_alchemy_generation_parameters_nsfw_detect.all_alchemy_operations[0],
    )


class TestHordeSingleGeneration:
    """Test the `HordeSingleGeneration` class."""

    _shared_image: bytes

    @pytest.fixture(autouse=True)
    def setup(self, default_testing_image_bytes: bytes) -> None:
        self._shared_image = default_testing_image_bytes

    @pytest.fixture(scope="function")
    def id_and_image_generation(
        self,
        single_id_str: str,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> tuple[str, ImageSingleGeneration]:
        generation = ImageSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_image_generation_parameters,
        )
        return single_id_str, generation

    @pytest.fixture(scope="function")
    def id_and_text_generation(
        self,
        single_id_str: str,
        simple_text_generation_parameters: TextGenerationParameters,
    ) -> tuple[str, TextSingleGeneration]:
        generation = TextSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_text_generation_parameters,
        )
        return single_id_str, generation

    @pytest.fixture(scope="function")
    def id_and_alchemy_generation(
        self,
        single_id_str: str,
        simple_alchemy_generation_parameters: AlchemyParameters,
    ) -> tuple[str, AlchemySingleGeneration]:
        assert len(simple_alchemy_generation_parameters.all_alchemy_operations) == 1
        generation = AlchemySingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_alchemy_generation_parameters.all_alchemy_operations[0],
        )
        return single_id_str, generation

    def test_none_generation_init(
        self,
    ) -> None:
        """Test that an exception is raised when a generation is initialized with a `None` ID."""

        with pytest.raises(TypeError):
            ImageSingleGeneration(generation_id=None)  # type: ignore

    @staticmethod
    def shared_check_generation_init(
        generation: HordeSingleGeneration[Any],
        generation_id: str,
    ) -> None:
        """Confirm that the `HordeSingleGeneration` was initialized correctly."""
        assert generation.generation_id == generation_id

        first_state, _ = generation._progress_history[0]
        assert first_state == GENERATION_PROGRESS.NOT_STARTED

        assert generation._state_error_limits is not None
        # assert len(generation._state_error_limits) == 0 # FIXME
        assert generation.errored_states is not None
        assert len(generation.errored_states) == 0

        assert generation.is_nsfw is None
        assert generation.is_csam is None

        assert generation.generation_results is None

    def test_alchemy_single_generation_init(
        self,
        id_and_alchemy_generation: tuple[str, AlchemySingleGeneration],
    ) -> None:
        """Test that an `AlchemySingleGeneration` object can be initialized correctly."""

        from horde_sdk.worker.consts import default_alchemy_generate_progress_transitions

        generation_id, generation = id_and_alchemy_generation

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=generation_id,
        )

        assert generation._generate_progress_transitions == default_alchemy_generate_progress_transitions

    def test_image_single_generation_init(
        self,
        id_and_image_generation: tuple[str, ImageSingleGeneration],
    ) -> None:
        """Test that an `ImageSingleGeneration` object can be initialized correctly."""

        from horde_sdk.worker.consts import default_image_generate_progress_transitions

        generation_id, generation = id_and_image_generation

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=generation_id,
        )

        assert generation._generate_progress_transitions == default_image_generate_progress_transitions

    def test_text_single_generation_init(
        self,
        id_and_text_generation: tuple[str, TextSingleGeneration],
    ) -> None:
        """Test that a `TextSingleGeneration` object can be initialized correctly."""

        from horde_sdk.worker.consts import default_text_generate_progress_transitions

        generation_id, generation = id_and_text_generation

        TestHordeSingleGeneration.shared_check_generation_init(
            generation=generation,
            generation_id=generation_id,
        )

        assert generation._generate_progress_transitions == default_text_generate_progress_transitions

    def test_invalid_step_raises_error(
        self,
        id_and_image_generation: tuple[str, ImageSingleGeneration],
    ) -> None:
        """Test that an exception is raised when an invalid step is passed to the generation."""

        _, generation = id_and_image_generation

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
        id_and_image_generation: tuple[str, ImageSingleGeneration],
    ) -> None:
        """Test that an exception is raised when the generation steps are called in the wrong order.

        - It should not be possible to transition according to the default transition \
            progressions defined in `horde_sdk/ai_horde_worker/consts.py`.
        - It should not be possible to transition to the same state in which the generation is currently in. \
            This is a safety check to prevent infinite loops or bad implementations.
        """

        _, generation = id_and_image_generation

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

    def test_set_safety_check_result_without_generation_result(
        self,
        id_and_image_generation: tuple[str, ImageSingleGeneration],
    ) -> None:
        """Test that an exception is raised when setting a safety check result without setting a generation result."""
        _, generation = id_and_image_generation

        with pytest.raises(ValueError, match="Generation result must be set before setting safety check result"):
            generation._set_safety_check_result(is_nsfw=True, is_csam=False)

    def test_reference_run_generation_process_image(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        default_testing_image_bytes: bytes,
    ) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.worker.consts import GENERATION_PROGRESS
        from horde_sdk.worker.generations import ImageSingleGeneration

        dummy_id = str(UUID("00000000-0000-0000-0000-000000000000"))
        generation = ImageSingleGeneration(
            generation_id=dummy_id,
            generation_parameters=simple_image_generation_parameters,
        )
        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()

        generation.set_work_result(default_testing_image_bytes)

        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

        generation.on_safety_checking()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(is_csam=False, is_nsfw=False)
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_reference_run_generation_process_text(
        self,
        simple_text_generation_parameters: TextGenerationParameters,
    ) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.worker.consts import GENERATION_PROGRESS
        from horde_sdk.worker.generations import TextSingleGeneration

        dummy_id = str(UUID("00000000-0000-0000-0000-000000000000"))
        generation = TextSingleGeneration(
            generation_id=dummy_id,
            generation_parameters=simple_text_generation_parameters,
        )
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

    def test_reference_run_generation_process_alchemy(
        self,
        id_and_alchemy_generation: tuple[str, AlchemySingleGeneration],
        default_testing_image_bytes: bytes,
    ) -> None:
        """Run a reference generation process from start to finish, without testing-specific magic or helpers.

        The purpose of this test is to have a the bare-minimum usage of the `HordeSingleGeneration` class to ensure
        that the most straight forward use-case works as expected and isn't lost in the complexity of the test suite.
        """
        from horde_sdk.worker.consts import GENERATION_PROGRESS

        _, generation = id_and_alchemy_generation

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED

        generation.on_preloading()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        generation.on_preloading_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        generation.on_post_processing()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        generation.set_work_result(default_testing_image_bytes)

        generation.on_post_processing_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    @staticmethod
    def run_generation_process(
        generation: HordeSingleGeneration[Any],
        result: bytes | str,
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

        from horde_sdk.worker.consts import GENERATION_PROGRESS

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
                generation.set_work_result(result)

        if include_post_processing:
            generation.on_post_processing()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

            generation.on_post_processing_complete()
            generation.set_work_result(result)

        assert generation.generation_results is not None
        assert len(generation.generation_results) == 1

        generation_result_id, generation_result = generation.generation_results.popitem()
        assert isinstance(generation_result_id, UUID)
        assert generation_result is not None

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
        single_id_str: str,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_image_generation_parameters_post_processing: ImageGenerationParameters,
    ) -> None:
        """Test the happy path for average `ImageSingleGeneration` from start to finish."""

        generation_no_post_processing = ImageSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_image_generation_parameters,
        )
        self.process_generation(
            generation_no_post_processing,
            include_preloading=True,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=False,
        )

        generation_with_post_processing = ImageSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_image_generation_parameters_post_processing,
        )
        self.process_generation(
            generation_with_post_processing,
            include_preloading=True,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=True,
        )

    def test_happy_path_image_no_preloading(
        self,
        single_id_str: str,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_image_generation_parameters_post_processing: ImageGenerationParameters,
    ) -> None:
        """Test the happy path for average `ImageSingleGeneration` from start to finish without preloading."""

        generation_no_post_processing = ImageSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_image_generation_parameters,
        )
        self.run_generation_process(
            generation_no_post_processing,
            result=self._shared_image,
            include_preloading=False,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=False,
        )

        generation_with_post_processing = ImageSingleGeneration(
            generation_id=single_id_str,
            generation_parameters=simple_image_generation_parameters_post_processing,
        )
        self.run_generation_process(
            generation_with_post_processing,
            result=self._shared_image,
            include_preloading=False,
            include_safety_check=True,
            include_generation=True,
            include_post_processing=True,
        )

    def test_happy_path_alchemy_start_to_finish(
        self,
        id_and_alchemy_generation: tuple[str, AlchemySingleGeneration],
    ) -> None:
        """Test the happy path for average `AlchemySingleGeneration` from start to finish."""

        _, generation = id_and_alchemy_generation

        self.run_generation_process(
            generation,
            result=self._shared_image,
            include_preloading=True,
            include_safety_check=False,
            include_generation=False,
            include_post_processing=True,
        )

    def test_happy_path_alchemy_no_preloading(
        self,
        id_and_alchemy_generation: tuple[str, AlchemySingleGeneration],
    ) -> None:
        """Test the happy path for average `AlchemySingleGeneration` from start to finish without preloading."""

        _, generation = id_and_alchemy_generation

        self.run_generation_process(
            generation,
            result=self._shared_image,
            include_preloading=False,
            include_safety_check=False,
            include_generation=False,
            include_post_processing=True,
        )

    def test_happy_path_text_start_to_finish(
        self,
        id_and_text_generation: tuple[str, TextSingleGeneration],
    ) -> None:
        """Test the happy path for average `TextSingleGeneration` from start to finish."""

        _, generation = id_and_text_generation

        self.run_generation_process(
            generation,
            result="Fake Text Generation Result",
            include_preloading=True,
            include_safety_check=False,
            include_generation=True,
            include_post_processing=False,
        )

    def test_happy_path_text_no_preloading(
        self,
        id_and_text_generation: tuple[str, TextSingleGeneration],
    ) -> None:
        """Test the happy path for average `TextSingleGeneration` from start to finish without preloading."""

        _, generation = id_and_text_generation

        self.run_generation_process(
            generation,
            result="Fake Text Generation Result",
            include_preloading=False,
            include_safety_check=False,
            include_generation=True,
            include_post_processing=False,
        )

    def simulate_hitting_error_limit(
        self,
        generation: HordeSingleGeneration[Any],
        state_to_error_out_on: GENERATION_PROGRESS,
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        include_submit: bool,
    ) -> None:
        from horde_sdk.worker.consts import GENERATION_PROGRESS

        if state_to_error_out_on == GENERATION_PROGRESS.PRELOADING and not include_preloading:
            return
        if state_to_error_out_on == GENERATION_PROGRESS.GENERATING and not include_generation:
            return
        if state_to_error_out_on == GENERATION_PROGRESS.POST_PROCESSING and not include_post_processing:
            return
        if state_to_error_out_on == GENERATION_PROGRESS.SAFETY_CHECKING and not include_safety_check:
            return
        if state_to_error_out_on == GENERATION_PROGRESS.SUBMITTING and not include_submit:
            return
        if state_to_error_out_on == GENERATION_PROGRESS.PENDING_SUBMIT:
            return

        if not (include_preloading or include_generation or include_post_processing or include_safety_check):
            return

        if include_submit and not generation.requires_submit:
            return

        if include_preloading:
            generation.on_preloading()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING
            if state_to_error_out_on == GENERATION_PROGRESS.PRELOADING:
                assert generation._state_error_limits is not None
                with pytest.raises(RuntimeError, match="has exceeded the maximum number of errors for state"):
                    for _ in range(generation._state_error_limits[GENERATION_PROGRESS.PRELOADING]):
                        generation.on_error(
                            failed_message="Failed to preload",
                            failure_exception=Exception("Failed to preload exception"),
                        )
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR
                        generation.step(GENERATION_PROGRESS.PRELOADING)
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING
            else:
                generation.on_preloading_complete()
                assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        if include_generation:
            generation.on_generating()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

            if state_to_error_out_on == GENERATION_PROGRESS.GENERATING:
                with pytest.raises(RuntimeError, match="has exceeded the maximum number of errors for state"):
                    assert generation._state_error_limits is not None
                    for _ in range(generation._state_error_limits[GENERATION_PROGRESS.GENERATING]):
                        generation.on_error(
                            failed_message="Failed to generate",
                            failure_exception=Exception("Failed to generate exception"),
                        )
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR
                        generation.step(GENERATION_PROGRESS.GENERATING)
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

                return

            generation.on_generation_work_complete()

        if include_post_processing:
            generation.on_post_processing()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

            if state_to_error_out_on == GENERATION_PROGRESS.POST_PROCESSING:
                with pytest.raises(RuntimeError, match="has exceeded the maximum number of errors for state"):
                    assert generation._state_error_limits is not None
                    for _ in range(generation._state_error_limits[GENERATION_PROGRESS.POST_PROCESSING]):
                        generation.on_error(
                            failed_message="Failed to post-process",
                            failure_exception=Exception("Failed to post-process exception"),
                        )
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR
                        generation.step(GENERATION_PROGRESS.POST_PROCESSING)
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

                return

            generation.on_post_processing_complete()
            if generation._result_type is bytes:
                generation.set_work_result(self._shared_image)
            elif generation._result_type is str:
                generation.set_work_result("Fake Text Generation Result")
        else:
            if generation._result_type is bytes:
                generation.set_work_result(self._shared_image)
            elif generation._result_type is str:
                generation.set_work_result("Fake Text Generation Result")

        if include_safety_check:
            generation.on_safety_checking()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

            if state_to_error_out_on == GENERATION_PROGRESS.SAFETY_CHECKING:
                with pytest.raises(RuntimeError, match="has exceeded the maximum number of errors for state"):
                    assert generation._state_error_limits is not None
                    for _ in range(generation._state_error_limits[GENERATION_PROGRESS.SAFETY_CHECKING]):
                        generation.on_error(
                            failed_message="Failed to safety check",
                            failure_exception=Exception("Failed to safety check exception"),
                        )
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR
                        generation.step(GENERATION_PROGRESS.SAFETY_CHECKING)
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

                return

            generation.on_safety_check_complete(is_csam=False, is_nsfw=False)

        if include_submit:
            generation.on_submitting()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

            if state_to_error_out_on == GENERATION_PROGRESS.SUBMITTING:
                with pytest.raises(RuntimeError, match="has exceeded the maximum number of errors for state"):
                    assert generation._state_error_limits is not None
                    for _ in range(generation._state_error_limits[GENERATION_PROGRESS.SUBMITTING]):
                        generation.on_error(
                            failed_message="Failed to submit",
                            failure_exception=Exception("Failed to submit exception"),
                        )
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR
                        generation.step(GENERATION_PROGRESS.SUBMITTING)
                        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

                return

            generation.on_submit_complete()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def simulate_hitting_all_error_limits(
        self,
        generations: list[HordeSingleGeneration[Any]],
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        include_submit: bool,
    ) -> None:
        error_limits = generations[0]._state_error_limits
        assert error_limits is not None

        for i, (state, _) in enumerate(error_limits.items()):
            self.simulate_hitting_error_limit(
                generations[i],
                state,
                include_preloading=include_preloading,
                include_generation=include_generation,
                include_post_processing=include_post_processing,
                include_safety_check=include_safety_check,
                include_submit=include_submit,
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
        include_submit: bool = True,
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
        if not generation.does_class_require_generation() and not include_generation and not include_post_processing:
            logger.trace(
                f"Skipping generation for {generation.__class__.__name__} as it does not require generation "
                "and generation and post-processing are not included",
            )
            return

        if generation.does_class_require_generation() and not include_generation:
            logger.trace(
                f"Skipping generation for {generation.__class__.__name__} as it requires generation and "
                "generation is not included",
            )
            return

        if include_post_processing and not generation.requires_post_processing:
            logger.trace(
                f"Skipping post-processing for {generation.__class__.__name__} as it does not require post-processing",
            )
            return

        if not include_submit and error_on_submit:
            logger.trace(
                f"Skipping submission for {generation.__class__.__name__} as it is not included and "
                "error_on_submit is True",
            )
            return

        error_flags = {
            "preloading": error_on_preloading and include_preloading,
            "generation": error_on_generation and include_generation,
            "post_processing": error_on_post_processing and include_post_processing,
            "safety_check": error_on_safety_check and include_safety_check,
            "submit": error_on_submit,
        }

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

        if include_submit:
            errors_count = self._simulate_submission(
                generation,
                error_on_submit=error_on_submit,
                errors_count=errors_count,
            )
        elif not include_submit and not generation.requires_submit:
            with pytest.raises(
                ValueError,
                match="Invalid transition from ",
            ):
                generation.on_submitting()

        assert generation.generation_failure_count == target_errors_count

    def _set_and_confirm_work_result(
        self,
        generation: HordeSingleGeneration[Any],
    ) -> None:
        if generation.result_type is bytes:
            generation.set_work_result(self._shared_image)

            assert generation.generation_results is not None
            assert len(generation.generation_results) == 1
            result_id, result = generation.generation_results.popitem()
            assert isinstance(result_id, UUID | str)
            assert result == self._shared_image
        elif generation.result_type is str:
            fake_result = "Fake Text Generation Result"
            generation.set_work_result(fake_result)
            assert generation.generation_results is not None
            assert len(generation.generation_results) == 1
            result_id, result = generation.generation_results.popitem()
            assert isinstance(result_id, UUID | str)
            assert result == fake_result
        else:
            raise ValueError(f"Unknown result type {generation.result_type}")

    def _simulate_preloading(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_preloading: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the preloading step for a `HordeSingleGeneration`."""

        from horde_sdk.worker.consts import GENERATION_PROGRESS

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

        from horde_sdk.worker.consts import GENERATION_PROGRESS

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

            self._set_and_confirm_work_result(generation)

        return errors_count

    def _simulate_post_processing(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_post_processing: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the post-processing step for a `HordeSingleGeneration`."""

        from horde_sdk.worker.consts import GENERATION_PROGRESS

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

        self._set_and_confirm_work_result(generation)

        return errors_count

    def _simulate_safety_check(
        self,
        generation: HordeSingleGeneration[Any],
        error_on_safety_check: bool,
        errors_count: int,
    ) -> int:
        """Simulate expected actions for the safety check step for a `HordeSingleGeneration`."""
        from horde_sdk.worker.consts import GENERATION_PROGRESS

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
        from horde_sdk.worker.consts import GENERATION_PROGRESS

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
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id_factory: Callable[[], str],
        permutations: list[GenerationPermutation],
        include_generation: bool,
        include_submit: bool,
        error_on_preloading: bool,
        error_on_generation: bool,
        error_on_post_processing: bool,
        error_on_safety_check: bool,
        error_on_submit: bool,
    ) -> None:
        """Run permutations of generation configurations.

        See the docstring for `GenerationPermutation` for more information on the possible configurations.

        Args:
            generation_class (type[HordeSingleGeneration[Any]]): The generation class to test.
            generation_id (str | Callable[[], str]): The generation ID or generation ID factory to\
                use for the test.
            permutations (list[GenerationPermutation]): The permutations to test.
            process_function (Callable[..., None]): The function to process the generation.
            include_generation (bool): Whether to include generation in the process.
            requires_generation (bool | None): Whether the generation requires generation.
            **kwargs (Any): Additional keyword arguments to pass to the process function.

        """
        dummy_generation = self.create_generation_instance(
            generation_class,
            generation_id_factory,
            include_submit,
            GenerationPermutation(
                include_preloading=True,
                include_generation=True,
                include_post_processing=True,
                include_safety_check=True,
                underlying_payload=permutations[0].underlying_payload,
            ),
            force_post_processing=True,
        )
        assert dummy_generation._state_error_limits is not None

        for state in dummy_generation._state_error_limits:
            assert state in GENERATION_PROGRESS.__members__

            addtl_generation_for_testing_error_limit = self.create_generation_instance(
                generation_class,
                generation_id_factory,
                include_submit,
                GenerationPermutation(
                    include_preloading=True,
                    include_generation=True,
                    include_post_processing=True,
                    include_safety_check=True,
                    underlying_payload=permutations[0].underlying_payload,
                ),
                force_post_processing=True,
            )

            self.simulate_hitting_error_limit(
                generation=addtl_generation_for_testing_error_limit,
                state_to_error_out_on=state,
                include_preloading=True,
                include_generation=True,
                include_post_processing=True,
                include_safety_check=True,
                include_submit=True,
            )

        for permutation in permutations:
            generation: HordeSingleGeneration[Any]

            generation = self.create_generation_instance(
                generation_class,
                generation_id_factory,
                include_submit,
                permutation,
            )
            self.process_generation(
                generation,
                include_generation=include_generation,
                include_safety_check=permutation.include_safety_check,
                include_preloading=permutation.include_preloading,
                include_post_processing=permutation.include_post_processing,
                include_submit=include_submit,
                error_on_preloading=error_on_preloading,
                error_on_generation=error_on_generation,
                error_on_post_processing=error_on_post_processing,
                error_on_safety_check=error_on_safety_check,
                error_on_submit=error_on_submit,
            )

    def create_generation_instance(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id_factory: Callable[[], str],
        include_submit: bool,
        permutation: GenerationPermutation,
        force_post_processing: bool = False,
    ) -> HordeSingleGeneration[Any]:
        generation: HordeSingleGeneration[Any]

        if generation_class == ImageSingleGeneration:
            assert isinstance(permutation.underlying_payload, ImageGenerationParameters)
            generation = ImageSingleGeneration(
                generation_id=generation_id_factory(),
                generation_parameters=permutation.underlying_payload,
                requires_submit=include_submit,
                extra_logging=False,
            )
            if force_post_processing:
                generation._requires_post_processing = True

            permutation.include_post_processing = generation.requires_post_processing
        elif generation_class == AlchemySingleGeneration:
            assert isinstance(permutation.underlying_payload, SingleAlchemyParameters)
            generation = AlchemySingleGeneration(
                generation_id=generation_id_factory(),
                generation_parameters=permutation.underlying_payload,
                requires_generation=permutation.include_post_processing,
                requires_post_processing=permutation.include_post_processing,
                requires_safety_check=permutation.include_safety_check,
                requires_submit=include_submit,
                extra_logging=False,
            )

        elif generation_class == TextSingleGeneration:
            assert isinstance(permutation.underlying_payload, TextGenerationParameters)
            generation = TextSingleGeneration(
                generation_id=generation_id_factory(),
                generation_parameters=permutation.underlying_payload,
                requires_post_processing=permutation.include_post_processing,
                requires_safety_check=permutation.include_safety_check,
                requires_submit=include_submit,
                extra_logging=False,
            )

        return generation

    @pytest.mark.parametrize(
        "generation_class,include_submit,include_generation",
        [
            (ImageSingleGeneration, True, True),
            (ImageSingleGeneration, False, True),
            (AlchemySingleGeneration, True, True),
            (AlchemySingleGeneration, False, True),
            (AlchemySingleGeneration, True, False),
            (AlchemySingleGeneration, False, False),
            (TextSingleGeneration, True, True),
            (TextSingleGeneration, False, True),
            (TextSingleGeneration, True, False),
            (TextSingleGeneration, False, False),
        ],
    )
    def test_error_handling(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        include_generation: bool,
        include_submit: bool,
        id_factory_str: Callable[[], str],
        image_permutations: list[GenerationPermutation],
        alchemy_permutations: list[GenerationPermutation],
        text_permutations: list[GenerationPermutation],
    ) -> None:
        """Test error handling for all permutations of generation configurations."""

        from collections import namedtuple

        ErrorPermutation = namedtuple(
            "ErrorPermutation",
            [
                "error_on_preloading",
                "error_on_generation",
                "error_on_post_processing",
                "error_on_safety_check",
                "error_on_submit",
            ],
        )

        error_permutations = [
            ErrorPermutation(
                error_on_preloading,
                error_on_generation,
                error_on_post_processing,
                error_on_safety_check,
                error_on_submit,
            )
            for error_on_preloading in [True, False]
            for error_on_generation in [True, False]
            for error_on_post_processing in [True, False]
            for error_on_safety_check in [True, False]
            for error_on_submit in [True, False]
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
                    id_factory_str,
                    permutations,
                    include_generation=include_generation,
                    include_submit=include_submit,
                    error_on_preloading=error_permutation.error_on_preloading,
                    error_on_generation=error_permutation.error_on_generation,
                    error_on_post_processing=error_permutation.error_on_post_processing,
                    error_on_safety_check=error_permutation.error_on_safety_check,
                    error_on_submit=error_permutation.error_on_submit,
                )
            except Exception as e:
                logger.exception(f"Error running permutations for {generation_class.__name__}")
                logger.exception(f"Error permutation: {error_permutation}")
                logger.exception(f"Generation permutations: {permutations}")
                logger.exception(f"included generation: {include_generation}")

                raise e
