from collections.abc import Iterable, Mapping
from io import BytesIO
from typing import Any

import PIL.Image
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels import (
    AlchemyPopFormPayload,
    ImageGenerateJobPopResponse,
    TextGenerateJobPopResponse,
)
from horde_sdk.ai_horde_api.fields import GenerationID
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

    api_response: ImageGenerateJobPopResponse

    def __init__(
        self,
        *,
        generation_id: GenerationID,
        api_response: ImageGenerateJobPopResponse,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (GenerationID): The unique identifier for the generation.
            api_response (ImageGenerateJobPopResponse): The API response for the generation.
            state_error_limits (Mapping[GENERATION_PROGRESS, int], optional): The maximum number of times a \
                generation can be in an error state before it is considered failed. \
                Defaults to HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS.
            generate_progress_transitions (dict[GENERATION_PROGRESS, list[GENERATION_PROGRESS]], optional): \
                Custom progress transitions for the generation. \
                Defaults to default_image_generate_progress_transitions.
            extra_logging (bool, optional): Whether or not to enable extra debug-level logging, \
                especially for state transitions. \
                Defaults to True.
        """
        self.api_response = api_response

        requires_post_processing = bool(api_response.payload.post_processing)

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

    form_payload: AlchemyPopFormPayload

    def __init__(
        self,
        *,
        generation_id: GenerationID,
        form: AlchemyPopFormPayload,
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
            generation_id (GenerationID): The unique identifier for the generation.
            requires_generation (bool, optional): Whether the generation requires generation. \
                Defaults to False.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to True.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
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
        """
        self.form_payload = form

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
        generation_id: GenerationID,
        api_response: TextGenerateJobPopResponse,
        requires_post_processing: bool = False,
        requires_safety_check: bool = False,
        state_error_limits: (
            Mapping[GENERATION_PROGRESS, int] | None
        ) = HordeWorkerConfigDefaults.DEFAULT_STATE_ERROR_LIMITS,
        extra_logging: bool = False,
    ) -> None:
        """Initialize the generation.

        Args:
            generation_id (GenerationID): The unique identifier for the generation.
            api_response (TextGenerateJobPopResponse): The API response for the generation.
            requires_post_processing (bool, optional): Whether the generation requires post-processing. \
                Defaults to False.
            requires_safety_check (bool, optional): Whether the generation requires a safety check. \
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
        """
        self.api_response = api_response

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
