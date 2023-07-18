"""Tests which actually call the (or a testing) AI Horde API."""

import asyncio
from pathlib import Path

import aiohttp
import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient, AIHordeAPISession, AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    AllWorkersDetailsRequest,
    AllWorkersDetailsResponse,
    DeleteImageGenerateRequest,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateStatusResponse,
    ImageGeneration,
    ImageGenerationInputPayload,
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
            expected_response_type=simple_image_gen_request.get_success_response_type(),
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

        assert isinstance(cancel_response, DeleteImageGenerateRequest.get_success_response_type())

    def test_workers_all(self) -> None:
        """Test the all workers endpoint."""
        client = AIHordeAPIManualClient()

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

    def test_HordeRequestSession_cleanup(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        """Test that the context manager cleans up correctly."""
        with pytest.raises(HordeTestException), AIHordeAPISession() as horde_session:
            api_response = horde_session.submit_request(  # noqa: F841
                simple_image_gen_request,
                simple_image_gen_request.get_success_response_type(),
            )
            raise HordeTestException("This tests the context manager, not the request/response.")

    @pytest.mark.asyncio
    async def test_HordeRequestSession_async(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        """Test that the context manager cleans up correctly asynchronously."""
        async with aiohttp.ClientSession() as aiohttp_session, AIHordeAPISession(aiohttp_session) as horde_session:
            api_response = await horde_session.async_submit_request(  # noqa: F841
                simple_image_gen_request,
                simple_image_gen_request.get_success_response_type(),
            )

    @pytest.mark.asyncio
    async def test_HordeRequestSession_async_exception_raised(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that the context manager cleans up correctly asynchronously when an exception is raised."""
        with pytest.raises(HordeTestException):
            async with aiohttp.ClientSession() as aiohttp_session, AIHordeAPISession(aiohttp_session) as horde_session:
                api_response = await horde_session.async_submit_request(  # noqa: F841
                    simple_image_gen_request,
                    simple_image_gen_request.get_success_response_type(),
                )
                raise HordeTestException("This tests the context manager, not the request/response.")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that multiple concurrent requests can be made."""
        async with aiohttp.ClientSession() as aiohttp_session:

            async def submit_request(aiohttp_session: aiohttp.ClientSession) -> None:
                async with AIHordeAPISession(aiohttp_session) as horde_session:
                    api_response: ImageGenerateAsyncResponse | RequestErrorResponse = (  # noqa: F841
                        await horde_session.async_submit_request(
                            simple_image_gen_request,
                            simple_image_gen_request.get_success_response_type(),
                        )
                    )

            # Run 5 concurrent requests using asyncio
            await asyncio.gather(*[asyncio.create_task(submit_request(aiohttp_session)) for _ in range(5)])

    def test_simple_client_image_generate(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        generations: list[ImageGeneration] = simple_client.image_generate_request(simple_image_gen_request)

        assert len(generations) == 1

        image = simple_client.generation_to_image(generations[0])

        assert image is not None

    def test_simple_client_image_generate_no_apikey_specified(
        self,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled when no API key is specified."""
        simple_client = AIHordeAPISimpleClient()

        generations = simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                prompt="a cat in a hat",
                params=ImageGenerationInputPayload(
                    seed="1234",
                    n=1,
                ),
                models=["Deliberate"],
            ),
        )

        assert len(generations) == 1

        image = simple_client.generation_to_image(generations[0])

        assert image is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled asynchronously."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPISimpleClient(aiohttp_session)

            generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
                simple_image_gen_request,
            )

            assert len(generations) == 1

            image = await simple_client.async_generation_to_image(generations[0])

            assert image is not None

    def test_simple_client_image_generate_multiple(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a batch of image generation requests can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        generations: list[ImageGeneration] = simple_client.image_generate_request(simple_image_gen_n_requests)

        assert simple_image_gen_n_requests.params is not None
        assert len(generations) == simple_image_gen_n_requests.params.n

        for generation in generations:
            image = simple_client.generation_to_image(generation)

            assert image is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate_multiple(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a batch of image generation requests can be submitted and retrieved asynchronously."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPISimpleClient(aiohttp_session)

            generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
                simple_image_gen_n_requests,
            )

            assert simple_image_gen_n_requests.params is not None
            assert len(generations) == simple_image_gen_n_requests.params.n

            for generation in generations:
                image = await simple_client.async_generation_to_image(generation)

                assert image is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate_multiple_with_timeout(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test a batch of image generation requests can be submitted and cancelled asynchronously with a timeout."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPISimpleClient(aiohttp_session)

            generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
                simple_image_gen_n_requests,
                timeout=7,  # 7 seconds isn't (generally) going to be enough time for 3 generations to complete
            )

            assert simple_image_gen_n_requests.params is not None
            assert len(generations) < simple_image_gen_n_requests.params.n
