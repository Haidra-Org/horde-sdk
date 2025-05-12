from collections.abc import Mapping

from typing_extensions import override

from horde_sdk.consts import ID_TYPES
from horde_sdk.generation_parameters.alchemy import SingleAlchemyParameters
from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.generation_parameters.text import TextGenerationParameters
from horde_sdk.safety import SafetyRules, default_image_safety_rules, default_text_safety_rules
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    HordeWorkerConfigDefaults,
    base_generate_progress_no_submit_transitions,
    base_generate_progress_transitions,
    default_alchemy_generate_progress_no_submit_transitions,
    default_alchemy_generate_progress_transitions,
    default_image_generate_progress_no_submit_transitions,
    default_image_generate_progress_transitions,
    default_text_generate_progress_no_submit_transitions,
    default_text_generate_progress_transitions,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration


class ImageSingleGeneration(HordeSingleGeneration[bytes]):
    """A single image generation.

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_image_generate_progress_transitions

    @override
    @classmethod
    def default_generate_progress_transitions_no_submit(
        cls,
    ) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_image_generate_progress_no_submit_transitions

    @override
    @classmethod
    def does_class_require_generation(cls) -> bool:
        return True

    @override
    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        return True

    generation_parameters: ImageGenerationParameters

    def __init__(
        self,
        *,
        generation_parameters: ImageGenerationParameters,
        generation_id: ID_TYPES | None = None,
        result_ids: list[ID_TYPES] | None = None,
        requires_submit: bool = True,
        safety_rules: SafetyRules = default_image_safety_rules,
        black_box_mode: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        strict_transition_mode: bool = HordeWorkerConfigDefaults.DEFAULT_GENERATION_STRICT_TRANSITION_MODE,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_parameters (ImageGenerationParameters): The parameters for the generation.
            generation_id (str | None): The unique identifier for the generation. \
                If None, a random UUID will be generated.
            result_ids (list[ID_TYPES] | None): The unique identifiers for the generation. \
                If None, a random UUID will be generated for each result.
            requires_submit (bool, optional): Whether the generation requires submission. \
                Defaults to True.
            safety_rules (SafetyRules, optional): The safety rules to apply to the generation. \
                Defaults to default_image_safety_rules from `horde_sdk.safety`.
            black_box_mode (bool, optional): Whether the generation is in black box mode. \
                This removes all of the intermediate states between starting and finished states. \
                This should only be used when the backend has no observability into the generation process. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            strict_transition_mode (bool, optional): Whether or not to enforce strict transition checking. \
                This prevents setting the same state multiple times in a row. \
                Defaults to True.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        generate_progress_transitions = self.default_generate_progress_transitions()

        if not requires_submit:
            generate_progress_transitions = self.default_generate_progress_transitions_no_submit()

        super().__init__(
            result_type=bytes,
            generation_parameters=generation_parameters,
            generation_id=generation_id,
            result_ids=result_ids,
            requires_generation=ImageSingleGeneration.does_class_require_generation(),
            requires_post_processing=generation_parameters.alchemy_params is not None,
            requires_safety_check=True,
            requires_submit=requires_submit,
            safety_rules=safety_rules,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            black_box_mode=black_box_mode,
            strict_transition_mode=strict_transition_mode,
            extra_logging=extra_logging,
        )


class AlchemySingleGeneration(HordeSingleGeneration[bytes]):
    """A single alchemy generation. Alchemy is generally transformative or analytical in nature.

    'Generation' is used more broadly here than in the context of AI generation for the sake of naming consistency.

    Generally an input might be an image and the output could be anything, such as the input `image` upscaled with a \
    model, caption `text`, or whether the image is NSFW or not (`bool`).

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_alchemy_generate_progress_transitions

    @override
    @classmethod
    def default_generate_progress_transitions_no_submit(
        cls,
    ) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_alchemy_generate_progress_no_submit_transitions

    @override
    @classmethod
    def does_class_require_generation(cls) -> bool:
        return False

    @override
    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        return False

    generation_parameters: SingleAlchemyParameters
    """The parameters for the generation."""

    def __init__(
        self,
        *,
        generation_parameters: SingleAlchemyParameters,
        generation_id: str | None = None,
        result_ids: list[ID_TYPES] | None = None,
        requires_generation: bool = False,
        requires_post_processing: bool = True,
        requires_safety_check: bool = False,
        requires_submit: bool = True,
        safety_rules: SafetyRules = default_image_safety_rules,
        black_box_mode: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        strict_transition_mode: bool = HordeWorkerConfigDefaults.DEFAULT_GENERATION_STRICT_TRANSITION_MODE,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_parameters (SingleAlchemyParameters): The parameters for the generation.
            generation_id (str | None): The unique identifier for the generation. \
                If None, a random UUID will be generated.
            result_ids (list[ID_TYPES] | None): The unique identifiers for the generation. \
                If None, a random UUID will be generated for each result.
            requires_generation (bool, optional): Whether the generation requires generation. \
                Defaults to False.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to True.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
                Defaults to False.
            requires_submit (bool, optional): Whether the generation requires submission. \
                Defaults to True.
            safety_rules (SafetyRules, optional): The safety rules to apply to the generation. \
                Defaults to default_image_safety_rules from `horde_sdk.safety`.
            black_box_mode (bool, optional): Whether the generation is in black box mode. \
                This removes all of the intermediate states between starting and finished states. \
                This should only be used when the backend has no observability into the generation process. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            strict_transition_mode (bool, optional): Whether or not to enforce strict transition checking. \
                This prevents setting the same state multiple times in a row. \
                Defaults to True.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        generate_progress_transitions = self.default_generate_progress_transitions()

        if not requires_safety_check and not requires_submit:
            generate_progress_transitions = self.default_generate_progress_transitions_no_submit()
        elif requires_safety_check and not requires_submit:
            generate_progress_transitions = base_generate_progress_no_submit_transitions
        elif requires_safety_check and requires_submit:
            generate_progress_transitions = base_generate_progress_transitions

        super().__init__(
            generation_parameters=generation_parameters,
            result_type=bytes,
            generation_id=generation_id,
            result_ids=result_ids,
            requires_generation=requires_generation,
            requires_post_processing=requires_post_processing,
            requires_safety_check=requires_safety_check,
            requires_submit=requires_submit,
            safety_rules=safety_rules,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            black_box_mode=black_box_mode,
            strict_transition_mode=strict_transition_mode,
            extra_logging=extra_logging,
        )


class TextSingleGeneration(HordeSingleGeneration[str]):
    """A single text generation.

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_text_generate_progress_transitions

    @override
    @classmethod
    def default_generate_progress_transitions_no_submit(
        cls,
    ) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_text_generate_progress_no_submit_transitions

    @override
    @classmethod
    def does_class_require_generation(cls) -> bool:
        return True

    @override
    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        return False

    generation_parameters: TextGenerationParameters
    """The parameters for the generation."""

    def __init__(
        self,
        *,
        generation_parameters: TextGenerationParameters,
        generation_id: ID_TYPES | None = None,
        result_ids: list[ID_TYPES] | None = None,
        requires_generation: bool = True,
        requires_post_processing: bool = False,
        requires_safety_check: bool = False,
        requires_submit: bool = True,
        safety_rules: SafetyRules = default_text_safety_rules,
        black_box_mode: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        strict_transition_mode: bool = HordeWorkerConfigDefaults.DEFAULT_GENERATION_STRICT_TRANSITION_MODE,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_parameters (TextGenerationParameters): The parameters for the generation.
            generation_id (str | None): The unique identifier for the generation. \
                If None, a random UUID will be generated.
            result_ids (list[ID_TYPES] | None): The unique identifiers for the generation. \
                If None, a random UUID will be generated for each result.
            requires_generation (bool, optional): Whether the generation requires generation. \
                Defaults to True.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
                Defaults to False.
            requires_submit (bool, optional): Whether the generation requires submission. \
                Defaults to True.
            safety_rules (SafetyRules, optional): The safety rules to apply to the generation. \
                Defaults to default_text_safety_rules from `horde_sdk.safety`.
            black_box_mode (bool, optional): Whether the generation is in black box mode. \
                This removes all of the intermediate states between starting and finished states. \
                This should only be used when the backend has no observability into the generation process. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            strict_transition_mode (bool, optional): Whether or not to enforce strict transition checking. \
                This prevents setting the same state multiple times in a row. \
                Defaults to True.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        if requires_generation is False:
            raise ValueError("requires_generation must be True for TextSingleGeneration")

        generate_progress_transitions = self.default_generate_progress_transitions()

        if not requires_safety_check and not requires_submit:
            generate_progress_transitions = self.default_generate_progress_transitions_no_submit()
        if requires_safety_check and requires_submit:
            generate_progress_transitions = base_generate_progress_transitions
        elif requires_safety_check and not requires_submit:
            generate_progress_transitions = base_generate_progress_no_submit_transitions

        super().__init__(
            result_type=str,
            generation_parameters=generation_parameters,
            generation_id=generation_id,
            result_ids=result_ids,
            requires_generation=True,
            requires_post_processing=requires_post_processing,
            requires_safety_check=requires_safety_check,
            requires_submit=requires_submit,
            safety_rules=safety_rules,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            black_box_mode=black_box_mode,
            strict_transition_mode=strict_transition_mode,
            extra_logging=extra_logging,
        )
