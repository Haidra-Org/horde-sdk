import PIL.Image

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters import AlchemyParameters, ImageGenerationParameters, TextGenerationParameters
from horde_sdk.worker.generations import AlchemySingleGeneration, ImageSingleGeneration, TextSingleGeneration
from horde_sdk.worker.job_base import (
    ComposedParameterSetTypeVar,
    HordeWorkerJob,
    HordeWorkerJobConfig,
    SingleGenerationTypeVar,
)
from horde_sdk.worker.jobs import AlchemyWorkerJob, ImageWorkerJob, TextWorkerJob


def _init_worker_job_checks(
    generation_parameters: ComposedParameterSetTypeVar,
    image_worker_job: HordeWorkerJob[SingleGenerationTypeVar, ComposedParameterSetTypeVar],
    generation_type: type[SingleGenerationTypeVar],
) -> None:

    assert image_worker_job is not None
    assert image_worker_job.generation_parameters is not None
    assert image_worker_job.generations is not None

    # assert len(image_worker_job.generations) == len(generation_parameters.ids

    # assert all(isinstance(gen_id, GenerationID) for gen_id in image_worker_job.generations)
    assert all(isinstance(gen, generation_type) for gen in image_worker_job.generations.values())


def test_init_image_worker_job(
    simple_image_generation_parameters_and_upload_map: tuple[
        ImageGenerationParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
) -> None:
    generation_parameters, upload_map = simple_image_generation_parameters_and_upload_map

    job_config = HordeWorkerJobConfig()
    image_worker_job = ImageWorkerJob(
        generation_parameters=generation_parameters,
        upload_map=upload_map,
        job_config=job_config,
    )
    _init_worker_job_checks(
        generation_parameters=generation_parameters,
        image_worker_job=image_worker_job,
        generation_type=ImageSingleGeneration,
    )

    assert len(image_worker_job._upload_map) == len(generation_parameters.generation_ids) == len(upload_map)


def test_init_image_worker_job_n_requests(
    simple_image_generation_parameters_n_iter_and_upload_map: tuple[
        ImageGenerationParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
) -> None:

    generation_parameters, upload_map = simple_image_generation_parameters_n_iter_and_upload_map

    job_config = HordeWorkerJobConfig()
    image_worker_job = ImageWorkerJob(
        generation_parameters=generation_parameters,
        upload_map=upload_map,
        job_config=job_config,
    )
    _init_worker_job_checks(
        generation_parameters=generation_parameters,
        image_worker_job=image_worker_job,
        generation_type=ImageSingleGeneration,
    )

    assert len(image_worker_job._upload_map) == len(generation_parameters.generation_ids) == len(upload_map)


def test_init_image_worker_job_end_to_end_happy_path(
    simple_image_generation_parameters_and_upload_map: tuple[
        ImageGenerationParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
    default_testing_image_PIL: PIL.Image.Image,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    generation_parameters, upload_map = simple_image_generation_parameters_and_upload_map

    image_worker_job = ImageWorkerJob(
        generation_parameters=generation_parameters,
        upload_map=upload_map,
    )

    for generation_id, generation in image_worker_job.generations.items():
        assert generation_id in generation_parameters.generation_ids

        TestHordeSingleGeneration.run_generation_process(
            generation=generation,
            result=default_testing_image_PIL,
            include_preloading=True,
            include_generation=True,
            include_post_processing=False,
            include_safety_check=True,
        )


def test_init_alchemy_worker_job(
    simple_alchemy_generation_parameters_and_upload_map: tuple[
        AlchemyParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
) -> None:
    generation_parameters, upload_map = simple_alchemy_generation_parameters_and_upload_map

    job_config = HordeWorkerJobConfig()
    alchemy_worker_job = AlchemyWorkerJob(
        generation_parameters=generation_parameters,
        upload_map=upload_map,
        job_config=job_config,
    )
    _init_worker_job_checks(
        generation_parameters=generation_parameters,
        image_worker_job=alchemy_worker_job,
        generation_type=AlchemySingleGeneration,
    )

    assert len(alchemy_worker_job._upload_map) == len(upload_map)


def test_init_alchemy_worker_job_end_to_end_happy_path(
    simple_alchemy_generation_parameters_and_upload_map: tuple[
        AlchemyParameters,
        dict[GENERATION_ID_TYPES, str | None],
    ],
    default_testing_image_PIL: PIL.Image.Image,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    generation_parameters, upload_map = simple_alchemy_generation_parameters_and_upload_map

    alchemy_worker_job = AlchemyWorkerJob(
        generation_parameters=generation_parameters,
        upload_map=upload_map,
    )

    for generation_id, generation in alchemy_worker_job.generations.items():
        assert generation_id in upload_map

        TestHordeSingleGeneration.run_generation_process(
            generation=generation,
            result=default_testing_image_PIL,
            include_preloading=True,
            include_generation=False,
            include_post_processing=True,
            include_safety_check=False,
        )


def test_init_text_worker_job(
    simple_text_generation_parameters: TextGenerationParameters,
) -> None:
    job_config = HordeWorkerJobConfig()
    text_worker_job = TextWorkerJob(
        generation_parameters=simple_text_generation_parameters,
        job_config=job_config,
    )
    _init_worker_job_checks(
        generation_parameters=simple_text_generation_parameters,
        image_worker_job=text_worker_job,
        generation_type=TextSingleGeneration,
    )


def test_init_text_worker_job_end_to_end_happy_path(
    simple_text_generation_parameters: TextGenerationParameters,
) -> None:
    from .test_horde_single_generations import TestHordeSingleGeneration

    TestHordeSingleGeneration()

    text_worker_job = TextWorkerJob(generation_parameters=simple_text_generation_parameters)

    for generation_id, generation in text_worker_job.generations.items():
        assert generation_id in simple_text_generation_parameters.generation_ids

        TestHordeSingleGeneration.run_generation_process(
            generation=generation,
            result="dummy testing result",
            include_preloading=True,
            include_generation=False,
            include_post_processing=True,
            include_safety_check=False,
        )
