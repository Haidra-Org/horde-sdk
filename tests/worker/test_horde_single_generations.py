from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
import yaml
from loguru import logger

from horde_sdk.generation_parameters.alchemy import (
    AlchemyParameters,
    SingleAlchemyParameters,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.alchemy.object_models import (
    UpscaleAlchemyParametersTemplate,
)
from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.generation_parameters.image.object_models import (
    BasicImageGenerationParametersTemplate,
    ImageGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.text import TextGenerationParameters
from horde_sdk.generation_parameters.text.object_models import (
    BasicTextGenerationParametersTemplate,
    TextGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.utils import ResultIdAllocator
from horde_sdk.safety import (
    ImageSafetyResult,
    SafetyResult,
    SafetyRules,
    default_image_safety_rules,
)
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    base_generate_progress_transitions,
    black_box_generate_progress_transitions,
)
from horde_sdk.worker.generations import (
    AlchemySingleGeneration,
    ImageSingleGeneration,
    TextSingleGeneration,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration


def test_write_progress_transitions() -> None:
    """Write the progress transitions to the docs folder."""

    # Convert enum dictionaries to string dictionaries before serializing to YAML
    def convert_enum_dict_to_string_dict(
        enum_dict: dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]],
    ) -> dict[str, list[str]]:
        string_dict = {}
        for key, values in enum_dict.items():
            string_key = key.name  # Get the name of the enum
            string_values = [value.name for value in values]  # Convert enum values to strings
            string_dict[string_key] = string_values
        return string_dict

    transitions_to_write = [
        (convert_enum_dict_to_string_dict(base_generate_progress_transitions), "base_transitions.yaml"),
        (convert_enum_dict_to_string_dict(black_box_generate_progress_transitions), "black_box_transitions.yaml"),
    ]

    output_folder = "docs/worker"

    for transitions in transitions_to_write:
        transitions_dict, filename = transitions
        output_path = f"{output_folder}/{filename}"

        with open(output_path, "w") as file:
            yaml.dump(transitions_dict, file, default_flow_style=False, sort_keys=False)

        logger.info(f"Wrote progress transitions to {output_path}")


class GenerationPermutation:
    """A permutation of possible generation configurations.

    For example, text generation may not require post-processing or safety checks, while image generation may require
    both. For testing, we can create permutations of these configurations to ensure that the generation process works
    as expected across all possible configurations.

    """

    def __init__(
        self,
        *,
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        include_submit: bool = False,
        underlying_payload: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
    ) -> None:
        """Initialize the permutation.

        Args:
            include_preloading (bool): Whether to include preloading in the generation process.
            include_generation (bool): Whether to include generation in the generation process.
            include_post_processing (bool): Whether to include post-processing in the generation process.
            include_safety_check (bool): Whether to include a safety check in the generation process.
            include_submit (bool): Whether to include submission in the generation process.
            underlying_payload (ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters): The
                underlying payload for the generation process.
        """
        self.include_preloading = include_preloading
        self.include_generation = include_generation
        self.include_post_processing = include_post_processing
        self.include_safety_check = include_safety_check
        self.include_submit = include_submit
        self.underlying_payload = underlying_payload


def create_permutations(
    payload: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
    *,
    required_preloading: bool = False,
    required_post_processing: bool = False,
    required_generation: bool = False,
    required_safety_check: bool = False,
    required_submit: bool = False,
) -> list[GenerationPermutation]:
    permutations = []

    for include_generation in [True] if required_generation else [False, True]:
        for include_post_processing in [True] if required_post_processing else [False, True]:
            if not (include_generation or include_post_processing):
                continue

            for include_preloading in [True] if required_preloading else [False, True]:
                for include_safety_check in [True] if required_safety_check else [False, True]:
                    if not (include_safety_check or include_generation or include_post_processing):
                        continue

                    for include_submit in [True] if required_submit else [False, True]:
                        permutations.append(
                            GenerationPermutation(
                                include_preloading=include_preloading,
                                include_generation=include_generation,
                                include_post_processing=include_post_processing,
                                include_safety_check=include_safety_check,
                                include_submit=include_submit,
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
        required_post_processing=True,
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


def test_image_single_generation_from_template_applies_updates() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="placeholder"),
    )
    generation = ImageSingleGeneration.from_template(
        template,
        base_param_updates=BasicImageGenerationParametersTemplate(model="test-model", prompt="updated"),
        result_ids=("result-1",),
    )

    assert generation.generation_parameters.base_params.prompt == "updated"
    assert generation.generation_parameters.result_ids == ["result-1"]


def test_image_single_generation_allocator_is_deterministic() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="allocator prompt", model="image-model"),
    )
    template.batch_size = 2

    allocator = ResultIdAllocator()
    first = ImageSingleGeneration.from_template(template, allocator=allocator, seed="image-seed")
    second = ImageSingleGeneration.from_template(template, allocator=allocator, seed="image-seed")

    assert first.generation_parameters.result_ids == second.generation_parameters.result_ids

    variant_template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="allocator prompt variant", model="image-model"),
    )
    variant_template.batch_size = 2
    third = ImageSingleGeneration.from_template(variant_template, allocator=allocator, seed="image-seed")

    assert first.generation_parameters.result_ids != third.generation_parameters.result_ids


def test_text_single_generation_from_template_allocates_result_id() -> None:
    template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="base",
            model="test-model",
        ),
    )

    generation = TextSingleGeneration.from_template(
        template,
        base_param_updates=BasicTextGenerationParametersTemplate(prompt="final"),
    )

    assert generation.generation_parameters.base_params.prompt == "final"
    assert generation.generation_parameters.result_ids is not None
    assert len(generation.generation_parameters.result_ids) == 1


def test_text_single_generation_allocator_is_deterministic() -> None:
    template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="allocator",
            model="allocator-model",
        ),
    )

    allocator = ResultIdAllocator()
    first = TextSingleGeneration.from_template(template, allocator=allocator, seed="text-seed")
    second = TextSingleGeneration.from_template(template, allocator=allocator, seed="text-seed")

    assert first.generation_parameters.result_ids == second.generation_parameters.result_ids

    modified_template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="allocator-2",
            model="allocator-model",
        ),
    )
    third = TextSingleGeneration.from_template(modified_template, allocator=allocator, seed="text-seed")

    assert first.generation_parameters.result_ids != third.generation_parameters.result_ids


def test_alchemy_single_generation_from_template_sets_source_image() -> None:
    template = UpscaleAlchemyParametersTemplate()
    generation = AlchemySingleGeneration.from_template(
        template,
        source_image=b"image-bytes",
        default_form=KNOWN_ALCHEMY_FORMS.post_process,
    )

    assert generation.generation_parameters.source_image == b"image-bytes"
    assert generation.generation_parameters.form == KNOWN_ALCHEMY_FORMS.post_process
    assert generation.generation_parameters.result_id is not None


class TestHordeSingleGeneration:
    """Test the `HordeSingleGeneration` class."""

    _shared_image: bytes

    @pytest.fixture(autouse=True)
    def setup(self, default_testing_image_bytes: bytes) -> None:
        self._shared_image = default_testing_image_bytes

    def test_image_generation_results_preserve_dispatch_identifiers(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        dispatch_ids = ["dispatch-image-1"]
        generation = ImageSingleGeneration(
            generation_parameters=simple_image_generation_parameters,
            dispatch_result_ids=dispatch_ids,
        )

        generation.on_generating()
        generation.on_generation_work_complete(result=self._shared_image)

        results_snapshot = generation.generation_results
        assert list(results_snapshot.keys()) == generation.result_ids

        result_id, payload = results_snapshot.popitem()
        assert payload == self._shared_image
        assert result_id == generation.result_ids[-1]

        assert generation.dispatch_result_ids == dispatch_ids
        mutated_ids = generation.dispatch_result_ids
        if mutated_ids is not None:
            mutated_ids.append("mutated")
        assert generation.dispatch_result_ids == dispatch_ids
        assert len(generation.generation_results) == 1

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

    def test_text_generation_results_preserve_dispatch_identifiers(
        self,
        simple_text_generation_parameters: TextGenerationParameters,
    ) -> None:
        dispatch_ids = ["dispatch-text-1"]
        generation = TextSingleGeneration(
            generation_parameters=simple_text_generation_parameters,
            dispatch_result_ids=dispatch_ids,
        )

        generation.on_generating()
        generation.on_generation_work_complete(result="generated text")

        results_snapshot = generation.generation_results
        assert list(results_snapshot.keys()) == generation.result_ids

        result_id, payload = results_snapshot.popitem()
        assert payload == "generated text"
        assert result_id == generation.result_ids[-1]

        assert generation.dispatch_result_ids == dispatch_ids
        mutated_ids = generation.dispatch_result_ids
        if mutated_ids is not None:
            mutated_ids.append("mutated")
        assert generation.dispatch_result_ids == dispatch_ids
        assert len(generation.generation_results) == 1

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

    def test_alchemy_generation_results_preserve_dispatch_identifiers(
        self,
        simple_alchemy_generation_parameters: AlchemyParameters,
    ) -> None:
        assert len(simple_alchemy_generation_parameters.all_alchemy_operations) == 1
        operation_parameters = simple_alchemy_generation_parameters.all_alchemy_operations[0]

        dispatch_ids = ["dispatch-alchemy-1"]
        generation = AlchemySingleGeneration(
            generation_parameters=operation_parameters,
            dispatch_result_ids=dispatch_ids,
        )

        generation.on_post_processing()
        generation.set_work_result(self._shared_image)
        generation.on_post_processing_complete()

        results_snapshot = generation.generation_results
        assert list(results_snapshot.keys()) == generation.result_ids

        result_id, payload = results_snapshot.popitem()
        assert payload == self._shared_image
        assert result_id == generation.result_ids[-1]

        assert generation.dispatch_result_ids == dispatch_ids
        mutated_ids = generation.dispatch_result_ids
        if mutated_ids is not None:
            mutated_ids.append("mutated")
        assert generation.dispatch_result_ids == dispatch_ids
        assert len(generation.generation_results) == 1

    def test_none_generation_init(
        self,
    ) -> None:
        """Test that an exception is raised when a generation is initialized with a `None` ID."""

        with pytest.raises(TypeError):
            ImageSingleGeneration(generation_id=None)  # type: ignore

    def test_black_box_mode_no_submit(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        """Test that a generation can be initialized in black box mode."""
        from horde_sdk.worker.consts import GENERATION_PROGRESS
        from horde_sdk.worker.generations import ImageSingleGeneration

        generation_id = str(UUID("00000000-0000-0000-0000-000000000000"))
        generation = ImageSingleGeneration(
            generation_id=generation_id,
            generation_parameters=simple_image_generation_parameters,
            black_box_mode=True,
            requires_submit=False,
        )

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED
        assert generation.black_box_mode is True

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()
        generation.set_work_result(self._shared_image)
        generation.on_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.COMPLETE

    def test_black_box_mode_with_submit(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        """Test that a generation can be initialized in black box mode with submission."""
        from horde_sdk.worker.consts import GENERATION_PROGRESS
        from horde_sdk.worker.generations import ImageSingleGeneration

        generation_id = str(UUID("00000000-0000-0000-0000-000000000000"))
        generation = ImageSingleGeneration(
            generation_id=generation_id,
            generation_parameters=simple_image_generation_parameters,
            black_box_mode=True,
            requires_submit=True,
        )

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED
        assert generation.black_box_mode is True

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()
        generation.set_work_result(self._shared_image)
        generation.on_pending_submit()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_black_box_mode_with_submit_and_safety_check(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
    ) -> None:
        """Test that a generation can be initialized in black box mode with submission."""
        from horde_sdk.worker.consts import GENERATION_PROGRESS
        from horde_sdk.worker.generations import ImageSingleGeneration

        generation_id = str(UUID("00000000-0000-0000-0000-000000000000"))
        generation = ImageSingleGeneration(
            generation_id=generation_id,
            generation_parameters=simple_image_generation_parameters,
            black_box_mode=True,
            requires_submit=True,
        )

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED
        assert generation.black_box_mode is True

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()
        generation.set_work_result(self._shared_image)
        generation.on_pending_safety_check()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

        generation.on_safety_checking()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(
            batch_index=0,
            safety_result=ImageSafetyResult(
                is_nsfw=False,
                is_csam=False,
            ),
        )
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SUBMIT

        generation.on_submitting()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        generation.on_submit_complete()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

    def test_alchemy_safety_only(
        self,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        assert len(simple_alchemy_generation_parameters_nsfw_detect.all_alchemy_operations) == 1
        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        assert len(simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors) == 1

        nsfw_parameters = simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0]

        generation = AlchemySingleGeneration(
            generation_parameters=nsfw_parameters,
            requires_post_processing=False,
            requires_submit=False,
        )

        generation.on_preloading()

    def _run_censor_test(
        self,
        *,
        generation_parameters: ImageGenerationParameters | SingleAlchemyParameters,
        generation_type: type[HordeSingleGeneration[Any]],
        result_id: UUID,
        is_nsfw: bool,
        is_csam: bool,
        expect_censored: bool,
        safety_rules: SafetyRules,
    ) -> None:
        from horde_sdk.worker.consts import GENERATION_PROGRESS

        generation_id = str(UUID("00000000-0000-0000-0000-000000000000"))

        generation: HordeSingleGeneration[Any] = generation_type(
            generation_id=generation_id,
            generation_parameters=generation_parameters,
            safety_rules=safety_rules,
            result_ids=[result_id],
            black_box_mode=True,
        )

        assert generation.get_generation_progress() == GENERATION_PROGRESS.NOT_STARTED
        assert generation.black_box_mode is True

        generation.on_generating()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        generation.on_generation_work_complete()
        generation.set_work_result(self._shared_image)

        generation.on_pending_safety_check()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

        generation.on_safety_checking()
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(
            batch_index=0,
            safety_result=ImageSafetyResult(
                is_nsfw=is_nsfw,
                is_csam=is_csam,
            ),
        )

        safety_check_results = generation.get_safety_check_results()
        assert safety_check_results is not None
        assert len(safety_check_results) == 1
        assert safety_check_results[0] is not None
        assert safety_check_results[0].is_nsfw == is_nsfw
        assert safety_check_results[0].is_csam == is_csam

        assert result_id in generation.generation_results
        if expect_censored or is_csam:
            assert generation.generation_results[result_id] is None
        else:
            assert generation.generation_results[result_id] is not None

    def test_safety_censored_results(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation can be censored based on safety results."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000000"),
            is_nsfw=True,
            is_csam=False,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000000"),
            is_nsfw=True,
            is_csam=False,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

    def test_safety_censoring_not_expected(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation is not censored when it shouldn't be."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000001"),
            is_nsfw=False,
            is_csam=False,
            expect_censored=False,
            safety_rules=default_image_safety_rules,
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000001"),
            is_nsfw=False,
            is_csam=False,
            expect_censored=False,
            safety_rules=default_image_safety_rules,
        )

    def test_safety_censored_csam(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation is censored when CSAM is detected."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000002"),
            is_nsfw=False,
            is_csam=True,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000002"),
            is_nsfw=False,
            is_csam=True,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

    def test_safety_censored_both(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation is censored when both NSFW and CSAM are detected."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000003"),
            is_nsfw=True,
            is_csam=True,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000003"),
            is_nsfw=True,
            is_csam=True,
            expect_censored=True,
            safety_rules=default_image_safety_rules,
        )

    def test_safety_uncensored_rules(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation is not censored when the safety rules are set to not censor."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000004"),
            is_nsfw=True,
            is_csam=False,
            expect_censored=False,
            safety_rules=SafetyRules(
                should_censor_nsfw=False,
                should_censor_hate_speech=False,
                should_censor_violent=False,
                should_censor_self_harm=False,
            ),
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000004"),
            is_nsfw=True,
            is_csam=False,
            expect_censored=False,
            safety_rules=SafetyRules(
                should_censor_nsfw=False,
                should_censor_hate_speech=False,
                should_censor_violent=False,
                should_censor_self_harm=False,
            ),
        )

    def test_safety_csam_always_censors(
        self,
        simple_image_generation_parameters: ImageGenerationParameters,
        simple_alchemy_generation_parameters_nsfw_detect: AlchemyParameters,
    ) -> None:
        """Test that a generation is always censored when CSAM is detected, regardless of safety rules."""
        self._run_censor_test(
            generation_parameters=simple_image_generation_parameters,
            generation_type=ImageSingleGeneration,
            result_id=UUID("00000000-0000-0000-9999-000000000005"),
            is_nsfw=False,
            is_csam=True,
            expect_censored=True,
            safety_rules=SafetyRules(
                should_censor_nsfw=False,
                should_censor_hate_speech=False,
                should_censor_violent=False,
                should_censor_self_harm=False,
            ),
        )

        assert simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors is not None
        self._run_censor_test(
            generation_parameters=simple_alchemy_generation_parameters_nsfw_detect.nsfw_detectors[0],
            generation_type=AlchemySingleGeneration,
            result_id=UUID("00000000-0000-0000-8888-000000000005"),
            is_nsfw=False,
            is_csam=True,
            expect_censored=True,
            safety_rules=SafetyRules(
                should_censor_nsfw=False,
                should_censor_hate_speech=False,
                should_censor_violent=False,
                should_censor_self_harm=False,
            ),
        )

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

        assert generation._safety_results[0] is None

        assert len(generation.generation_results) == 0

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
            f"Invalid transition from {GENERATION_PROGRESS.NOT_STARTED} to {GENERATION_PROGRESS.PENDING_SAFETY_CHECK}",
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
            f"Invalid transition from {GENERATION_PROGRESS.PRELOADING} to {GENERATION_PROGRESS.PENDING_SAFETY_CHECK}",
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
            generation.on_safety_check_complete(
                batch_index=0,
                safety_result=ImageSafetyResult(
                    is_nsfw=False,
                    is_csam=False,
                ),
            )

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

        generation.on_safety_check_complete(
            batch_index=0,
            safety_result=ImageSafetyResult(
                is_nsfw=False,
                is_csam=False,
            ),
        )
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
        assert isinstance(generation_result_id, UUID | str)
        assert generation_result is not None

        if include_safety_check:
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PENDING_SAFETY_CHECK

            generation.on_safety_checking()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

            generation.on_safety_check_complete(
                batch_index=0,
                safety_result=SafetyResult(
                    is_nsfw=False,
                    is_csam=False,
                ),
            )

            assert generation._safety_results[0] is not None
            assert generation._safety_results[0].is_nsfw is False
            assert generation._safety_results[0].is_csam is False

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

        if generation.requires_post_processing is not include_post_processing:
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

                return
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

            generation.on_safety_check_complete(
                batch_index=0,
                safety_result=SafetyResult(
                    is_nsfw=False,
                    is_csam=False,
                ),
            )
            assert generation._safety_results[0] is not None
            assert generation._safety_results[0].is_nsfw is False
            assert generation._safety_results[0].is_csam is False

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

    def simulate_abort(
        self,
        generation: HordeSingleGeneration[Any],
        state_to_abort_on: GENERATION_PROGRESS,
        include_preloading: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        include_submit: bool,
        error_message: str,
        error_exception: Exception,
    ) -> None:
        """Simulate aborting a generation.

        This function will simulate aborting a generation by calling the `on_abort` method on the generation object.
        It will also check that the generation progresses through the correct states.

        If a step is not requested, it will be skipped.
        """
        from horde_sdk.worker.consts import GENERATION_PROGRESS

        if state_to_abort_on == GENERATION_PROGRESS.PRELOADING and not include_preloading:
            return
        if state_to_abort_on == GENERATION_PROGRESS.GENERATING and not include_generation:
            return
        if state_to_abort_on == GENERATION_PROGRESS.POST_PROCESSING and not include_post_processing:
            return
        if state_to_abort_on == GENERATION_PROGRESS.SAFETY_CHECKING and not include_safety_check:
            return
        if state_to_abort_on == GENERATION_PROGRESS.SUBMITTING and not include_submit:
            return

        if not (include_preloading or include_generation or include_post_processing or include_safety_check):
            return

        if include_submit and not generation.requires_submit:
            return

        if state_to_abort_on == GENERATION_PROGRESS.NOT_STARTED:
            generation.on_abort(
                failed_message=error_message,
                failure_exception=error_exception,
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
            return

        if include_preloading:
            generation.on_preloading()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

            if state_to_abort_on == GENERATION_PROGRESS.PRELOADING:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return

            generation.on_preloading_complete()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING_COMPLETE

        if include_generation:
            generation.on_generating()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

            if state_to_abort_on == GENERATION_PROGRESS.GENERATING:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return

            generation.on_generation_work_complete()

            if not include_post_processing:
                if generation.result_type is bytes:
                    generation.set_work_result(self._shared_image)
                elif generation.result_type is str:
                    generation.set_work_result("Fake Text Generation Result")

        if include_post_processing:
            generation.on_post_processing()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

            if state_to_abort_on == GENERATION_PROGRESS.POST_PROCESSING:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return

            generation.on_post_processing_complete()
            if generation._result_type is bytes:
                generation.set_work_result(self._shared_image)
            elif generation._result_type is str:
                generation.set_work_result("Fake Text Generation Result")

        if include_safety_check:
            generation.on_safety_checking()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING
            if state_to_abort_on == GENERATION_PROGRESS.SAFETY_CHECKING:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return
            generation.on_safety_check_complete(
                batch_index=0,
                safety_result=SafetyResult(
                    is_nsfw=False,
                    is_csam=False,
                ),
            )
            assert generation._safety_results[0] is not None
            assert generation._safety_results[0].is_nsfw is False
            assert generation._safety_results[0].is_csam is False

        if include_submit:
            generation.on_submitting()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

            if state_to_abort_on == GENERATION_PROGRESS.SUBMITTING:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return

            generation.on_submit_complete()
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

            if state_to_abort_on == GENERATION_PROGRESS.SUBMIT_COMPLETE:
                generation.on_abort(
                    failed_message=error_message,
                    failure_exception=error_exception,
                )

                assert generation.get_generation_progress() == GENERATION_PROGRESS.ABORTED
                return

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
        if error_on_preloading and not include_preloading:
            return
        if error_on_generation and not include_generation:
            return
        if error_on_post_processing and not include_post_processing:
            return
        if error_on_safety_check and not include_safety_check:
            return
        if error_on_submit and not include_submit:
            return

        error_flags = {
            "preloading": error_on_preloading and include_preloading,
            "generation": error_on_generation and include_generation,
            "post_processing": error_on_post_processing
            and include_post_processing
            and generation.requires_post_processing,
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

        if include_post_processing and generation.requires_post_processing:
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

        assert generation.step(GENERATION_PROGRESS.PRELOADING) == GENERATION_PROGRESS.PRELOADING
        assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

        if error_on_preloading:
            errors_count += 1
            assert (
                generation.on_error(
                    failed_message="Failed to preload",
                    failure_exception=Exception("Failed to preload exception"),
                )
                == GENERATION_PROGRESS.ERROR
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            assert generation.step(GENERATION_PROGRESS.PRELOADING) == GENERATION_PROGRESS.PRELOADING
            assert generation.get_generation_progress() == GENERATION_PROGRESS.PRELOADING

            assert generation.generation_failure_count == errors_count
            assert generation.errored_states is not None
            error_state, error_time = generation.errored_states[-1]
            assert error_state == GENERATION_PROGRESS.PRELOADING
            assert error_time != 0

        assert generation.on_preloading_complete() == GENERATION_PROGRESS.PRELOADING_COMPLETE
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

        assert generation.step(GENERATION_PROGRESS.GENERATING) == GENERATION_PROGRESS.GENERATING
        assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

        if error_on_generation:
            errors_count += 1
            assert (
                generation.on_error(
                    failed_message="Failed to generate",
                    failure_exception=Exception("Failed to generate exception"),
                )
                == GENERATION_PROGRESS.ERROR
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            assert generation.step(GENERATION_PROGRESS.GENERATING) == GENERATION_PROGRESS.GENERATING
            assert generation.get_generation_progress() == GENERATION_PROGRESS.GENERATING

            assert generation.generation_failure_count == errors_count
            assert generation.errored_states is not None
            error_state, error_time = generation.errored_states[-1]
            assert error_state == GENERATION_PROGRESS.GENERATING
            assert error_time != 0

        if include_post_processing and generation.requires_post_processing:
            assert generation.on_generation_work_complete() == GENERATION_PROGRESS.PENDING_POST_PROCESSING
        else:
            assert generation.on_generation_work_complete() in (
                GENERATION_PROGRESS.PENDING_SUBMIT,
                GENERATION_PROGRESS.PENDING_SAFETY_CHECK,
                GENERATION_PROGRESS.PENDING_POST_PROCESSING,
                GENERATION_PROGRESS.COMPLETE,
            )

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

        assert generation.step(GENERATION_PROGRESS.POST_PROCESSING) == GENERATION_PROGRESS.POST_PROCESSING
        assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        if error_on_post_processing:
            errors_count += 1
            assert (
                generation.on_error(
                    failed_message="Failed during post-processing",
                    failure_exception=Exception("Failed during post-processing exception"),
                )
                == GENERATION_PROGRESS.ERROR
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            generation.step(GENERATION_PROGRESS.POST_PROCESSING)
            assert generation.get_generation_progress() == GENERATION_PROGRESS.POST_PROCESSING

        assert generation.on_post_processing_complete() in (
            GENERATION_PROGRESS.PENDING_SUBMIT,
            GENERATION_PROGRESS.PENDING_SAFETY_CHECK,
            GENERATION_PROGRESS.COMPLETE,
        )

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

        assert generation.step(GENERATION_PROGRESS.SAFETY_CHECKING) == GENERATION_PROGRESS.SAFETY_CHECKING
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        if error_on_safety_check:
            errors_count += 1
            assert (
                generation.on_error(
                    failed_message="Failed during safety check",
                    failure_exception=Exception("Failed during safety check exception"),
                )
                == GENERATION_PROGRESS.ERROR
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            assert generation.step(GENERATION_PROGRESS.SAFETY_CHECKING) == GENERATION_PROGRESS.SAFETY_CHECKING
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SAFETY_CHECKING

        generation.on_safety_check_complete(
            batch_index=0,
            safety_result=SafetyResult(
                is_nsfw=False,
                is_csam=False,
            ),
        )
        assert generation._safety_results[0] is not None
        assert generation._safety_results[0].is_nsfw is False
        assert generation._safety_results[0].is_csam is False

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

        assert generation.step(GENERATION_PROGRESS.SUBMITTING) == GENERATION_PROGRESS.SUBMITTING
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        if error_on_submit:
            errors_count += 1
            assert (
                generation.on_error(
                    failed_message="Failed during submission",
                    failure_exception=Exception("Failed during submission exception"),
                )
                == GENERATION_PROGRESS.ERROR
            )
            assert generation.get_generation_progress() == GENERATION_PROGRESS.ERROR

            assert generation.step(GENERATION_PROGRESS.SUBMITTING) == GENERATION_PROGRESS.SUBMITTING
            assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMITTING

        assert generation.on_submit_complete() == GENERATION_PROGRESS.SUBMIT_COMPLETE
        assert generation.get_generation_progress() == GENERATION_PROGRESS.SUBMIT_COMPLETE

        return errors_count

    def run_generation_abort_and_error_tests(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id_factory: Callable[[], str],
        generation_parameters: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
        include_generation: bool,
        include_post_processing: bool,
        include_safety_check: bool,
        include_submit: bool,
    ) -> None:
        states_to_test = list(GENERATION_PROGRESS.__members__.values())
        states_to_test = [s for s in states_to_test if s not in generation_class.default_interrupt_states()]
        states_to_test.remove(GENERATION_PROGRESS.ERROR)

        for state in states_to_test:
            if self.is_conflicting_permutations(
                generation_class_requires_generation=generation_class.does_class_require_generation(),
                generation_requires_post_processing=include_post_processing,
                generation_requires_submit=include_submit,
                include_generation=include_generation,
                include_post_processing=include_post_processing,
                include_submit=include_submit,
            ):
                continue

            abort_generation = self.create_generation_instance(
                generation_class,
                generation_id_factory(),
                generation_parameters,
                requires_generation=include_generation,
                requires_post_processing=include_post_processing,
                requires_safety_check=include_safety_check,
                requires_submit=include_submit,
                strict_transition_mode=True,
                extra_logging=False,
            )

            if abort_generation.requires_post_processing is not include_post_processing:
                continue

            self.simulate_abort(
                generation=abort_generation,
                state_to_abort_on=state,
                include_preloading=True,
                include_generation=include_generation,
                include_post_processing=include_post_processing,
                include_safety_check=include_safety_check,
                include_submit=include_submit,
                error_message="Simulated error message",
                error_exception=Exception("Simulated error exception"),
            )

        generation_strict = self.create_generation_instance(
            generation_class,
            generation_id_factory(),
            generation_parameters,
            requires_generation=include_generation,
            requires_post_processing=include_post_processing,
            requires_safety_check=include_safety_check,
            requires_submit=include_submit,
            strict_transition_mode=True,
            extra_logging=False,
        )
        self.simulate_hitting_error_limit(
            generation=generation_strict,
            state_to_error_out_on=state,
            include_preloading=True,
            include_generation=include_generation,
            include_post_processing=include_post_processing,
            include_safety_check=include_safety_check,
            include_submit=include_submit,
        )

        generation_non_strict = self.create_generation_instance(
            generation_class,
            generation_id_factory(),
            generation_parameters,
            requires_generation=include_generation,
            requires_post_processing=include_post_processing,
            requires_safety_check=include_safety_check,
            requires_submit=include_submit,
            strict_transition_mode=False,
            extra_logging=False,
        )

        self.simulate_hitting_error_limit(
            generation=generation_non_strict,
            state_to_error_out_on=state,
            include_preloading=True,
            include_generation=include_generation,
            include_post_processing=include_post_processing,
            include_safety_check=include_safety_check,
            include_submit=include_submit,
        )

    def run_generation_test_permutations(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id_factory: Callable[[], str],
        permutations: list[GenerationPermutation],
        error_on_preloading: bool,
        error_on_generation: bool,
        error_on_post_processing: bool,
        error_on_safety_check: bool,
        error_on_submit: bool,
    ) -> None:
        """Run permutations of generation configurations.

        Additionally ensures that error limits are respected and that aborting a generation works as expected.

        See the docstring for `GenerationPermutation` for more information on the possible configurations.

        Args:
            generation_class (type[HordeSingleGeneration[Any]]): The generation class to test.
            generation_id_factory (Callable[[], str]): A factory function to create unique generation IDs.
            permutations (list[GenerationPermutation]): A list of permutations to test.
            include_generation (bool): Whether to force include the generation step.
            include_submit (bool): Whether to force include the submit step.
            error_on_preloading (bool): Whether to simulate an error during preloading.
            error_on_generation (bool): Whether to simulate an error during generation.
            error_on_post_processing (bool): Whether to simulate an error during post-processing.
            error_on_safety_check (bool): Whether to simulate an error during safety check.
            error_on_submit (bool): Whether to simulate an error during submission.
        """
        for permutation in permutations:
            generation: HordeSingleGeneration[Any]

            generation = self.create_generation_instance_for_permutation(
                generation_class,
                generation_id_factory,
                permutation.include_submit,
                permutation,
            )

            self.process_generation(
                generation,
                include_generation=permutation.include_generation,
                include_safety_check=permutation.include_safety_check,
                include_preloading=permutation.include_preloading,
                include_post_processing=permutation.include_post_processing,
                include_submit=permutation.include_submit,
                error_on_preloading=error_on_preloading,
                error_on_generation=error_on_generation,
                error_on_post_processing=error_on_post_processing,
                error_on_safety_check=error_on_safety_check,
                error_on_submit=error_on_submit,
            )

    @staticmethod
    def is_conflicting_permutations(
        generation_class_requires_generation: bool,
        generation_requires_post_processing: bool,
        generation_requires_submit: bool,
        include_generation: bool,
        include_post_processing: bool,
        include_submit: bool,
    ) -> bool:
        """Check if the given generation and configurations are conflicting.

        Args:
            generation (HordeSingleGeneration[Any]): The generation to check.
            include_generation (bool): Whether to force include the generation step.
            include_post_processing (bool): Whether to force include the post-processing step.
            include_submit (bool): Whether to force include the submit step.

        Returns:
            bool: True if the configurations are conflicting, False otherwise.
        """
        if not generation_class_requires_generation and not include_generation:
            return True

        if generation_class_requires_generation and not include_generation:
            return True

        if not include_generation and not include_post_processing:
            return True

        if include_post_processing is not generation_requires_post_processing:
            return True

        if include_submit is not generation_requires_submit:
            return True

        return bool(not (include_generation or include_post_processing))

    @staticmethod
    def create_generation_instance(
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id: str,
        generation_parameters: ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters,
        requires_generation: bool,
        requires_post_processing: bool,
        requires_safety_check: bool,
        requires_submit: bool,
        strict_transition_mode: bool,
        extra_logging: bool = False,
    ) -> HordeSingleGeneration[Any]:
        """Create a generation instance for the given class and parameters.

        Args:
            generation_class (type[HordeSingleGeneration[Any]]): The generation class to create.
            generation_id (str): The ID of the generation.
            generation_parameters (ImageGenerationParameters | TextGenerationParameters | SingleAlchemyParameters):
                The parameters for the generation.
            requires_generation (bool): Whether the generation requires generation.
            requires_post_processing (bool): Whether the generation requires post-processing.
            requires_safety_check (bool): Whether the generation requires a safety check.
            requires_submit (bool): Whether the generation requires submission.
            force_post_processing (bool): Whether to force post-processing.
            strict_transition_mode (bool): Whether to use strict transition mode.
            extra_logging (bool, optional): Whether to enable extra logging. Defaults to False.

        Returns:
            HordeSingleGeneration[Any]: The created generation instance.
        """

        generation: HordeSingleGeneration[Any]

        if generation_class == ImageSingleGeneration:
            assert isinstance(generation_parameters, ImageGenerationParameters)
            generation = ImageSingleGeneration(
                generation_id=generation_id,
                generation_parameters=generation_parameters,
                requires_submit=requires_submit,
                extra_logging=extra_logging,
                strict_transition_mode=strict_transition_mode,
            )
        elif generation_class == AlchemySingleGeneration:
            assert isinstance(generation_parameters, SingleAlchemyParameters)
            generation = AlchemySingleGeneration(
                generation_id=generation_id,
                generation_parameters=generation_parameters,
                requires_generation=requires_generation,
                requires_post_processing=requires_post_processing,
                requires_safety_check=requires_safety_check,
                requires_submit=requires_submit,
                extra_logging=extra_logging,
                strict_transition_mode=strict_transition_mode,
            )
        elif generation_class == TextSingleGeneration:
            assert isinstance(generation_parameters, TextGenerationParameters)
            generation = TextSingleGeneration(
                generation_id=generation_id,
                generation_parameters=generation_parameters,
                requires_post_processing=requires_post_processing,
                requires_safety_check=requires_safety_check,
                requires_submit=requires_submit,
                extra_logging=extra_logging,
                strict_transition_mode=strict_transition_mode,
            )
        else:
            raise ValueError(f"Unknown generation class: {generation_class}")

        return generation

    def create_generation_instance_for_permutation(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        generation_id_factory: Callable[[], str],
        include_submit: bool,
        permutation: GenerationPermutation,
        strict_transition_mode: bool = True,
    ) -> HordeSingleGeneration[Any]:
        generation: HordeSingleGeneration[Any] = self.create_generation_instance(
            generation_class,
            generation_id=generation_id_factory(),
            generation_parameters=permutation.underlying_payload,
            requires_generation=permutation.include_generation,
            requires_post_processing=permutation.include_post_processing,
            requires_safety_check=permutation.include_safety_check,
            requires_submit=include_submit,
            strict_transition_mode=strict_transition_mode,
            extra_logging=False,
        )

        return generation

    @pytest.mark.parametrize(
        "generation_class",
        [
            ImageSingleGeneration,
            AlchemySingleGeneration,
            TextSingleGeneration,
        ],
    )
    def test_error_handling(
        self,
        generation_class: type[ImageSingleGeneration | TextSingleGeneration | AlchemySingleGeneration],
        id_factory_str: Callable[[], str],
        image_permutations: list[GenerationPermutation],
        alchemy_permutations: list[GenerationPermutation],
        text_permutations: list[GenerationPermutation],
    ) -> None:
        """Test error handling for all permutations of generation configurations.

        This function is one of the heaviest in the test suite but does a lot of heavy
        lifting in terms of making sure all of the intended generation paths are covered.
        """

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

        permutations_map: dict[
            type[ImageSingleGeneration] | type[AlchemySingleGeneration] | type[TextSingleGeneration],
            list[GenerationPermutation],
        ]
        permutations_map = {
            ImageSingleGeneration: image_permutations,
            AlchemySingleGeneration: alchemy_permutations,
            TextSingleGeneration: text_permutations,
        }

        for generation_type, permutations in permutations_map.items():
            for permutation in permutations:
                self.run_generation_abort_and_error_tests(
                    generation_class=generation_type,
                    generation_id_factory=id_factory_str,
                    generation_parameters=permutation.underlying_payload,
                    include_generation=permutation.include_generation,
                    include_post_processing=permutation.include_post_processing,
                    include_safety_check=permutation.include_safety_check,
                    include_submit=permutation.include_submit,
                )

        for error_permutation in error_permutations:
            permutations_list = permutations_map.get(generation_class)
            if permutations_list is None:
                raise ValueError(f"Permutations not found for {generation_class.__name__}")
            try:
                self.run_generation_test_permutations(
                    generation_class,
                    id_factory_str,
                    permutations_list,
                    error_on_preloading=error_permutation.error_on_preloading,
                    error_on_generation=error_permutation.error_on_generation,
                    error_on_post_processing=error_permutation.error_on_post_processing,
                    error_on_safety_check=error_permutation.error_on_safety_check,
                    error_on_submit=error_permutation.error_on_submit,
                )
            except Exception as e:
                logger.exception(f"Error running permutations for {generation_class.__name__}")
                logger.exception(f"Error permutation: {error_permutation}")
                logger.exception(f"Generation permutations: {permutations_list}")

                raise e
