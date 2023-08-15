import pytest
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import StatsImageModelsRequest, StatsModelsResponse, StatsModelsTimeframe
from horde_sdk.ai_horde_worker.model_meta import ImageModelLoadResolver
from horde_sdk.generic_api.apimodels import RequestErrorResponse


@pytest.fixture(scope="session")
def stats_response() -> StatsModelsResponse:
    client = AIHordeAPIManualClient()

    stats_response = client.submit_request(StatsImageModelsRequest(), StatsModelsResponse)

    if isinstance(stats_response, RequestErrorResponse):
        raise Exception(f"Request error: {stats_response.message}. object_data: {stats_response.object_data}")

    return stats_response


def test_image_model_load_resolver_init() -> None:
    model_reference_manager = ModelReferenceManager()
    ImageModelLoadResolver(model_reference_manager)


def test_image_model_load_resolver_all() -> None:
    model_reference_manager = ModelReferenceManager()
    image_model_load_resolver = ImageModelLoadResolver(model_reference_manager)
    all_model_names = image_model_load_resolver.resolve_all_model_names()

    assert len(all_model_names) > 0


def test_image_model_load_resolver_top_n(stats_response: StatsModelsResponse) -> None:
    model_reference_manager = ModelReferenceManager()
    image_model_load_resolver = ImageModelLoadResolver(model_reference_manager)

    all_model_names = image_model_load_resolver.resolve_top_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(all_model_names) == 1


def test_image_model_load_resolver_bottom_n(stats_response: StatsModelsResponse) -> None:
    model_reference_manager = ModelReferenceManager()
    image_model_load_resolver = ImageModelLoadResolver(model_reference_manager)

    all_model_names = image_model_load_resolver.resolve_bottom_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(all_model_names) == 1
