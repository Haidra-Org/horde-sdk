from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import override

from horde_sdk.consts import ID_TYPES, WORKER_TYPE, HTTPMethod
from horde_sdk.generation_parameters import (
    ImageGenerationParameters,
    SingleAlchemyParameters,
    TextGenerationParameters,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.alchemy.object_models import SingleAlchemyParametersTemplate
from horde_sdk.generation_parameters.image.object_models import ImageGenerationParametersTemplate
from horde_sdk.generation_parameters.text.object_models import TextGenerationParametersTemplate
from horde_sdk.generation_parameters.utils import ResultIdAllocator
from horde_sdk.worker.generations import (
    AlchemyGenerationInitKwargs,
    AlchemySingleGeneration,
    ImageGenerationInitKwargs,
    ImageSingleGeneration,
    TextGenerationInitKwargs,
    TextSingleGeneration,
    _stringify_id,
)
from horde_sdk.worker.job_base import (
    HordeWorkerJob,
    HordeWorkerJobConfig,
)

DEFAULT_UPLOAD_METHOD = HTTPMethod.PUT


class ImageWorkerJob(HordeWorkerJob[ImageSingleGeneration, ImageGenerationParameters]):
    """A job containing only image generations."""

    def __init__(
        self,
        *,
        generation: ImageSingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        preserve_generation_id: bool = False,
    ) -> None:
        """Initialize the image worker job.

        Args:
            generation (ImageSingleGeneration): The generation to use for the job.
            job_config (HordeWorkerJobConfig | None): The configuration for the job.
            job_config (HordeWorkerJobConfig, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            job_id (ID_TYPES | None): Optional identifier to associate with the job.
            dispatch_job_id (ID_TYPES | None): Identifier supplied by dispatch for the job.
            dispatch_result_ids (Sequence[ID_TYPES] | None): Result identifiers supplied by dispatch for the
                generation.
            preserve_generation_id (bool): Retain the existing generation identifier instead of overwriting it with the
                job identifier.
        """
        super().__init__(
            generation=generation,
            generation_cls=ImageSingleGeneration,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.image

    @classmethod
    def from_template(
        cls,
        template: ImageGenerationParametersTemplate,
        *,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        base_param_updates: Mapping[str, object] | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "image",
        generation_kwargs: ImageGenerationInitKwargs | None = None,
        job_config: HordeWorkerJobConfig | None = None,
        preserve_generation_id: bool = False,
    ) -> ImageWorkerJob:
        """Instantiate an image job from a template."""
        generation_parameters = template.to_parameters(
            base_param_updates=base_param_updates,
            result_ids=result_ids,
            allocator=allocator,
            seed=seed,
        )
        init_kwargs: ImageGenerationInitKwargs = {}
        if generation_kwargs:
            init_kwargs.update(generation_kwargs)
        if generation_id is not None:
            init_kwargs.setdefault("generation_id", generation_id)
        if dispatch_result_ids is not None:
            init_kwargs.setdefault("dispatch_result_ids", list(dispatch_result_ids))
        init_kwargs.setdefault("result_ids", generation_parameters.result_ids)
        generation = ImageSingleGeneration(
            generation_parameters=generation_parameters,
            **init_kwargs,
        )
        return cls(
            generation=generation,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )


class AlchemyWorkerJob(HordeWorkerJob[AlchemySingleGeneration, SingleAlchemyParameters]):
    """A job containing only alchemy generations."""

    def __init__(
        self,
        *,
        generation: AlchemySingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        preserve_generation_id: bool = False,
    ) -> None:
        """Initialize the alchemy worker job.

        Args:
            generation (AlchemySingleGeneration): The response from the API.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            job_id (ID_TYPES | None): Optional identifier to associate with the job.
            dispatch_job_id (ID_TYPES | None): Identifier supplied by dispatch for the job.
            dispatch_result_ids (Sequence[ID_TYPES] | None): Result identifiers supplied by dispatch for the
                generation.
            preserve_generation_id (bool): Retain the existing generation identifier instead of overwriting it with the
                job identifier.
        """
        super().__init__(
            generation=generation,
            generation_cls=AlchemySingleGeneration,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.alchemist

    @classmethod
    def from_template(
        cls,
        template: SingleAlchemyParametersTemplate,
        *,
        source_image: bytes | str | None = None,
        default_form: KNOWN_ALCHEMY_FORMS | str | None = KNOWN_ALCHEMY_FORMS.post_process,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        result_id: ID_TYPES | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "alchemy",
        generation_kwargs: AlchemyGenerationInitKwargs | None = None,
        job_config: HordeWorkerJobConfig | None = None,
        preserve_generation_id: bool = False,
    ) -> AlchemyWorkerJob:
        """Instantiate an alchemy job from a template."""
        generation_parameters = template.to_parameters(
            result_id=result_id,
            source_image=source_image,
            default_form=default_form,
            allocator=allocator,
            seed=seed,
        )
        init_kwargs: AlchemyGenerationInitKwargs = {}
        if generation_kwargs:
            init_kwargs.update(generation_kwargs)
        if generation_id is not None:
            init_kwargs.setdefault("generation_id", _stringify_id(generation_id))
        if dispatch_result_ids is not None:
            init_kwargs.setdefault(
                "dispatch_result_ids",
                [
                    stringified
                    for identifier in dispatch_result_ids
                    if (stringified := _stringify_id(identifier)) is not None
                ],
            )
        init_kwargs.setdefault("result_ids", [generation_parameters.result_id])
        generation = AlchemySingleGeneration(
            generation_parameters=generation_parameters,
            **init_kwargs,
        )
        return cls(
            generation=generation,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )


class TextWorkerJob(HordeWorkerJob[TextSingleGeneration, TextGenerationParameters]):
    """A job containing only text generations."""

    def __init__(
        self,
        generation: TextSingleGeneration,
        job_config: HordeWorkerJobConfig | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        preserve_generation_id: bool = False,
    ) -> None:
        """Initialize the text worker job.

        Args:
            generation (TextSingleGeneration): The response from the API.
            job_config (HordeWorkerJobConfig | None, optional): The configuration for the job. If `None`, the default \
                configuration will be used. Defaults to None.
            job_id (ID_TYPES | None): Optional identifier to associate with the job.
            dispatch_job_id (ID_TYPES | None): Identifier supplied by dispatch for the job.
            dispatch_result_ids (Sequence[ID_TYPES] | None): Result identifiers supplied by dispatch for the
                generation.
            preserve_generation_id (bool): Retain the existing generation identifier instead of overwriting it with the
                job identifier.
        """
        super().__init__(
            generation=generation,
            generation_cls=TextSingleGeneration,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )

    @override
    @classmethod
    def job_worker_type(cls) -> WORKER_TYPE:
        return WORKER_TYPE.text

    @classmethod
    def from_template(
        cls,
        template: TextGenerationParametersTemplate,
        *,
        generation_id: ID_TYPES | None = None,
        dispatch_result_ids: Sequence[ID_TYPES] | None = None,
        job_id: ID_TYPES | None = None,
        dispatch_job_id: ID_TYPES | None = None,
        base_param_updates: Mapping[str, object] | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "text",
        generation_kwargs: TextGenerationInitKwargs | None = None,
        job_config: HordeWorkerJobConfig | None = None,
        preserve_generation_id: bool = False,
    ) -> TextWorkerJob:
        """Instantiate a text job from a template."""
        generation_parameters = template.to_parameters(
            base_param_updates=base_param_updates,
            result_ids=result_ids,
            allocator=allocator,
            seed=seed,
        )
        init_kwargs: TextGenerationInitKwargs = {}
        if generation_kwargs:
            init_kwargs.update(generation_kwargs)
        if generation_id is not None:
            init_kwargs.setdefault("generation_id", generation_id)
        if dispatch_result_ids is not None:
            init_kwargs.setdefault("dispatch_result_ids", list(dispatch_result_ids))
        init_kwargs.setdefault("result_ids", generation_parameters.result_ids)
        generation = TextSingleGeneration(
            generation_parameters=generation_parameters,
            **init_kwargs,
        )
        return cls(
            generation=generation,
            job_config=job_config,
            job_id=job_id,
            dispatch_job_id=dispatch_job_id,
            dispatch_result_ids=dispatch_result_ids,
            preserve_generation_id=preserve_generation_id,
        )
