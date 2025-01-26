from collections.abc import Iterable, Mapping
from typing import Any

import PIL.Image
from typing_extensions import override

from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.ai_horde_worker.consts import (
    GENERATION_PROGRESS,
    HordeWorkerConfigDefaults,
    default_alchemy_generate_progress_transitions,
    default_image_generate_progress_transitions,
    default_text_generate_progress_transitions,
)
from horde_sdk.ai_horde_worker.generations_base import HordeSingleGeneration


class ImageSingleGeneration(HordeSingleGeneration[PIL.Image.Image]):
    """A single image generation.

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        return default_image_generate_progress_transitions

    @override
    @classmethod
    def does_class_requires_generation(cls) -> bool:
        return True

    def __init__(
        self,
        *,
        generation_id: GenerationID,
        requires_post_processing: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            list[GENERATION_PROGRESS],
        ] = default_image_generate_progress_transitions,
        extra_logging: bool = False,
        **kwargs: dict[Any, Any],
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (GenerationID): The unique identifier for the generation.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            generate_progress_transitions (dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]], optional): \
                Custom progress transitions for the generation. \
                Defaults to default_image_generate_progress_transitions.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
            **kwargs (dict[Any, Any]): Additional keyword arguments to pass to the superclass.
        """
        super().__init__(
            generation_id=generation_id,
            requires_generation=ImageSingleGeneration.does_class_requires_generation(),
            requires_post_processing=requires_post_processing,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
            **kwargs,
        )


class AlchemySingleGeneration(HordeSingleGeneration[PIL.Image.Image]):
    """A single alchemy generation. Alchemy is generally transformative or analytical in nature.

    'Generation' is used more broadly here than in the context of AI generation for the sake of naming consistency.

    Generally an input might be an image and the output could be anything, such as the input `image` upscaled with a \
    model, caption `text`, or whether the image is NSFW or not (`bool`).

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        return default_alchemy_generate_progress_transitions

    @override
    @classmethod
    def does_class_requires_generation(cls) -> bool:
        return False

    def __init__(
        self,
        *,
        generation_id: GenerationID,
        requires_generation: bool = False,
        requires_post_processing: bool = True,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            list[GENERATION_PROGRESS],
        ] = default_alchemy_generate_progress_transitions,
        extra_logging: bool = False,
        **kwargs: dict[Any, Any],
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (GenerationID): The unique identifier for the generation.
            requires_generation (bool, optional): Whether the generation requires generation. \
                Defaults to False.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to True.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            generate_progress_transitions (dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]], optional): \
                Custom progress transitions for the generation. \
                Defaults to default_image_generate_progress_transitions.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
            **kwargs (dict[Any, Any]): Additional keyword arguments to pass to the superclass.
        """
        super().__init__(
            generation_id=generation_id,
            requires_generation=requires_generation,
            requires_post_processing=requires_post_processing,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
            **kwargs,
        )


class TextSingleGeneration(HordeSingleGeneration[str]):
    """A single text generation.

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> Mapping[GENERATION_PROGRESS, Iterable[GENERATION_PROGRESS]]:
        return default_text_generate_progress_transitions

    @override
    @classmethod
    def does_class_requires_generation(cls) -> bool:
        return True

    def __init__(
        self,
        *,
        generation_id: GenerationID,
        requires_post_processing: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        generate_progress_transitions: Mapping[
            GENERATION_PROGRESS,
            list[GENERATION_PROGRESS],
        ] = default_text_generate_progress_transitions,
        extra_logging: bool = False,
        **kwargs: dict[Any, Any],
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (GenerationID): The unique identifier for the generation.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            generate_progress_transitions (dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]], optional): \
                Custom progress transitions for the generation. \
                Defaults to default_text_generate_progress_transitions.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
            **kwargs (dict[Any, Any]): Additional keyword arguments to pass to the superclass.
        """
        super().__init__(
            generation_id=generation_id,
            requires_generation=True,
            requires_post_processing=requires_post_processing,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
            **kwargs,
        )
