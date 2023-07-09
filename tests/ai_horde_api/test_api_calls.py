from pathlib import Path

import pytest
from horde_sdk.ai_horde_api import (
    AllWorkersDetailsRequest,
    AllWorkersDetailsResponse,
    CancelImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
)
from horde_sdk.ai_horde_api.ai_horde_client import AIHordeAPIClient
from horde_sdk.ai_horde_api.consts import WORKER_TYPE
from horde_sdk.generic_api import RequestErrorResponse
from horde_sdk.generic_api.apimodels import BaseResponse
from horde_sdk.generic_api.utils.swagger import SwaggerDoc

_PRODUCTION_RESPONSES_FOLDER = Path(__file__).parent.parent / "test_data" / "ai_horde_api" / "production_responses"


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

    def test_generate_async(self, default_image_gen_request: ImageGenerateAsyncRequest):
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

        assert isinstance(cancel_response, CancelImageGenerateRequest.get_success_response_type())

    def test_workers_all(self):
        client = AIHordeAPIClient()

        api_request = AllWorkersDetailsRequest(type=WORKER_TYPE.image)

        api_response = client.submit_request(api_request)

        if isinstance(api_response, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response.message}")

        assert isinstance(api_response, AllWorkersDetailsResponse)

        assert len(api_response.workers) > 0

        # Write the response to the production responses folder
        status_response_pairs = AllWorkersDetailsRequest.get_success_status_response_pairs()

        if len(status_response_pairs) != 1:
            raise ValueError("Expected exactly one success status code")

        status_code, _ = status_response_pairs.popitem()

        filename = SwaggerDoc.filename_from_endpoint_path(
            endpoint_path=AllWorkersDetailsRequest.get_endpoint_subpath(),
            http_method=AllWorkersDetailsRequest.get_http_method(),
            http_status_code=status_code,
        )
        filename = filename + "_production.json"

        _PRODUCTION_RESPONSES_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(_PRODUCTION_RESPONSES_FOLDER / filename, "w") as f:
            f.write(api_response.to_json_horde_sdk_safe())
