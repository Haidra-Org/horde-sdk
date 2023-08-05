import asyncio

import aiohttp
import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISession, AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGeneration,
    ImageGenerationInputPayload,
    LorasPayloadEntry,
)
from horde_sdk.generic_api.apimodels import RequestErrorResponse


class TestAIHordeGenerate:
    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test multiple concurrent requests. Note this test does not wait for the requests to finish."""
        async with aiohttp.ClientSession() as aiohttp_session:

            async def submit_request(
                aiohttp_session: aiohttp.ClientSession,
            ) -> ImageGenerateAsyncResponse | RequestErrorResponse | None:
                async with AIHordeAPISession(aiohttp_session) as horde_session:
                    api_response: ImageGenerateAsyncResponse | RequestErrorResponse = (
                        await horde_session.async_submit_request(  # noqa: F841
                            simple_image_gen_request,
                            simple_image_gen_request.get_success_response_type(),
                        )
                    )
                    return api_response
                return None

            # Run 5 concurrent requests using asyncio
            all_responses: list[ImageGenerateAsyncResponse | RequestErrorResponse | None] = await asyncio.gather(
                *[asyncio.create_task(submit_request(aiohttp_session)) for _ in range(5)],
            )

            # Check that all requests were successful
            assert (
                len([response for response in all_responses if isinstance(response, ImageGenerateAsyncResponse)]) == 5
            )

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

    def test_simple_client_image_generate_loras(
        self,
    ) -> None:
        """Test that a simple image generation with loras is successful."""

        lora_image_gen_request = ImageGenerateAsyncRequest(
            prompt="a cat in a hat",
            params=ImageGenerationInputPayload(
                seed="1234",
                n=1,
                loras=[LorasPayloadEntry(name="48139", model=1, clip=1)],
            ),
            models=["Deliberate"],
        )

        simple_client = AIHordeAPISimpleClient()

        generations: list[ImageGeneration] = simple_client.image_generate_request(lora_image_gen_request)

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

    def test_simple_client_image_generate_multiple_n(
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

    def test_simple_client_image_generate_multiple_requests(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        simple_client = AIHordeAPISimpleClient()

        for _ in range(5):
            generations: list[ImageGeneration] = simple_client.image_generate_request(simple_image_gen_request)

            assert len(generations) == 1

            image = simple_client.generation_to_image(generations[0])

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

    async def delayed_cancel(self, task: asyncio.Task) -> None:
        """Cancel the task after 2 seconds."""
        await asyncio.sleep(4)
        assert task.cancel("Test cancel")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests_cancel_single_task(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPISimpleClient(aiohttp_session)

            async def submit_request() -> list[ImageGeneration]:
                generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
                    simple_image_gen_request,
                    timeout=-1,
                )
                return generations

            # Run 5 concurrent requests using asyncio
            tasks = [asyncio.create_task(submit_request()) for _ in range(5)]
            all_generations: list[list[ImageGeneration]] = await asyncio.gather(*tasks, self.delayed_cancel(tasks[0]))

            # Check that all requests were successful
            assert len([generations for generations in all_generations if generations]) == 4

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests_cancel_all_tasks(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPISimpleClient(aiohttp_session)

            async def submit_request() -> list[ImageGeneration]:
                generations: list[ImageGeneration] = await simple_client.async_image_generate_request(
                    simple_image_gen_request,
                    timeout=-1,
                )
                return generations

            # Run 5 concurrent requests using asyncio
            tasks = [asyncio.create_task(submit_request()) for _ in range(5)]
            cancel_tasks = [asyncio.create_task(self.delayed_cancel(task)) for task in tasks]
            all_generations: list[list[ImageGeneration]] = await asyncio.gather(*tasks, *cancel_tasks)

            # Check that all requests were successful
            assert len([generations for generations in all_generations if generations]) == 0
