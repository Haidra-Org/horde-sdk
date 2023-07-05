import pytest
from horde_sdk.ai_horde_api.ai_horde_client import AIHordeAPIClient
from horde_sdk.ai_horde_api.apimodels.generate import (
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
)
from horde_sdk.generic_api import RequestErrorResponse


@pytest.fixture
def default_image_gen_request() -> ImageGenerateAsyncRequest:
    return ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="a cat in a hat",
        models=["Deliberate"],
    )


def test_AIHordeAPIClient_init():
    AIHordeAPIClient()


def test_AIHordeAPIClient_async(default_image_gen_request: ImageGenerateAsyncRequest):
    client = AIHordeAPIClient()
    api_response: ImageGenerateAsyncResponse | RequestErrorResponse = client.generate_image_async(
        default_image_gen_request
    )

    if isinstance(api_response, RequestErrorResponse):
        pytest.fail(f"API Response was an error: {api_response.message}")

    assert isinstance(api_response, ImageGenerateAsyncResponse)
