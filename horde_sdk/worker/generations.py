from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TypedDict, override

from loguru import logger

from horde_sdk.consts import ID_TYPES
from horde_sdk.generation_parameters import BasicImageGenerationParametersTemplate
from horde_sdk.generation_parameters.alchemy import SingleAlchemyParameters
from horde_sdk.generation_parameters.alchemy.object_models import SingleAlchemyParametersTemplate
from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.generation_parameters.image.object_models import (
    ImageGenerationComponentContainer,
    ImageGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.text import TextGenerationParameters
from horde_sdk.generation_parameters.text.object_models import (
    BasicTextGenerationParametersTemplate,
    TextGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.utils import ResultIdAllocator
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


class ImageGenerationInitKwargs(TypedDict, total=False):
    """Optional keyword arguments accepted by `ImageSingleGeneration` from template helpers."""

    generation_id: ID_TYPES | None
    dispatch_result_ids: Sequence[ID_TYPES] | None
    result_ids: list[ID_TYPES] | None
    requires_submit: bool
    safety_rules: SafetyRules
    black_box_mode: bool
    state_error_limits: Mapping[GENERATION_PROGRESS, int] | None
    strict_transition_mode: bool
    extra_logging: bool


class AlchemyGenerationInitKwargs(TypedDict, total=False):
    """Optional keyword arguments accepted by `AlchemySingleGeneration` factory flows."""

    generation_id: str | None
    dispatch_result_ids: Sequence[ID_TYPES] | None
    result_ids: list[ID_TYPES] | None
    requires_generation: bool
    requires_post_processing: bool
    requires_safety_check: bool
    requires_submit: bool
    safety_rules: SafetyRules
    black_box_mode: bool
    state_error_limits: Mapping[GENERATION_PROGRESS, int] | None
    strict_transition_mode: bool
    extra_logging: bool


class TextGenerationInitKwargs(TypedDict, total=False):
    """Optional keyword arguments accepted by `TextSingleGeneration` helpers."""

    generation_id: ID_TYPES | None
    dispatch_result_ids: Sequence[ID_TYPES] | None
    result_ids: list[ID_TYPES] | None
    requires_post_processing: bool
    requires_safety_check: bool
    requires_submit: bool
    safety_rules: SafetyRules
    black_box_mode: bool
    state_error_limits: Mapping[GENERATION_PROGRESS, int] | None
    strict_transition_mode: bool
    extra_logging: bool


def _stringify_id(identifier: ID_TYPES | None) -> str | None:
    if identifier is None:
        return None
    return str(identifier)


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
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
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
            dispatch_result_ids (Sequence[str | uuid.UUID] | None): Result identifiers assigned by dispatch, if
                available.
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

        if result_ids is None and generation_parameters.result_ids is not None:
            result_ids = generation_parameters.result_ids
            logger.trace(
                f"Result IDs were not provided, using result IDs from generation parameters: {result_ids}",
                extra={"generation_id": generation_id},
            )
        elif result_ids is not None and generation_parameters.result_ids is not None:
            logger.warning(
                "Both result IDs and generation parameters result IDs were provided. Using the provided result IDs.",
                extra={"generation_id": generation_id},
            )

        super().__init__(
            result_type=bytes,
            generation_parameters=generation_parameters,
            generation_id=generation_id,
            dispatch_result_ids=dispatch_result_ids,
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

    @classmethod
    def from_template(
        cls,
        template: ImageGenerationParametersTemplate,
        *,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        base_param_updates: BasicImageGenerationParametersTemplate | None = None,
        additional_param_updates: ImageGenerationComponentContainer | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "image",
        init_kwargs: ImageGenerationInitKwargs | None = None,
    ) -> ImageSingleGeneration:
        """Instantiate an image generation from a template."""
        generation_parameters = template.to_parameters(
            base_param_updates=base_param_updates,
            result_ids=result_ids,
            allocator=allocator,
            seed=seed,
        )
        resolved_kwargs: ImageGenerationInitKwargs = {}
        if init_kwargs:
            resolved_kwargs.update(init_kwargs)
        if generation_id is not None:
            resolved_kwargs.setdefault("generation_id", generation_id)
        if dispatch_result_ids is not None:
            resolved_kwargs.setdefault("dispatch_result_ids", list(dispatch_result_ids))
        resolved_kwargs.setdefault("result_ids", generation_parameters.result_ids)
        return cls(
            generation_parameters=generation_parameters,
            **resolved_kwargs,
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
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
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
            dispatch_result_ids (Sequence[str | uuid.UUID] | None): Result identifiers assigned by dispatch, if
                available.
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
            dispatch_result_ids=dispatch_result_ids,
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

    @classmethod
    def from_template(
        cls,
        template: SingleAlchemyParametersTemplate,
        *,
        source_image: bytes | str | None = None,
        default_form: str | None = None,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        result_id: ID_TYPES | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "alchemy",
        init_kwargs: AlchemyGenerationInitKwargs | None = None,
    ) -> AlchemySingleGeneration:
        """Instantiate an alchemy generation from a template."""
        generation_parameters = template.to_parameters(
            result_id=result_id,
            source_image=source_image,
            default_form=default_form,
            allocator=allocator,
            seed=seed,
        )
        resolved_kwargs: AlchemyGenerationInitKwargs = {}
        if init_kwargs:
            resolved_kwargs.update(init_kwargs)
        if generation_id is not None:
            resolved_kwargs.setdefault("generation_id", _stringify_id(generation_id))
        else:
            resolved_kwargs.setdefault("generation_id", _stringify_id(generation_parameters.result_id))
        if dispatch_result_ids is not None:
            resolved_kwargs.setdefault(
                "dispatch_result_ids",
                [str(identifier) for identifier in dispatch_result_ids],
            )
        resolved_kwargs.setdefault("result_ids", [generation_parameters.result_id])
        return cls(
            generation_parameters=generation_parameters,
            **resolved_kwargs,
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
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
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
            dispatch_result_ids (Sequence[str | uuid.UUID] | None): Result identifiers assigned by dispatch, if
                available.
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
            dispatch_result_ids=dispatch_result_ids,
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

    @classmethod
    def from_template(
        cls,
        template: TextGenerationParametersTemplate,
        *,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        base_param_updates: BasicTextGenerationParametersTemplate | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "text",
        init_kwargs: TextGenerationInitKwargs | None = None,
    ) -> TextSingleGeneration:
        """Instantiate a text generation from a template."""
        generation_parameters = template.to_parameters(
            base_param_updates=base_param_updates,
            result_ids=result_ids,
            allocator=allocator,
            seed=seed,
        )
        resolved_kwargs: TextGenerationInitKwargs = {}
        if init_kwargs:
            resolved_kwargs.update(init_kwargs)
        if generation_id is not None:
            resolved_kwargs.setdefault("generation_id", generation_id)
        if dispatch_result_ids is not None:
            resolved_kwargs.setdefault("dispatch_result_ids", list(dispatch_result_ids))
        resolved_kwargs.setdefault("result_ids", generation_parameters.result_ids)
        return cls(
            generation_parameters=generation_parameters,
            **resolved_kwargs,
        )
