import asyncio
import base64
import functools
import io
import os
import pathlib
import sys
from collections.abc import Callable
from uuid import UUID

import PIL.Image
import pytest
from loguru import logger

from horde_sdk.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.worker.model_meta import ImageModelLoadResolver

os.environ["TESTS_ONGOING"] = "1"

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.apimodels import (
    AlchemyJobPopResponse,
    AlchemyPopFormPayload,
    ImageGenerateAsyncRequest,
    ImageGenerateJobPopPayload,
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
    ImageGenerationInputPayload,
    ModelPayloadKobold,
    NoValidAlchemyFound,
    NoValidRequestFoundKobold,
    TextGenerateJobPopResponse,
)
from horde_sdk.generation_parameters.alchemy.consts import KNOWN_UPSCALERS
from horde_sdk.ai_horde_api.fields import GenerationID
from horde_sdk.generic_api.consts import ANON_API_KEY


@pytest.fixture(scope="session", autouse=True)
def check_tests_ongoing_env_var() -> None:
    """Checks that the TESTS_ONGOING environment variable is set."""
    assert os.getenv("TESTS_ONGOING", None) is not None, "TESTS_ONGOING environment variable not set"

    AI_HORDE_TESTING = os.getenv("AI_HORDE_TESTING", None)
    HORDE_SDK_TESTING = os.getenv("HORDE_SDK_TESTING", None)
    if AI_HORDE_TESTING is None and HORDE_SDK_TESTING is None:
        logger.warning(
            "Neither AI_HORDE_TESTING nor HORDE_SDK_TESTING environment variables are set. "
            "Is this a local development test run? If so, set AI_HORDE_TESTING=1 or HORDE_SDK_TESTING=1 to suppress "
            "this warning",
        )

    if AI_HORDE_TESTING is not None:
        logger.info("AI_HORDE_TESTING environment variable set.")

    if HORDE_SDK_TESTING is not None:
        logger.info("HORDE_SDK_TESTING environment variable set.")


@pytest.fixture(scope="session")
def ai_horde_api_key() -> str:
    """Return the key being used for testing against an AI Horde API."""
    dev_key = os.getenv("AI_HORDE_DEV_APIKEY", None)

    return dev_key if dev_key is not None else ANON_API_KEY


@pytest.fixture(scope="session")
def model_reference_manager() -> ModelReferenceManager:
    return ModelReferenceManager()


@pytest.fixture(scope="session")
def image_model_load_resolver(model_reference_manager: ModelReferenceManager) -> ImageModelLoadResolver:
    return ImageModelLoadResolver(model_reference_manager)


@functools.cache
def _get_testing_image(filename: str) -> bytes:
    """Returns a test image."""

    image_bytes = None

    # Get the directory of this file
    dir_path = pathlib.Path(__file__).parent.absolute()
    test_image_path = dir_path / "test_data" / "images" / filename

    with open(test_image_path, "rb") as f:
        image_bytes = f.read()

    assert image_bytes is not None

    return image_bytes


@functools.cache
def _get_testing_image_base64(filename: str) -> str:
    """Returns a base64 encoded test image."""
    return base64.b64encode(_get_testing_image(filename)).decode("utf-8")


@pytest.fixture(scope="function")
def default_testing_image_bytes() -> bytes:
    """Returns a test image."""
    return _get_testing_image("haidra.png")


@pytest.fixture(scope="function")
def default_testing_image_PIL() -> PIL.Image.Image:
    """Returns a test image."""
    return PIL.Image.open(io.BytesIO(_get_testing_image("haidra.png")))


@pytest.fixture(scope="function")
def default_testing_image_base64() -> str:
    """Returns a base64 encoded test image."""
    return _get_testing_image_base64("haidra.png")


@pytest.fixture(scope="function")
def img2img_testing_image_base64() -> str:
    """Returns a base64 encoded test image."""
    return base64.b64encode(_get_testing_image("sketch-mountains-input.jpg")).decode("utf-8")


@pytest.fixture(scope="function")
def inpaint_source_image_and_mask_PIL() -> tuple[PIL.Image.Image, PIL.Image.Image]:
    """Returns a test image and mask suitable for inpainting."""
    image = PIL.Image.open(io.BytesIO(_get_testing_image("test_inpaint_original.png")))
    mask = PIL.Image.open(io.BytesIO(_get_testing_image("test_inpaint_mask.png")))

    return image, mask


@pytest.fixture(scope="function")
def inpainting_source_image_and_mask_base64() -> tuple[str, str]:
    """Returns a base64 encoded test image and mask suitable for inpainting."""
    image = _get_testing_image_base64("test_inpaint_original.png")
    mask = _get_testing_image_base64("test_inpaint_mask.png")

    return image, mask


@pytest.fixture(scope="function")
def outpaint_alpha_source_image_base64() -> str:
    """Returns a base64 encoded test image suitable for outpainting."""
    return _get_testing_image_base64("test_outpaint.png")


@pytest.fixture(scope="function")
def openpose_control_map_base64() -> str:
    """Returns a base64 encoded test image of a pre-processed control image."""
    return _get_testing_image_base64("test_openpose_control_map.png")


@pytest.fixture(scope="function")
def woman_headshot_testing_image_base64() -> str:
    return base64.b64encode(_get_testing_image("woman_headshot_bokeh.png")).decode("utf-8")


@pytest.fixture(scope="function")
def simple_image_gen_request(ai_horde_api_key: str) -> ImageGenerateAsyncRequest:
    """Return a simple `ImageGenerateAsyncRequest` instance with minimal arguments set."""
    return ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        prompt="a cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            steps=5,
            n=1,
        ),
    )


@pytest.fixture(scope="function")
def simple_image_gen_n_requests(ai_horde_api_key: str) -> ImageGenerateAsyncRequest:
    """Return a simple `ImageGenerateAsyncRequest` instance with minimal arguments set, but with n==3."""
    return ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        prompt="a cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            steps=1,
            n=3,
        ),
    )


_id_counter = 0


def _single_id() -> GenerationID:
    """Return a new UUID for each call."""
    global _id_counter
    _id_counter += 1

    num_to_use = _id_counter
    # copy the last 8 bits to fill the rest of the UUID
    for i in range(8):
        num_to_use |= num_to_use << (8 * i)

    # mask to 128 bits (16 bytes, the size of a UUID)
    num_to_use &= (1 << 128) - 1
    return GenerationID(root=UUID(int=num_to_use))


@pytest.fixture(scope="function")
def single_id() -> GenerationID:
    """Return a new UUID for each call."""
    return _single_id()


@pytest.fixture(scope="function")
def id_factory() -> Callable[[], GenerationID]:
    """Return a function that generates a new UUID for each call."""
    return _single_id


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response(
    single_id: UUID,
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance with a typical model and no arguments set."""
    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="42"),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_n_requests(
    id_factory: Callable[[], GenerationID],
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance with no arguments set."""
    ids = [id_factory() for _ in range(3)]
    return ImageGenerateJobPopResponse(
        ids=ids,
        payload=ImageGenerateJobPopPayload(prompt="a cat in a hat", seed="42"),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        r2_uploads=[f"https://not.a.real.url.internal/upload/{id_}" for id_ in ids],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_post_processing(
    single_id: UUID,
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance with a upscaling post-processing argument set."""
    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            seed="42",
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_img2img(
    single_id: UUID,
    img2img_testing_image_base64: str,
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance for `img2img` and no other arguments set"""
    from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING

    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            seed="42",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=img2img_testing_image_base64,
        source_processing=KNOWN_SOURCE_PROCESSING.img2img,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_img2img_masked(
    single_id: UUID,
    inpainting_source_image_and_mask_base64: tuple[str, str],
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance for `img2img` and no other arguments set"""
    from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING

    source_image, source_mask = inpainting_source_image_and_mask_base64

    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            seed="42",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=source_image,
        source_mask=source_mask,
        source_processing=KNOWN_SOURCE_PROCESSING.img2img,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_inpainting(
    single_id: UUID,
    inpainting_source_image_and_mask_base64: tuple[str, str],
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance for `img2img` and no other arguments set"""
    from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING

    source_image, source_mask = inpainting_source_image_and_mask_base64

    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            seed="42",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=source_image,
        source_mask=source_mask,
        source_processing=KNOWN_SOURCE_PROCESSING.inpainting,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_outpainting_alpha(
    single_id: UUID,
    outpaint_alpha_source_image_base64: str,
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance for `img2img` and no other arguments set"""
    from horde_sdk.generation_parameters.image.consts import KNOWN_SOURCE_PROCESSING

    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            seed="42",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=outpaint_alpha_source_image_base64,
        source_processing=KNOWN_SOURCE_PROCESSING.inpainting,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_job_pop_response_controlnet_openpose(
    single_id: UUID,
    openpose_control_map_base64: str,
) -> ImageGenerateJobPopResponse:
    """Return a `ImageGenerateJobPopResponse` instance for `controlnet` and no other arguments set"""
    from horde_sdk.generation_parameters.image.consts import KNOWN_CONTROLNETS

    return ImageGenerateJobPopResponse(
        ids=[single_id],
        payload=ImageGenerateJobPopPayload(
            prompt="a cat in a hat",
            image_is_control=True,
            control_type=KNOWN_CONTROLNETS.openpose,
            seed="42",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
        model="Deliberate",
        source_image=openpose_control_map_base64,
        r2_uploads=[f"https://not.a.real.url.internal/upload/{single_id}"],
    )


@pytest.fixture(scope="function")
def simple_text_gen_job_pop_response(
    single_id: UUID,
) -> TextGenerateJobPopResponse:
    """Return a `TextGenerateJobPopResponse` instance with a dummy model no other arguments set."""
    return TextGenerateJobPopResponse(
        ids=[single_id],
        payload=ModelPayloadKobold(prompt="Tell me about a cat in a hat."),
        skipped=NoValidRequestFoundKobold(),
        model="oFakeModel",
    )


@pytest.fixture(scope="function")
def simple_alchemy_gen_job_pop_response(
    single_id: UUID,
) -> AlchemyJobPopResponse:
    """Return a `AlchemyJobPopResponse` instance for `interrogation` and no other arguments set"""
    return AlchemyJobPopResponse(
        forms=[
            AlchemyPopFormPayload(
                id=single_id,
                form=KNOWN_ALCHEMY_TYPES.interrogation,
                r2_upload=f"https://not.a.real.url.internal/upload/{single_id}",
            ),
        ],
        skipped=NoValidAlchemyFound(),
    )


@pytest.fixture(scope="function")
def simple_alchemy_gen_job_pop_nsfw_check(
    single_id: UUID,
) -> AlchemyJobPopResponse:
    """Return a `AlchemyJobPopResponse` instance for `nsfw` check and no other arguments set"""
    return AlchemyJobPopResponse(
        forms=[
            AlchemyPopFormPayload(
                id=single_id,
                form=KNOWN_ALCHEMY_TYPES.nsfw,
                r2_upload=f"https://not.a.real.url.internal/upload/{single_id}",
            ),
        ],
        skipped=NoValidAlchemyFound(),
    )


def pytest_collection_modifyitems(items):  # type: ignore # noqa
    """Modifies test items to ensure test modules run in a given order."""
    MODULES_TO_RUN_FIRST = [
        "tests.tests_generic",
        "tests.test_utils",
        "tests.test_dynamically_check_apimodels",
        "tests.test_verify_api_surface",
    ]

    MODULES_TO_RUN_LAST = [
        "tests.ai_horde_api.test_ai_horde_api_calls",
        "tests.ai_horde_api.test_ai_horde_alchemy_api_calls",
        "tests.ai_horde_api.test_ai_horde_generate_api_calls",
    ]  # FIXME make dynamic
    module_mapping = {item: item.module.__name__ for item in items}

    sorted_items = []

    for module in MODULES_TO_RUN_FIRST:
        sorted_items.extend([item for item in items if module_mapping[item] == module])

    sorted_items.extend(
        [item for item in items if module_mapping[item] not in MODULES_TO_RUN_FIRST + MODULES_TO_RUN_LAST],
    )

    for module in MODULES_TO_RUN_LAST:
        sorted_items.extend([item for item in items if module_mapping[item] == module])

    items[:] = sorted_items
