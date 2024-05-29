import aiohttp
import pytest

from horde_sdk import RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
)
from horde_sdk.ai_horde_api.apimodels._stats import (
    ImageStatsModelsRequest,
    ImageStatsModelsResponse,
    ImageStatsModelsTotalRequest,
    ImageStatsModelsTotalResponse,
    SinglePeriodImgStat,
    TextStatsModelResponse,
    TextStatsModelsRequest,
    TextStatsModelsTotalRequest,
    TextStatsModelsTotalResponse,
)


class TestAIHordeStats:

    @pytest.mark.asyncio
    async def test_get_image_stats_models(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = ImageStatsModelsRequest()
            response = await client.submit_request(
                request,
                expected_response_type=ImageStatsModelsResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, ImageStatsModelsResponse)
            assert isinstance(response.day, dict)
            assert isinstance(response.month, dict)
            assert isinstance(response.total, dict)

            request_known = ImageStatsModelsRequest(model_state="known")
            response_known = await client.submit_request(
                request_known,
                expected_response_type=ImageStatsModelsResponse,
            )

            if isinstance(response_known, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_known}")

            assert response_known is not None
            assert isinstance(response_known, ImageStatsModelsResponse)
            assert isinstance(response_known.day, dict)
            assert isinstance(response_known.month, dict)
            assert isinstance(response_known.total, dict)

            request_custom = ImageStatsModelsRequest(model_state="custom")
            response_custom = await client.submit_request(
                request_custom,
                expected_response_type=ImageStatsModelsResponse,
            )

            if isinstance(response_custom, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_custom}")

            assert response_custom is not None
            assert isinstance(response_custom, ImageStatsModelsResponse)
            assert isinstance(response_custom.day, dict)
            assert isinstance(response_custom.month, dict)
            assert isinstance(response_custom.total, dict)

            if (not isinstance(response, ImageStatsModelsResponse) or response.month is None) or (
                not isinstance(response_custom, ImageStatsModelsResponse) or response_custom.month is None
            ):
                pytest.skip("No data to compare. Is this a development environment?")
            else:
                assert len(response.month) != len(response_custom.month)

    @pytest.mark.asyncio
    async def test_get_image_stats_models_total(self) -> None:
        request = ImageStatsModelsTotalRequest()
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            response = await client.submit_request(
                request,
                expected_response_type=ImageStatsModelsTotalResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, ImageStatsModelsTotalResponse)
            assert isinstance(response.day, SinglePeriodImgStat)
            assert isinstance(response.hour, SinglePeriodImgStat)
            assert isinstance(response.minute, SinglePeriodImgStat)
            assert isinstance(response.month, SinglePeriodImgStat)
            assert isinstance(response.total, SinglePeriodImgStat)
            assert response.total.images is not None
            assert response.total.ps is not None
            assert response.total.mps is not None

    @pytest.mark.asyncio
    async def test_get_text_stats_models(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = TextStatsModelsRequest()
            response = await client.submit_request(
                request,
                expected_response_type=TextStatsModelResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, TextStatsModelResponse)
            assert isinstance(response.day, dict)
            assert isinstance(response.month, dict)
            assert isinstance(response.total, dict)

    @pytest.mark.asyncio
    async def test_get_text_stats_models_total(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = TextStatsModelsTotalRequest()
            response = await client.submit_request(
                request,
                expected_response_type=TextStatsModelsTotalResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, TextStatsModelsTotalResponse)
            assert isinstance(response.minute, dict)
            assert isinstance(response.hour, dict)
            assert isinstance(response.day, dict)
            assert isinstance(response.month, dict)
            assert isinstance(response.total, dict)
