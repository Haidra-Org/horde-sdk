import aiohttp
import pytest
from loguru import logger

from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncSimpleClient,
    AIHordeAPISimpleClient,
)
from horde_sdk.ai_horde_api.apimodels import (
    TextGenerateAsyncRequest,
    TextGenerateStatusResponse,
)
from horde_sdk.ai_horde_api.fields import JobID


class TestAIHordeTextGenerate:
    def test_text_generate(self) -> None:
        simple_client = AIHordeAPISimpleClient()
        request = TextGenerateAsyncRequest(
            prompt="Hello, world!",
            models=[
                "koboldcpp/LLaMA2-13B-Psyfighter2",
            ],
        )

        response, job_id = simple_client.text_generate_request(request)

        logger.debug(f"{job_id}: {response}")

        assert isinstance(job_id, JobID)
        assert isinstance(response, TextGenerateStatusResponse)

        assert len(response.generations) == 1
        assert response.generations[0].model == "koboldcpp/LLaMA2-13B-Psyfighter2"
        text_response = response.generations[0].text
        assert text_response is not None
        assert len(text_response) > 0


class TestAIHordeTextGenerateAsync:
    @pytest.mark.asyncio
    async def test_text_generate_async(self) -> None:
        aiohttp_session = aiohttp.ClientSession()
        horde_client_session = AIHordeAPIAsyncClientSession(
            aiohttp_session=aiohttp_session,
        )
        async with aiohttp_session, horde_client_session:
            simple_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)
            request = TextGenerateAsyncRequest(
                prompt="Hello, world!",
                models=[
                    "koboldcpp/LLaMA2-13B-Psyfighter2",
                ],
            )

            response, job_id = await simple_client.text_generate_request(
                request,
                check_callback=lambda response: logger.debug(f"Response: {response}"),
            )

            logger.debug(f"{job_id}: {response}")

            assert isinstance(job_id, JobID)
            assert isinstance(response, TextGenerateStatusResponse)

            assert len(response.generations) == 1
            assert response.generations[0].model == "koboldcpp/LLaMA2-13B-Psyfighter2"
            text_response = response.generations[0].text
            assert text_response is not None
            assert len(text_response) > 0

    @pytest.mark.asyncio
    async def test_text_generate_async_keyboard_interrupt(self) -> None:
        aiohttp_session = aiohttp.ClientSession()
        horde_client_session = AIHordeAPIAsyncClientSession(
            aiohttp_session=aiohttp_session,
        )
        async with aiohttp_session, horde_client_session:
            simple_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)
            request = TextGenerateAsyncRequest(
                prompt="Hello, world!",
                models=[
                    "koboldcpp/LLaMA2-13B-Psyfighter2",
                ],
            )

            def check_callback(response: TextGenerateStatusResponse) -> None:
                logger.debug(f"Response: {response}")
                raise KeyboardInterrupt("Test KeyboardInterrupt")

            with pytest.raises(KeyboardInterrupt):
                await simple_client.text_generate_request(
                    request,
                    check_callback=check_callback,
                )
