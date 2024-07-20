import asyncio

import aiohttp
import PIL.Image
import pytest
import yarl
from loguru import logger

from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
    AIHordeAPIAsyncSimpleClient,
)
from horde_sdk.ai_horde_api.apimodels import (
    ImageGenerateAsyncRequest,
    ImageGenerateJobPopRequest,
    ImageGenerateJobPopResponse,
    ImageGenerateStatusResponse,
    ImageGenerationJobSubmitRequest,
    JobSubmitResponse,
)
from horde_sdk.ai_horde_api.consts import (
    GENERATION_STATE,
)
from horde_sdk.ai_horde_api.fields import JobID


class TestImageWorkerRoundtrip:
    async def fake_worker_checkin(
        self,
        aiohttp_session: aiohttp.ClientSession,
        horde_client_session: AIHordeAPIAsyncClientSession,
        image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        assert image_gen_request.params is not None

        effective_resolution = (image_gen_request.params.width * image_gen_request.params.height) * 2

        job_pop_request = ImageGenerateJobPopRequest(
            name="fake CI worker",
            bridge_agent="AI Horde Worker reGen:8.0.1-citests:https://github.com/Haidra-Org/horde-worker-reGen",
            max_pixels=effective_resolution,
            models=image_gen_request.models,
        )

        job_pop_response = await horde_client_session.submit_request(
            job_pop_request,
            job_pop_request.get_default_success_response_type(),
        )

        assert isinstance(job_pop_response, ImageGenerateJobPopResponse)
        logger.info(f"{job_pop_response.log_safe_model_dump({'skipped'})}")

        assert not job_pop_response.ids_present
        assert job_pop_response.skipped is not None

        logger.info(f"Checked in as fake worker ({effective_resolution}): {job_pop_response.skipped}")

    async def fake_worker(
        self,
        aiohttp_session: aiohttp.ClientSession,
        horde_client_session: AIHordeAPIAsyncClientSession,
        image_gen_request: ImageGenerateAsyncRequest,
    ) -> None:
        assert image_gen_request.params is not None

        effective_resolution = (image_gen_request.params.width * image_gen_request.params.height) * 2

        job_pop_request = ImageGenerateJobPopRequest(
            name="fake CI worker",
            bridge_agent="AI Horde Worker reGen:8.0.1-citests:https://github.com/Haidra-Org/horde-worker-reGen",
            max_pixels=effective_resolution,
            models=image_gen_request.models,
        )

        max_tries = 5
        try_wait = 5
        current_try = 0

        while True:
            job_pop_response = await horde_client_session.submit_request(
                job_pop_request,
                job_pop_request.get_default_success_response_type(),
            )

            assert isinstance(job_pop_response, ImageGenerateJobPopResponse)
            logger.info(f"{job_pop_response.log_safe_model_dump({'skipped'})}")
            logger.info(f"Checked in as fake worker ({effective_resolution}): {job_pop_response.skipped}")

            if not job_pop_response.ids_present:
                if current_try >= max_tries:
                    raise RuntimeError("Max tries exceeded")

                logger.info(f"Waiting {try_wait} seconds before retrying")
                await asyncio.sleep(try_wait)
                current_try += 1
                continue

            # We're going to send a blank image base64 encoded
            fake_image = PIL.Image.new(
                "RGB",
                (image_gen_request.params.width, image_gen_request.params.height),
                (255, 255, 255),
            )

            fake_image_bytes = fake_image.tobytes()

            r2_url = job_pop_response.r2_upload

            assert r2_url is not None

            async with aiohttp_session.put(
                yarl.URL(r2_url, encoded=True),
                data=fake_image_bytes,
                skip_auto_headers=["content-type"],
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                assert response.status == 200

            assert job_pop_response.ids is not None
            assert len(job_pop_response.ids) == 1

            job_submit_request = ImageGenerationJobSubmitRequest(
                id=job_pop_response.ids[0],
                state=GENERATION_STATE.ok,
                generation="R2",
                seed="1312",
            )

            job_submit_response = await horde_client_session.submit_request(
                job_submit_request,
                job_submit_request.get_default_success_response_type(),
            )

            assert isinstance(job_submit_response, JobSubmitResponse)
            assert job_submit_response.reward is not None and job_submit_response.reward > 0

            break

    @pytest.mark.api_side_ci
    @pytest.mark.asyncio
    async def test_basic_image_roundtrip(self, simple_image_gen_request: ImageGenerateAsyncRequest) -> None:
        aiohttp_session = aiohttp.ClientSession()
        horde_client_session = AIHordeAPIAsyncClientSession(aiohttp_session)

        async with aiohttp_session, horde_client_session:
            simple_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)

            await self.fake_worker_checkin(aiohttp_session, horde_client_session, simple_image_gen_request)

            image_gen_task = asyncio.create_task(simple_client.image_generate_request(simple_image_gen_request))

            fake_worker_task = asyncio.create_task(
                self.fake_worker(
                    aiohttp_session,
                    horde_client_session,
                    simple_image_gen_request,
                ),
            )

            await asyncio.gather(image_gen_task, fake_worker_task)

            image_gen_response, job_id = image_gen_task.result()

            assert isinstance(image_gen_response, ImageGenerateStatusResponse)
            assert isinstance(job_id, JobID)

            assert len(image_gen_response.generations) == 1

            generation = image_gen_response.generations[0]
            assert generation.seed == "1312"
            assert generation.img is not None
            assert not generation.gen_metadata

            assert generation.censored is False
