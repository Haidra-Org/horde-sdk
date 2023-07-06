import pytest
from horde_sdk.ai_horde_api import CancelImageGenerateRequest, ImageGenerateAsyncRequest, ImageGenerateAsyncResponse
from horde_sdk.ai_horde_api.ai_horde_client import AIHordeAPIClient
from horde_sdk.generic_api import RequestErrorResponse
from horde_sdk.generic_api.apimodels import BaseResponse


class TestAIHordeAPIClient:
    @pytest.fixture
    def default_image_gen_request(self) -> ImageGenerateAsyncRequest:
        return ImageGenerateAsyncRequest(
            apikey="0000000000",
            prompt="a cat in a hat",
            models=["Deliberate"],
        )

    def test_AIHordeAPIClient_init(self):
        AIHordeAPIClient()

    def test_AIHordeAPIClient_async(self, default_image_gen_request: ImageGenerateAsyncRequest):
        client = AIHordeAPIClient()

        api_response: ImageGenerateAsyncResponse | RequestErrorResponse = client.generate_image_async(
            default_image_gen_request
        )

        if isinstance(api_response, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response.message}")

        assert isinstance(api_response, ImageGenerateAsyncResponse)

        cancel_request = CancelImageGenerateRequest(apikey="0000000000", id=api_response.id)
        cancel_response: BaseResponse | RequestErrorResponse = client.submit_request(cancel_request)

        if isinstance(cancel_response, RequestErrorResponse):
            pytest.fail(
                f"API Response was an error: {cancel_response.message}"
                f"Please note that the job ({api_response.id}) is orphaned and will continue to run on the server"
                "until it is finished, it times out or it is cancelled manually."
            )

        assert isinstance(cancel_response, CancelImageGenerateRequest.get_expected_response_type())
