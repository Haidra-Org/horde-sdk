import pytest

from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload


@pytest.fixture(scope="function")
def simple_image_gen_request() -> ImageGenerateAsyncRequest:
    return ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="a cat in a hat",
        models=["Deliberate"],
    )


@pytest.fixture(scope="function")
def simple_image_gen_n_requests() -> ImageGenerateAsyncRequest:
    return ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="a cat in a hat",
        models=["Deliberate"],
        params=ImageGenerationInputPayload(
            n=3,
        ),
    )


def pytest_collection_modifyitems(items):  # type: ignore
    """Modifies test items to ensure test modules run in a given order."""
    MODULES_TO_RUN_FIRST = ["tests_generic", "test_utils", "test_dynamically_check_apimodels"]

    MODULES_TO_RUN_LAST = [
        "tests.ai_horde_api.test_ai_horde_api_calls",
    ]
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
