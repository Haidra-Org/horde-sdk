import asyncio

import aiohttp
import pytest

from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncSimpleClient,
    AIHordeAPISimpleClient,
)
from horde_sdk.ai_horde_api.apimodels import (
    KNOWN_ALCHEMY_TYPES,
    AlchemyAsyncRequest,
    AlchemyAsyncRequestFormItem,
    AlchemyStatusResponse,
    ImageGenerateAsyncRequest,
    ImageGenerateAsyncResponse,
    ImageGenerateStatusResponse,
    ImageGeneration,
    ImageGenerationInputPayload,
    LorasPayloadEntry,
)
from horde_sdk.ai_horde_api.consts import (
    KNOWN_FACEFIXERS,
    KNOWN_MISC_POST_PROCESSORS,
    KNOWN_UPSCALERS,
    POST_PROCESSOR_ORDER_TYPE,
)
from horde_sdk.ai_horde_api.fields import JobID
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
                async with AIHordeAPIAsyncClientSession(aiohttp_session) as horde_session:
                    api_response: ImageGenerateAsyncResponse | RequestErrorResponse = (
                        await horde_session.submit_request(
                            simple_image_gen_request,
                            simple_image_gen_request.get_default_success_response_type(),
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

        image_generate_status_respons, job_id = simple_client.image_generate_request(simple_image_gen_request)

        if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
            raise AssertionError(image_generate_status_respons.generations.message)

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

        assert image is not None

    def test_simple_client_image_generate_with_post_process(
        self,
        ai_horde_api_key: str,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        pp_image_gen_request = ImageGenerateAsyncRequest(
            apikey=ai_horde_api_key,
            prompt="a cat in a hat",
            params=ImageGenerationInputPayload(
                seed="1234",
                n=1,
                post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            ),
            models=["Deliberate"],
        )

        image_generate_status_respons, job_id = simple_client.image_generate_request(pp_image_gen_request)

        if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
            raise AssertionError(image_generate_status_respons.generations.message)

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

        assert image is not None

    def test_simple_client_image_generate_with_post_process_costly_order(
        self,
        ai_horde_api_key: str,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        pp_image_gen_request = ImageGenerateAsyncRequest(
            apikey=ai_horde_api_key,
            prompt="a cat in a hat",
            params=ImageGenerationInputPayload(
                seed="1234",
                n=1,
                post_processing=[
                    KNOWN_UPSCALERS.RealESRGAN_x2plus,
                    KNOWN_FACEFIXERS.CodeFormers,
                    KNOWN_MISC_POST_PROCESSORS.strip_background,
                ],
                post_processing_order=POST_PROCESSOR_ORDER_TYPE.custom,
            ),
            models=["Deliberate"],
        )

        image_generate_status_respons, job_id = simple_client.image_generate_request(pp_image_gen_request)

        if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
            raise AssertionError(image_generate_status_respons.generations.message)

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

        assert image is not None

    def test_simple_client_image_generate_with_post_process_fix_costly_order(
        self,
        ai_horde_api_key: str,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        pp_image_gen_request = ImageGenerateAsyncRequest(
            apikey=ai_horde_api_key,
            prompt="a cat in a hat",
            params=ImageGenerationInputPayload(
                seed="1234",
                n=1,
                post_processing=[
                    KNOWN_UPSCALERS.RealESRGAN_x2plus,
                    KNOWN_FACEFIXERS.CodeFormers,
                    KNOWN_MISC_POST_PROCESSORS.strip_background,
                ],
                post_processing_order=POST_PROCESSOR_ORDER_TYPE.facefixers_first,
            ),
            models=["Deliberate"],
        )

        image_generate_status_respons, job_id = simple_client.image_generate_request(pp_image_gen_request)

        if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
            raise AssertionError(image_generate_status_respons.generations.message)

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

        assert image is not None

    def test_simple_client_image_generate_no_apikey_specified(
        self,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled when no API key is specified."""
        simple_client = AIHordeAPISimpleClient()

        image_generate_status_respons, job_id = simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                prompt="a cat in a hat",
                params=ImageGenerationInputPayload(
                    seed="1234",
                    n=1,
                ),
                models=["Deliberate"],
            ),
        )

        if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
            raise AssertionError(image_generate_status_respons.generations.message)

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

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
                loras=[LorasPayloadEntry(name="76693", model=1, clip=1)],
            ),
            models=["Deliberate"],
        )

        simple_client = AIHordeAPISimpleClient()

        image_generate_status_respons, job_id = simple_client.image_generate_request(
            lora_image_gen_request,
        )

        assert len(image_generate_status_respons.generations) == 1

        image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

        assert image is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a simple image generation request can be submitted and cancelled asynchronously."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            image_generate_status_respons, job_id = await simple_client.image_generate_request(
                simple_image_gen_request,
            )

            assert len(image_generate_status_respons.generations) == 1

            image = await simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

            assert image is not None

    def test_simple_client_image_generate_multiple_n(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a batch of image generation requests can be submitted and cancelled."""
        simple_client = AIHordeAPISimpleClient()

        image_generate_status_respons, job_id = simple_client.image_generate_request(simple_image_gen_n_requests)

        assert simple_image_gen_n_requests.params is not None
        assert len(image_generate_status_respons.generations) == simple_image_gen_n_requests.params.n

        for generation in image_generate_status_respons.generations:
            image = simple_client.download_image_from_generation(generation)

            assert image is not None

    def test_simple_client_image_generate_multiple_requests(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        simple_client = AIHordeAPISimpleClient()

        for _ in range(5):
            image_generate_status_respons, job_id = simple_client.image_generate_request(simple_image_gen_request)

            if isinstance(image_generate_status_respons.generations, RequestErrorResponse):
                raise AssertionError(image_generate_status_respons.generations.message)

            assert len(image_generate_status_respons.generations) == 1

            image = simple_client.download_image_from_generation(image_generate_status_respons.generations[0])

            assert image is not None

    def test_simple_client_alchemy_basic(
        self,
        default_testing_image_base64: str,
    ) -> None:
        simple_client = AIHordeAPISimpleClient()

        result, jobid = simple_client.alchemy_request(
            alchemy_request=AlchemyAsyncRequest(
                forms=[
                    AlchemyAsyncRequestFormItem(
                        name=KNOWN_ALCHEMY_TYPES.caption,
                    ),
                    AlchemyAsyncRequestFormItem(
                        name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus,
                    ),
                ],
                source_image=default_testing_image_base64,
            ),
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_alchemy_basic_flood(
        self,
        default_testing_image_base64: str,
    ) -> None:
        # Perform 15 requests in parallel
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            async def submit_request() -> AlchemyStatusResponse:
                result, jobid = await simple_client.alchemy_request(
                    alchemy_request=AlchemyAsyncRequest(
                        forms=[
                            AlchemyAsyncRequestFormItem(
                                name=KNOWN_ALCHEMY_TYPES.caption,
                            ),
                            AlchemyAsyncRequestFormItem(
                                name=KNOWN_ALCHEMY_TYPES.RealESRGAN_x4plus,
                            ),
                        ],
                        source_image=default_testing_image_base64,
                    ),
                )

                if isinstance(result, RequestErrorResponse):
                    raise AssertionError(result.message)

                return result

            # Run 15 concurrent requests using asyncio
            tasks = [asyncio.create_task(submit_request()) for _ in range(15)]
            all_responses: list[AlchemyStatusResponse | None] = await asyncio.gather(*tasks)

            # Check that all requests were successful
            assert len([response for response in all_responses if response]) == 15

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate_multiple(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test that a batch of image generation requests can be submitted and retrieved asynchronously."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            image_generate_status_response, job_id = await simple_client.image_generate_request(
                simple_image_gen_n_requests,
            )

            if isinstance(image_generate_status_response.generations, RequestErrorResponse):
                raise AssertionError(image_generate_status_response.generations.message)

            assert simple_image_gen_n_requests.params is not None
            assert len(image_generate_status_response.generations) == simple_image_gen_n_requests.params.n

            for generation in image_generate_status_response.generations:
                image = await simple_client.download_image_from_generation(generation)

                assert image is not None

    @pytest.mark.asyncio
    async def test_simple_client_async_image_generate_multiple_with_timeout(
        self,
        simple_image_gen_n_requests: ImageGenerateAsyncRequest,
    ) -> None:
        """Test a batch of image generation requests can be submitted and cancelled asynchronously with a timeout."""
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            image_generate_status_response, job_id = await simple_client.image_generate_request(
                simple_image_gen_n_requests,
                timeout=7,  # 7 seconds isn't (generally) going to be enough time for 3 generations to complete
            )

            if isinstance(image_generate_status_response.generations, RequestErrorResponse):
                raise AssertionError(image_generate_status_response.generations.message)

            assert simple_image_gen_n_requests.params is not None
            assert len(image_generate_status_response.generations) < simple_image_gen_n_requests.params.n

    async def delayed_cancel(self, task: asyncio.Task) -> None:
        """Cancel the task after 3 seconds."""
        await asyncio.sleep(3)
        assert task.cancel("Test cancel")

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests_cancel_single_task(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            async def _submit_request() -> tuple[ImageGenerateStatusResponse, JobID] | None:
                try:
                    image_generate_status_response, job_id = await simple_client.image_generate_request(
                        simple_image_gen_request,
                        timeout=-1,
                    )
                    return image_generate_status_response, job_id
                except asyncio.CancelledError:
                    return None

            # Run 5 concurrent requests using asyncio
            tasks = [asyncio.create_task(_submit_request()) for _ in range(5)]
            all_generations: list[list[ImageGeneration]] = await asyncio.gather(*tasks, self.delayed_cancel(tasks[0]))

            # Check that all requests were successful
            assert len([generations for generations in all_generations if generations]) == 4

    @pytest.mark.asyncio
    async def test_multiple_concurrent_async_requests_cancel_all_tasks(
        self,
        simple_image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        async with aiohttp.ClientSession() as aiohttp_session:
            simple_client = AIHordeAPIAsyncSimpleClient(aiohttp_session)

            async def submit_request() -> ImageGenerateStatusResponse | None:
                try:
                    image_generate_status_response, job_id = await simple_client.image_generate_request(
                        simple_image_gen_request,
                        timeout=-1,
                    )

                    if isinstance(image_generate_status_response.generations, RequestErrorResponse):
                        raise AssertionError(image_generate_status_response.generations.message)
                    return image_generate_status_response
                except asyncio.CancelledError:
                    return None

            # Run 5 concurrent requests using asyncio
            tasks = [asyncio.create_task(submit_request()) for _ in range(5)]
            cancel_tasks = [asyncio.create_task(self.delayed_cancel(task)) for task in tasks]
            all_generations: list[ImageGenerateStatusResponse] = await asyncio.gather(*tasks, *cancel_tasks)

            # Check that all requests were successful
            assert len([generations for generations in all_generations if generations]) == 0
