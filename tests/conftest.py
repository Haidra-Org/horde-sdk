import base64
import os
import pathlib

import pytest

from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload
from horde_sdk.generic_api.consts import ANON_API_KEY


@pytest.fixture(scope="session")
def ai_horde_api_key() -> str:
    dev_key = os.getenv("AI_HORDE_DEV_APIKEY", None)

    return dev_key if dev_key is not None else ANON_API_KEY


@pytest.fixture(scope="function")
def simple_image_gen_request(ai_horde_api_key: str) -> ImageGenerateAsyncRequest:
    return ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        prompt="a cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            steps=1,
            n=1,
        ),
    )


@pytest.fixture(scope="function")
def simple_image_gen_n_requests(ai_horde_api_key: str) -> ImageGenerateAsyncRequest:
    return ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        prompt="a cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            steps=1,
            n=3,
        ),
    )


def pytest_collection_modifyitems(items):  # type: ignore # noqa
    """Modifies test items to ensure test modules run in a given order."""
    MODULES_TO_RUN_FIRST = ["tests_generic", "test_utils", "test_dynamically_check_apimodels"]

    MODULES_TO_RUN_LAST = [
        "tests.ai_horde_api.test_ai_horde_api_calls",
        "test.ai_horde_api.test_ai_horde_alchemy_api_calls",
        "test.ai_horde_api.test_ai_horde_generate_api_calls",
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


@pytest.fixture(scope="session")
def default_testing_image_base64() -> str:
    """Returns a base64 encoded test image."""
    return base64.b64encode(_get_testing_image("haidra.png")).decode("utf-8")


@pytest.fixture(scope="session")
def img2img_testing_image_base64() -> str:
    """Returns a base64 encoded test image."""
    return base64.b64encode(_get_testing_image("sketch-mountains-input.jpg")).decode("utf-8")


@pytest.fixture(scope="session")
def woman_headshot_testing_image_base64() -> str:
    return base64.b64encode(_get_testing_image("woman_headshot_bokeh.png")).decode("utf-8")
