import aiohttp
import pytest

from horde_sdk import RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import (
    AIHordeAPIAsyncClientSession,
)
from horde_sdk.ai_horde_api.apimodels._status import (
    ActiveModel,
    AIHordeHeartbeatRequest,
    AIHordeHeartbeatResponse,
    HordePerformanceRequest,
    HordePerformanceResponse,
    HordeStatusModelsAllRequest,
    HordeStatusModelsAllResponse,
    HordeStatusModelsSingleRequest,
    HordeStatusModelsSingleResponse,
    Newspiece,
    NewsRequest,
    NewsResponse,
)


class TestAIHordeStatus:

    @pytest.mark.asyncio
    async def test_ai_horde_heartbeat(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = AIHordeHeartbeatRequest()
            response = await client.submit_request(
                request,
                expected_response_type=AIHordeHeartbeatResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, AIHordeHeartbeatResponse)

    @pytest.mark.asyncio
    async def test_horde_performance(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = HordePerformanceRequest()
            response = await client.submit_request(
                request,
                expected_response_type=HordePerformanceResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, HordePerformanceResponse)

    @pytest.mark.asyncio
    async def test_horde_status_models_all(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = HordeStatusModelsAllRequest()
            response = await client.submit_request(
                request,
                expected_response_type=HordeStatusModelsAllResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, HordeStatusModelsAllResponse)
            assert len(response.root) > 0

            for model in response:
                assert isinstance(model, ActiveModel)
                assert model.type_ == "image"

            text_request = HordeStatusModelsAllRequest(type="text")
            text_response = await client.submit_request(
                text_request,
                expected_response_type=HordeStatusModelsAllResponse,
            )

            if isinstance(text_response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {text_response}")

            assert text_response is not None
            assert isinstance(text_response, HordeStatusModelsAllResponse)
            assert len(text_response.root) > 0

            for model in text_response:
                assert isinstance(model, ActiveModel)
                assert model.type_ == "text"

    @pytest.mark.asyncio
    async def test_horde_status_models_single_image(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = HordeStatusModelsAllRequest()
            response = await client.submit_request(
                request,
                expected_response_type=HordeStatusModelsAllResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, HordeStatusModelsAllResponse)
            assert len(response.root) > 0

            for model in response:
                assert isinstance(model, ActiveModel)
                assert model.type_ == "image"

            # Pick two random models
            import random

            random_model_1 = random.choice(response.root)
            random_model_2 = random.choice(response.root)

            request_single_1 = HordeStatusModelsSingleRequest(model_name=random_model_1.name)
            response_single_1 = await client.submit_request(
                request_single_1,
                expected_response_type=HordeStatusModelsSingleResponse,
            )

            if isinstance(response_single_1, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_single_1}")

            assert response_single_1 is not None
            assert isinstance(response_single_1, HordeStatusModelsSingleResponse)
            assert response_single_1[0].name == random_model_1.name
            assert response_single_1[0].type_ == "image"

            request_single_2 = HordeStatusModelsSingleRequest(model_name=random_model_2.name)
            response_single_2 = await client.submit_request(
                request_single_2,
                expected_response_type=HordeStatusModelsSingleResponse,
            )

            if isinstance(response_single_2, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_single_2}")

            assert response_single_2 is not None
            assert isinstance(response_single_2, HordeStatusModelsSingleResponse)
            assert response_single_2[0].name == random_model_2.name
            assert response_single_2[0].type_ == "image"

    @pytest.mark.asyncio
    async def test_horde_status_models_single_text(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = HordeStatusModelsAllRequest(type="text")
            response = await client.submit_request(
                request,
                expected_response_type=HordeStatusModelsAllResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, HordeStatusModelsAllResponse)
            assert len(response.root) > 0

            for model in response:
                assert isinstance(model, ActiveModel)
                assert model.type_ == "text"

            # Pick two random models
            import random

            random_model_1 = random.choice(response.root)
            random_model_2 = random.choice(response.root)

            import urllib.parse

            assert random_model_1.name is not None
            model_1_name_double_encoded = urllib.parse.quote(random_model_1.name, safe="")
            model_1_name_double_encoded = urllib.parse.quote(model_1_name_double_encoded, safe="")

            request_single_1 = HordeStatusModelsSingleRequest(model_name=model_1_name_double_encoded)
            response_single_1 = await client.submit_request(
                request_single_1,
                expected_response_type=HordeStatusModelsSingleResponse,
            )

            if isinstance(response_single_1, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_single_1}")

            assert response_single_1 is not None
            assert isinstance(response_single_1, HordeStatusModelsSingleResponse)
            if len(response_single_1.root) == 0:
                pytest.skip("No data to compare. Is this a development environment?")
            else:
                assert response_single_1[0].name == random_model_1.name
                assert response_single_1[0].type_ == "text"

            assert random_model_2.name is not None
            model_2_name_double_encoded = urllib.parse.quote(random_model_2.name, safe="")
            model_2_name_double_encoded = urllib.parse.quote(model_2_name_double_encoded, safe="")

            request_single_2 = HordeStatusModelsSingleRequest(model_name=model_2_name_double_encoded)
            response_single_2 = await client.submit_request(
                request_single_2,
                expected_response_type=HordeStatusModelsSingleResponse,
            )

            if isinstance(response_single_2, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response_single_2}")

            assert response_single_2 is not None
            assert isinstance(response_single_2, HordeStatusModelsSingleResponse)
            if len(response_single_2.root) == 0:
                pytest.skip("No data to compare. Is this a development environment?")
            else:
                assert response_single_2[0].name == random_model_2.name
                assert response_single_2[0].type_ == "text"

    @pytest.mark.asyncio
    async def test_news(self) -> None:
        async with (
            aiohttp.ClientSession() as aiohttp_session,
            AIHordeAPIAsyncClientSession(aiohttp_session=aiohttp_session) as client,
        ):
            request = NewsRequest()
            response = await client.submit_request(
                request,
                expected_response_type=NewsResponse,
            )

            if isinstance(response, RequestErrorResponse):
                raise AssertionError(f"Request failed: {response}")

            assert response is not None
            assert isinstance(response, NewsResponse)
            assert len(response.root) > 0

            for news in response:
                assert isinstance(news, Newspiece)
                assert news.date_published is not None
                assert news.newspiece is not None
