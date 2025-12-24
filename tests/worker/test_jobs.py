from uuid import uuid4

import pytest

from horde_sdk.generation_parameters import (
    AlchemyParameters,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_ALCHEMY_FORMS
from horde_sdk.generation_parameters.alchemy.object_models import (
    UpscaleAlchemyParametersTemplate,
)
from horde_sdk.generation_parameters.image.object_models import (
    BasicImageGenerationParametersTemplate,
    ImageGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.text.object_models import (
    BasicTextGenerationParametersTemplate,
    TextGenerationParametersTemplate,
)
from horde_sdk.generation_parameters.utils import ResultIdAllocator
from horde_sdk.worker.consts import GENERATION_PROGRESS, WORKER_ERRORS
from horde_sdk.worker.generations import AlchemySingleGeneration, ImageSingleGeneration, TextSingleGeneration
from horde_sdk.worker.jobs import AlchemyWorkerJob, ImageWorkerJob, TextWorkerJob


@pytest.fixture(scope="function")
def simple_image_worker_job(
    simple_image_generation: ImageSingleGeneration,
) -> ImageWorkerJob:
    return ImageWorkerJob(
        generation=simple_image_generation,
    )


def test_init_image_worker_job(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration


def test_init_worker_job_end_to_end_happy_path(
    simple_image_worker_job: ImageWorkerJob,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_image_worker_job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=True,
    )


def test_image_worker_job_lifecycle_preserves_dispatch_result_ids(
    simple_image_generation: ImageSingleGeneration,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    dispatch_ids = ("dispatch-image-1", uuid4())
    job = ImageWorkerJob(
        generation=simple_image_generation,
        dispatch_result_ids=dispatch_ids,
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=True,
    )

    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_image_worker_job_lifecycle_uses_dispatch_job_id(
    simple_image_generation: ImageSingleGeneration,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    job = ImageWorkerJob(
        generation=simple_image_generation,
        dispatch_job_id="dispatch-image-job",
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=True,
    )

    assert job.generation.dispatch_result_ids == ["dispatch-image-job"]


def test_image_job_abort_immediately(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration

    simple_image_worker_job.set_job_faulted(
        faulted_reason=WORKER_ERRORS.UNHANDLED_EXCEPTION,
        failure_exception=Exception("Test faulted exception"),
    )


def test_image_job_abort_during_generation(
    simple_image_worker_job: ImageWorkerJob,
) -> None:
    assert simple_image_worker_job is not None
    assert simple_image_worker_job.generation is not None
    assert simple_image_worker_job.generation_cls is ImageSingleGeneration

    generation = simple_image_worker_job.generation

    assert generation.on_generating() == GENERATION_PROGRESS.GENERATING

    assert generation.on_abort(
        failed_message=WORKER_ERRORS.UNHANDLED_EXCEPTION,
        failure_exception=Exception("Test faulted exception"),
    )


@pytest.fixture(scope="function")
def simple_alchemy_job(
    simple_alchemy_generation_parameters: AlchemyParameters,
) -> AlchemyWorkerJob:
    assert len(simple_alchemy_generation_parameters.all_alchemy_operations) == 1
    alchemy_single_generation_parameters = simple_alchemy_generation_parameters.all_alchemy_operations[0]
    return AlchemyWorkerJob(
        generation=AlchemySingleGeneration(
            generation_parameters=alchemy_single_generation_parameters,
        ),
    )


def test_init_alchemy_job(
    simple_alchemy_job: AlchemyWorkerJob,
) -> None:
    assert simple_alchemy_job is not None
    assert simple_alchemy_job.generation is not None
    assert simple_alchemy_job.generation_cls is AlchemySingleGeneration


def test_init_alchemy_worker_job_end_to_end_happy_path(
    simple_alchemy_job: AlchemyWorkerJob,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_alchemy_job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=False,
        include_post_processing=True,
        include_safety_check=False,
    )


def test_alchemy_worker_job_lifecycle_preserves_dispatch_result_ids(
    simple_alchemy_generation: AlchemySingleGeneration,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    dispatch_ids = ("dispatch-alchemy-1", uuid4())
    job = AlchemyWorkerJob(
        generation=simple_alchemy_generation,
        dispatch_result_ids=dispatch_ids,
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=False,
        include_post_processing=True,
        include_safety_check=False,
    )

    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_alchemy_worker_job_lifecycle_uses_dispatch_job_id(
    simple_alchemy_generation: AlchemySingleGeneration,
    default_testing_image_bytes: bytes,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    job = AlchemyWorkerJob(
        generation=simple_alchemy_generation,
        dispatch_job_id="dispatch-alchemy-job",
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result=default_testing_image_bytes,
        include_preloading=True,
        include_generation=False,
        include_post_processing=True,
        include_safety_check=False,
    )

    assert job.generation.dispatch_result_ids == ["dispatch-alchemy-job"]


@pytest.fixture(scope="function")
def simple_text_job(
    simple_text_generation: TextSingleGeneration,
) -> TextWorkerJob:
    return TextWorkerJob(
        generation=simple_text_generation,
    )


def test_init_text_job(
    simple_text_job: TextWorkerJob,
) -> None:
    assert simple_text_job is not None
    assert simple_text_job.generation_cls is TextSingleGeneration


def test_init_text_worker_job_end_to_end_happy_path(
    simple_text_job: TextWorkerJob,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=simple_text_job.generation,
        result="Dummy result",
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=False,
    )


def test_text_worker_job_lifecycle_preserves_dispatch_result_ids(
    simple_text_generation: TextSingleGeneration,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    dispatch_ids = ("dispatch-text-1", uuid4())
    job = TextWorkerJob(
        generation=simple_text_generation,
        dispatch_result_ids=dispatch_ids,
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result="Dummy result",
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=False,
    )

    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_text_worker_job_lifecycle_uses_dispatch_job_id(
    simple_text_generation: TextSingleGeneration,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    job = TextWorkerJob(
        generation=simple_text_generation,
        dispatch_job_id="dispatch-text-job",
    )

    TestHordeSingleGeneration()

    TestHordeSingleGeneration.run_generation_process(
        generation=job.generation,
        result="Dummy result",
        include_preloading=True,
        include_generation=True,
        include_post_processing=False,
        include_safety_check=False,
    )

    assert job.generation.dispatch_result_ids == ["dispatch-text-job"]


def test_image_worker_job_from_template_overrides_prompt() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="placeholder")
    )
    job = ImageWorkerJob.from_template(
        template,
        base_param_updates=BasicImageGenerationParametersTemplate(prompt="generated", model="image-model"),
        result_ids=("image-result",),
    )

    assert job.generation.generation_parameters.base_params.prompt == "generated"
    assert job.generation.generation_parameters.base_params.model == "image-model"
    assert job.generation.generation_parameters.result_ids == ["image-result"]


def test_text_worker_job_from_template_updates_prompt() -> None:
    template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="base",
            model="text-model",
        ),
    )
    job = TextWorkerJob.from_template(
        template,
        base_param_updates=BasicTextGenerationParametersTemplate(prompt="final"),
    )

    assert job.generation.generation_parameters.base_params.prompt == "final"
    assert job.generation.generation_parameters.result_ids is not None


def test_text_worker_job_from_template_accepts_explicit_result_ids() -> None:
    template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="seed",
            model="text-model",
        ),
    )

    job = TextWorkerJob.from_template(
        template,
        base_param_updates=BasicTextGenerationParametersTemplate(prompt="updated"),
        result_ids=("text-template",),
    )

    result_ids = job.generation.generation_parameters.result_ids
    assert result_ids == ["text-template"]
    result_ids.append("mutated")
    assert job.generation.generation_parameters.result_ids == result_ids


def test_text_worker_job_from_template_uses_allocator() -> None:
    template = TextGenerationParametersTemplate(
        base_params=BasicTextGenerationParametersTemplate(
            prompt="allocator",
            model="text-model",
        ),
    )
    allocator = ResultIdAllocator()

    first_job = TextWorkerJob.from_template(template, allocator=allocator, seed="text-seed")
    second_job = TextWorkerJob.from_template(template, allocator=allocator, seed="text-seed")

    assert (
        first_job.generation.generation_parameters.result_ids == second_job.generation.generation_parameters.result_ids
    )


def test_alchemy_worker_job_from_template_sets_source_image() -> None:
    template = UpscaleAlchemyParametersTemplate()
    job = AlchemyWorkerJob.from_template(
        template,
        source_image=b"image-bytes",
        default_form=KNOWN_ALCHEMY_FORMS.post_process,
    )

    assert job.generation.generation_parameters.source_image == b"image-bytes"
    assert job.generation.generation_parameters.form == KNOWN_ALCHEMY_FORMS.post_process


def test_alchemy_worker_job_from_template_allocates_result_id_with_allocator() -> None:
    template = UpscaleAlchemyParametersTemplate()
    allocator = ResultIdAllocator()

    first_job = AlchemyWorkerJob.from_template(
        template,
        source_image=b"seed-image",
        allocator=allocator,
        seed="alchemy-seed",
    )
    second_job = AlchemyWorkerJob.from_template(
        template,
        source_image=b"seed-image",
        allocator=allocator,
        seed="alchemy-seed",
    )

    first_id = first_job.generation.generation_parameters.result_id
    assert first_id
    assert first_job.generation.result_ids == [first_id]
    assert first_id == second_job.generation.generation_parameters.result_id


def test_worker_job_from_template_preserves_generation_identifier_when_requested() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="placeholder")
    )
    job = ImageWorkerJob.from_template(
        template,
        generation_id="generation-id",
        job_id="job-id",
        preserve_generation_id=True,
        base_param_updates=BasicImageGenerationParametersTemplate(prompt="generated", model="image-model"),
    )

    assert job.job_id == "job-id"
    assert job.generation.generation_id == "generation-id"


def test_worker_job_from_template_binds_generation_identifier_by_default() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="placeholder", model="image-model")
    )
    job = ImageWorkerJob.from_template(
        template,
        job_id="job-id",
    )

    assert job.job_id == "job-id"
    assert job.generation.generation_id == "job-id"


def test_worker_job_propagates_dispatch_result_ids(
    simple_image_generation: ImageSingleGeneration,
) -> None:
    dispatch_ids = ("result-1", uuid4())

    job = ImageWorkerJob(
        generation=simple_image_generation,
        dispatch_result_ids=dispatch_ids,
    )

    # Generation receives the dispatch result identifiers and exposes copies on access.
    assert job.generation.dispatch_result_ids == list(dispatch_ids)

    observed_ids = job.generation.dispatch_result_ids
    assert observed_ids is not None
    observed_ids.append("mutated")

    # Mutating the returned collection should not affect the internal dispatch bindings.
    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_worker_job_defaults_dispatch_result_ids_to_dispatch_job_id(
    simple_image_generation: ImageSingleGeneration,
) -> None:
    job = ImageWorkerJob(
        generation=simple_image_generation,
        dispatch_job_id="remote-job",
    )

    assert job.generation.dispatch_result_ids == ["remote-job"]


def test_text_worker_job_dispatch_result_ids(
    simple_text_generation: TextSingleGeneration,
) -> None:
    dispatch_ids = (uuid4(), "result-2")

    job = TextWorkerJob(
        generation=simple_text_generation,
        dispatch_result_ids=dispatch_ids,
    )

    assert job.generation.dispatch_result_ids == list(dispatch_ids)

    observed_ids = job.generation.dispatch_result_ids
    assert observed_ids is not None
    observed_ids.append("mutated")

    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_text_worker_job_defaults_dispatch_result_ids_to_dispatch_job_id(
    simple_text_generation: TextSingleGeneration,
) -> None:
    job = TextWorkerJob(
        generation=simple_text_generation,
        dispatch_job_id="remote-text-job",
    )

    assert job.generation.dispatch_result_ids == ["remote-text-job"]


def test_image_worker_job_from_template_uses_allocator_for_result_ids() -> None:
    template = ImageGenerationParametersTemplate(
        base_params=BasicImageGenerationParametersTemplate(prompt="allocator prompt", model="image-model")
    )
    template.batch_size = 2
    allocator = ResultIdAllocator()

    first_job = ImageWorkerJob.from_template(template, allocator=allocator, seed="image-seed")
    second_job = ImageWorkerJob.from_template(template, allocator=allocator, seed="image-seed")

    first_ids = first_job.generation.generation_parameters.result_ids
    assert len(first_ids) == 2
    assert first_ids == first_job.generation.result_ids
    assert first_ids == second_job.generation.generation_parameters.result_ids


def test_worker_job_preserves_existing_dispatch_result_ids(
    simple_image_generation: ImageSingleGeneration,
) -> None:
    existing = ["pre-announced"]
    simple_image_generation.set_dispatch_result_ids(existing)

    job = ImageWorkerJob(
        generation=simple_image_generation,
        dispatch_job_id="remote-job",
    )

    assert job.generation.dispatch_result_ids == existing


def test_alchemy_worker_job_dispatch_result_ids(
    simple_alchemy_generation: AlchemySingleGeneration,
) -> None:
    dispatch_ids = ("result-1", uuid4())

    job = AlchemyWorkerJob(
        generation=simple_alchemy_generation,
        dispatch_result_ids=dispatch_ids,
    )

    assert job.generation.dispatch_result_ids == list(dispatch_ids)

    observed_ids = job.generation.dispatch_result_ids
    assert observed_ids is not None
    observed_ids.append("mutated")

    assert job.generation.dispatch_result_ids == list(dispatch_ids)


def test_alchemy_worker_job_defaults_dispatch_result_ids_to_dispatch_job_id(
    simple_alchemy_generation: AlchemySingleGeneration,
) -> None:
    job = AlchemyWorkerJob(
        generation=simple_alchemy_generation,
        dispatch_job_id="remote-alchemy-job",
    )

    assert job.generation.dispatch_result_ids == ["remote-alchemy-job"]
