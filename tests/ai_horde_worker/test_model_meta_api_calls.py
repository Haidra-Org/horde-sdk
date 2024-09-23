import pytest
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageStatsModelsRequest, ImageStatsModelsResponse, StatsModelsTimeframe
from horde_sdk.ai_horde_worker.model_meta import ImageModelLoadResolver
from horde_sdk.generic_api.apimodels import RequestErrorResponse


@pytest.fixture(scope="session")
def stats_response() -> ImageStatsModelsResponse:
    client = AIHordeAPIManualClient()

    stats_response = client.submit_request(ImageStatsModelsRequest(), ImageStatsModelsResponse)

    if isinstance(stats_response, RequestErrorResponse):
        raise Exception(f"Request error: {stats_response.message}. object_data: {stats_response.object_data}")

    return stats_response


@pytest.fixture(scope="session")
def image_model_load_resolver() -> ImageModelLoadResolver:
    return ImageModelLoadResolver(ModelReferenceManager())


def test_image_model_load_resolver_all(image_model_load_resolver: ImageModelLoadResolver) -> None:
    all_model_names = image_model_load_resolver.resolve_all_model_names()

    assert len(all_model_names) > 0

    import os

    os.environ["AI_HORDE_MODEL_META_LARGE_MODELS"] = "true"

    all_model_names_with_large = image_model_load_resolver.resolve_all_model_names()

    del os.environ["AI_HORDE_MODEL_META_LARGE_MODELS"]

    assert len(all_model_names_with_large) > len(all_model_names)


def test_image_model_load_resolver_top_n(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: ImageStatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_top_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 1


def test_image_model_top_10(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: ImageStatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_top_n_model_names(
        10,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 10


def test_image_model_load_resolver_bottom_n(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: ImageStatsModelsResponse,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_bottom_n_model_names(
        1,
        stats_response,
        timeframe=StatsModelsTimeframe.month,
    )

    assert len(resolved_model_names) == 1


def test_image_model_load_resolver_bottom_10(
    image_model_load_resolver: ImageModelLoadResolver,
    stats_response: ImageStatsModelsResponse,
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


def test_image_model_load_resolved_all_sd15(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all sd15"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0

    for model_name in resolved_model_names:
        assert "SDXL" not in model_name

    assert "Deliberate" in resolved_model_names


def test_image_model_load_resolved_all_sd21(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all sd21"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0

    for model_name in resolved_model_names:
        assert "SDXL" not in model_name
        assert model_name != "Deliberate"


def test_image_model_load_resolved_all_sdxl(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all sdxl"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0
    assert "AlbedoBase XL (SDXL)" in resolved_model_names


def test_image_model_load_resolved_all_inpainting(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all inpainting"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0
    assert any("inpainting" in model_name.lower() for model_name in resolved_model_names)


def test_image_model_load_resolved_sfw_nsfw(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all sfw"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0
    assert not any("urpm" in model_name.lower() for model_name in resolved_model_names)

    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["all nsfw"],
        AIHordeAPIManualClient(),
    )

    assert len(resolved_model_names) > 0
    assert any("urpm" in model_name.lower() for model_name in resolved_model_names)


def test_image_models_unique_results_only(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_meta_instructions(
        ["top 1000", "bottom 1000"],
        AIHordeAPIManualClient(),
    )
    all_model_names = image_model_load_resolver.resolve_all_model_names()

    assert len(resolved_model_names) >= (len(all_model_names) - 1)  # FIXME: -1 is to account for SDXL beta

    import os

    os.environ["AI_HORDE_MODEL_META_LARGE_MODELS"] = "true"

    resolved_models_names_with_large = image_model_load_resolver.resolve_meta_instructions(
        ["top 1000", "bottom 1000"],
        AIHordeAPIManualClient(),
    )

    del os.environ["AI_HORDE_MODEL_META_LARGE_MODELS"]

    assert len(resolved_models_names_with_large) >= len(resolved_model_names)


def test_resolve_all_models_of_baseline(
    image_model_load_resolver: ImageModelLoadResolver,
) -> None:
    resolved_model_names = image_model_load_resolver.resolve_all_models_of_baseline("stable_diffusion_xl")

    assert len(resolved_model_names) > 0
