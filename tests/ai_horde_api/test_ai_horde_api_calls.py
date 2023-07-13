import asyncio
from pathlib import Path

import pytest

from horde_sdk.ai_horde_api.ai_horde_client import AIHordeAPISession, AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    AllWorkersDetailsRequest,
    AllWorkersDetailsResponse,
    DeleteImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateStatusResponse,
)
from horde_sdk.ai_horde_api.consts import WORKER_TYPE
from horde_sdk.generic_api.apimodels import RequestErrorResponse
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

    def test_AIHordeAPIClient_init(self) -> None:
        AIHordeAPISimpleClient()

    def test_generate_async(self, default_image_gen_request: ImageGenerateAsyncRequest) -> None:
        client = AIHordeAPISimpleClient()

        image_async_response: ImageGenerateAsyncResponse | RequestErrorResponse = client.submit_request(
            api_request=default_image_gen_request,
            expected_response_type=default_image_gen_request.get_success_response_type(),
        )

        if isinstance(image_async_response, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {image_async_response.message}")

        assert isinstance(image_async_response, ImageGenerateAsyncResponse)

        cancel_response: ImageGenerateStatusResponse | RequestErrorResponse = client.delete_pending_image(
            "0000000000",
            image_async_response.id_,
        )
        if isinstance(cancel_response, RequestErrorResponse):
            pytest.fail(
                (
                    f"API Response was an error: {cancel_response.message}Please note that the job"
                    f" ({image_async_response.id_}) is orphaned and will continue to run on the server until it is"
                    " finished, it times out or it is cancelled manually."
                ),
            )

        assert isinstance(cancel_response, DeleteImageGenerateRequest.get_success_response_type())

    def test_workers_all(self) -> None:
        client = AIHordeAPISimpleClient()

        api_request = AllWorkersDetailsRequest(type=WORKER_TYPE.image)

        api_response = client.submit_request(
            api_request,
            api_request.get_success_response_type(),
        )

        if isinstance(api_response, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response.message}")

        assert isinstance(api_response, AllWorkersDetailsResponse)

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


class HordeTestException(Exception):
    pass


def test_HordeRequestSession(simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
    with pytest.raises(HordeTestException), AIHordeAPISession() as horde_session:
        api_response = horde_session.submit_request(  # noqa: F841
            simple_image_gen_request,
            simple_image_gen_request.get_success_response_type(),
        )
        raise HordeTestException("This tests the context manager, not the request/response.")


@pytest.mark.asyncio
async def test_HordeRequestSession_async(simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
    with AIHordeAPISession() as horde_session:
        api_response = await horde_session.async_submit_request(  # noqa: F841
            simple_image_gen_request,
            simple_image_gen_request.get_success_response_type(),
        )


@pytest.mark.asyncio
async def test_HordeRequestSession_async_exception_raised(simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
    with pytest.raises(HordeTestException), AIHordeAPISession() as horde_session:
        api_response = await horde_session.async_submit_request(  # noqa: F841
            simple_image_gen_request,
            simple_image_gen_request.get_success_response_type(),
        )
        raise HordeTestException("This tests the context manager, not the request/response.")


@pytest.mark.asyncio
async def test_multiple_concurrent_async_requests(simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
    async def submit_request() -> None:
        async with AIHordeAPISession() as horde_session:
            api_response: ImageGenerateAsyncResponse | RequestErrorResponse = (  # noqa: F841
                await horde_session.async_submit_request(
                    simple_image_gen_request,
                    simple_image_gen_request.get_success_response_type(),
                )
            )

    # Run 5 concurrent requests using asyncio
    await asyncio.gather(*[asyncio.create_task(submit_request()) for _ in range(5)])
