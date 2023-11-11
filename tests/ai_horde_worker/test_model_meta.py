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


@pytest.fixture(scope="session")
def image_model_load_resolver() -> ImageModelLoadResolver:
    return ImageModelLoadResolver(ModelReferenceManager())


def test_image_model_load_resolver_all(image_model_load_resolver: ImageModelLoadResolver) -> None:
    all_model_names = image_model_load_resolver.resolve_all_model_names()

    assert len(all_model_names) > 0


def test_image_model_load_resolver_top_n(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: StatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_top_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 1


def test_image_model_top_10(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: StatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_top_n_model_names(
        10,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 10


def test_image_model_load_resolver_bottom_n(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: StatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_bottom_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 1


def test_image_model_load_resolver_bottom_10(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: StatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_bottom_n_model_names(
        10,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 10


def test_image_model_load_resolver_multiple_instructions(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["top 1", "bottom 1"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) == 2


def test_image_models_unique_results_only(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["top 1000", "bottom 1000"],
        AIHordeAPIManualClient(),
    )
    all_model_names = image_model_load_resolver.resolve_all_model_names()

    assert len(resolved_model_names) >= (len(all_model_names) - 1)  # FIXME: -1 is to account for SDXL beta
