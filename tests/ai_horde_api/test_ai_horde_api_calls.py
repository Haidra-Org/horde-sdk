"""Tests which actually call the (or a testing) AI Horde API."""

from pathlib import Path

import aiohttp
import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIClientSession,
    AIHordeAPIManualClient,
)
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


class HordeTestException(Exception):
    """Exception used to test that exceptions raised in the context manager are handled correctly."""


class TestAIHordeAPIClients:
    """Tests which actually call the (or a testing) AI Horde API."""

    def test_AIHordeAPIClient_init(self) -> None:
        """Test that the client can be initialised."""
        AIHordeAPIManualClient()

    def test_generate_async(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        """Test that a simple image generation request can be submitted and cancelled.

        Note, async is the endpoint description, not the python test type.
        """
        client = AIHordeAPIManualClient()

        image_async_response: ImageGenerateAsyncResponse | RequestErrorResponse = client.submit_request(
            api_request=simple_image_gen_request,
            expected_response_type=simple_image_gen_request.get_default_success_response_type(),
        )

        if isinstance(image_async_response, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {image_async_response.message}")

        assert isinstance(image_async_response, ImageGenerateAsyncResponse)

        cancel_response: ImageGenerateStatusResponse | RequestErrorResponse = client.delete_pending_image(
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

        assert isinstance(cancel_response, DeleteImageGenerateRequest.get_default_success_response_type())

    def test_workers_all(self) -> None:
        """Test the all workers endpoint."""
        client = AIHordeAPIManualClient()

        api_request = AllWorkersDetailsRequest()

        api_response = client.submit_request(
            api_request,
            api_request.get_default_success_response_type(),
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
            endpoint_path=AllWorkersDetailsRequest.get_api_endpoint_subpath(),
            http_method=AllWorkersDetailsRequest.get_http_method(),
            http_status_code=status_code,
        )

        _PRODUCTION_RESPONSES_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(_PRODUCTION_RESPONSES_FOLDER / Path(filename + "_production.json"), "w", encoding="utf-8") as f:
            f.write(api_response.model_dump_json())

        api_request_image = AllWorkersDetailsRequest(type=WORKER_TYPE.image)
        api_response_image = client.submit_request(
            api_request_image,
            api_request_image.get_default_success_response_type(),
        )

        if isinstance(api_response_image, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response_image.message}")

        assert isinstance(api_response_image, AllWorkersDetailsResponse)
        assert all(worker.type_ == WORKER_TYPE.image for worker in api_response_image.root)

        api_request_text = AllWorkersDetailsRequest(type=WORKER_TYPE.text)
        api_response_text = client.submit_request(
            api_request_text,
            api_request_text.get_default_success_response_type(),
        )

        if isinstance(api_response_text, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response_text.message}")

        assert isinstance(api_response_text, AllWorkersDetailsResponse)
        assert all(worker.type_ == WORKER_TYPE.text for worker in api_response_text.root)

        api_request_interrogation = AllWorkersDetailsRequest(type=WORKER_TYPE.interrogation)
        api_response_interrogation = client.submit_request(
            api_request_interrogation,
            api_request_interrogation.get_default_success_response_type(),
        )

        if isinstance(api_response_interrogation, RequestErrorResponse):
            pytest.fail(f"API Response was an error: {api_response_interrogation.message}")

        assert isinstance(api_response_interrogation, AllWorkersDetailsResponse)

    def test_HordeRequestSession_cleanup(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        """Test that the context manager cleans up correctly."""
        with pytest.raises(HordeTestException), AIHordeAPIClientSession() as horde_session:
            api_response = horde_session.submit_request(  # noqa: F841
                simple_image_gen_request,
                simple_image_gen_request.get_default_success_response_type(),
            )
            raise HordeTestException("This tests the context manager, not the request/response.")

    @pytest.mark.asyncio
    async def test_HordeRequestSession_async(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        """Test that the context manager cleans up correctly asynchronously."""
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(
                aiohttp_session=aiohttp_session,
            ) as horde_session,
        ):
            api_response = await horde_session.submit_request(  # noqa: F841
                simple_image_gen_request,
                simple_image_gen_request.get_default_success_response_type(),
            )

    @pytest.mark.asyncio
    async def test_HordeRequestSession_async_exception_raised(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that the context manager cleans up correctly asynchronously when an exception is raised."""
        with pytest.raises(HordeTestException):
            async with (
                aiohttp.ClientSession() as aiohttp_session,
                AIHordeAPIAsyncClientSession(
                    aiohttp_session=aiohttp_session,
                ) as horde_session,
            ):
                api_response = await horde_session.submit_request(  # noqa: F841
                    simple_image_gen_request,
                    simple_image_gen_request.get_default_success_response_type(),
                )
                raise HordeTestException("This tests the context manager, not the request/response.")
