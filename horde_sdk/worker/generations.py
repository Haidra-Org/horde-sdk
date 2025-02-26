from collections.abc import Mapping
from io import BytesIO

import PIL.Image
from typing_extensions import override

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters.alchemy import SingleAlchemyParameters
from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.generation_parameters.text import TextGenerationParameters
from horde_sdk.worker.consts import (
    GENERATION_PROGRESS,
    HordeWorkerConfigDefaults,
    base_generate_progress_transitions,
    default_alchemy_generate_progress_transitions,
    default_image_generate_progress_transitions,
    default_text_generate_progress_transitions,
)
from horde_sdk.worker.generations_base import HordeSingleGeneration


class ImageSingleGeneration(HordeSingleGeneration[PIL.Image.Image]):
    """A single image generation.

    **Not to be confused with a job**, which can contain multiple generations.
    """

    @override
    @classmethod
    def default_generate_progress_transitions(cls) -> dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]]:
        return default_image_generate_progress_transitions

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
        generation_id: GENERATION_ID_TYPES,
        generation_parameters: ImageGenerationParameters,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (str): The unique identifier for the generation.
            generation_parameters (ImageGenerationParameters): The parameters for the generation.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        self.generation_parameters = generation_parameters

        requires_post_processing = self.generation_parameters.alchemy_params is not None

        generate_progress_transitions = default_image_generate_progress_transitions

        super().__init__(
            generation_id=generation_id,
            result_type=PIL.Image.Image,
            requires_generation=ImageSingleGeneration.does_class_require_generation(),
            requires_post_processing=requires_post_processing,
            requires_safety_check=True,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
        )

    @override
    @staticmethod
    def result_to_bytesio(result: PIL.Image.Image, buffer: BytesIO) -> None:
        result.save(buffer, format="PNG")


class AlchemySingleGeneration(HordeSingleGeneration[PIL.Image.Image]):
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
    def does_class_require_generation(cls) -> bool:
        return False

    @override
    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        return False

    single_alchemy_parameters: SingleAlchemyParameters

    def __init__(
        self,
        *,
        generation_id: str,
        single_alchemy_parameters: SingleAlchemyParameters,
        requires_generation: bool = False,
        requires_post_processing: bool = True,
        requires_safety_check: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (str): The unique identifier for the generation.
            single_alchemy_parameters (SingleAlchemyParameters): The parameters for the generation.
            requires_generation (bool, optional): Whether the generation requires generation. \
                Defaults to False.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to True.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        self.single_alchemy_parameters = single_alchemy_parameters

        generate_progress_transitions = default_alchemy_generate_progress_transitions

        if requires_safety_check:
            generate_progress_transitions = base_generate_progress_transitions

        super().__init__(
            generation_id=generation_id,
            result_type=PIL.Image.Image,
            requires_generation=requires_generation,
            requires_post_processing=requires_post_processing,
            requires_safety_check=requires_safety_check,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
        )

    @override
    @staticmethod
    def result_to_bytesio(result: PIL.Image.Image, buffer: BytesIO) -> None:
        result.save(buffer, format="PNG")


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
    def does_class_require_generation(cls) -> bool:
        return True

    @override
    @classmethod
    def does_class_require_safety_check(cls) -> bool:
        return False

    def __init__(
        self,
        *,
        generation_id: GENERATION_ID_TYPES,
        generation_parameters: TextGenerationParameters,
        requires_post_processing: bool = False,
        requires_safety_check: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (str): The unique identifier for the generation.
            generation_parameters (TextGenerationParameters): The parameters for the generation.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
                Defaults to False.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        self.generation_parameters = generation_parameters

        generate_progress_transitions = default_text_generate_progress_transitions

        if requires_safety_check:
            generate_progress_transitions = base_generate_progress_transitions

        super().__init__(
            generation_id=generation_id,
            result_type=str,
            requires_generation=True,
            requires_post_processing=requires_post_processing,
            requires_safety_check=requires_safety_check,
            state_error_limits=state_error_limits,
            generate_progress_transitions=generate_progress_transitions,
            extra_logging=extra_logging,
        )

    @override
    @staticmethod
    def result_to_bytesio(result: str, buffer: BytesIO) -> None:
        """Convert the result to a BytesIO object, encoding the result as UTF-8."""
        buffer.write(result.encode())
