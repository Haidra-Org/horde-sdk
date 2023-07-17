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


def pytest_collection_modifyitems(items: list) -> None:
    """Modifies test items in place to ensure test modules run in a given order."""
    MODULE_ORDER = ["tests_generic", "test_utils", "test_dynamically_check_apimodels"]
    # `test.scripts` must run first because it downloads the legacy database
    module_mapping = {item: item.module.__name__ for item in items}

    sorted_items = items.copy()

    # Iteratively move tests of each module to the end of the test queue
    for module in MODULE_ORDER:
        sorted_items = [it for it in sorted_items if module_mapping[it] != module] + [
            it for it in sorted_items if module_mapping[it] == module
        ]

    items[:] = sorted_items
