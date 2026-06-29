"""Network-free tests for ``ImageModelLoadResolver`` dependency injection.

These deliberately live outside ``*api_calls.py`` so the suite's network-test gate does not skip them:
the whole point is that an injected manager keeps the resolver off the network.
"""

from unittest.mock import MagicMock

import pytest
from horde_model_reference.meta_consts import MODEL_REFERENCE_CATEGORY
from horde_model_reference.model_reference_manager import ModelReferenceManager

from horde_sdk.worker.model_meta import ImageModelLoadResolver


def test_injected_reference_manager_is_used_without_network() -> None:
    """An injected manager is read directly, with no self-built (network-fetching) manager.

    Constructing the resolver with a caller-owned manager must not touch the event loop or the PRIMARY
    API: it should read the records the injected manager already holds. This is what lets a process that
    must not stall on the network (or that already owns a manager) reuse it.
    """
    fake_manager = MagicMock(spec=ModelReferenceManager)
    fake_manager.get_all_model_references.return_value = {
        MODEL_REFERENCE_CATEGORY.image_generation: {"ModelA": object(), "ModelB": object()},
    }

    resolver = ImageModelLoadResolver(model_reference_manager=fake_manager)

    assert resolver._model_reference_manager is fake_manager
    assert resolver.resolve_all_model_names() == {"ModelA", "ModelB"}


def _resolver_with_references(references: dict[MODEL_REFERENCE_CATEGORY, object]) -> ImageModelLoadResolver:
    """Build a resolver over an injected manager returning exactly ``references``."""
    fake_manager = MagicMock(spec=ModelReferenceManager)
    fake_manager.get_all_model_references.return_value = references
    return ImageModelLoadResolver(model_reference_manager=fake_manager)


@pytest.mark.parametrize(
    "references",
    [
        pytest.param({MODEL_REFERENCE_CATEGORY.image_generation: None}, id="present-but-none"),
        pytest.param({MODEL_REFERENCE_CATEGORY.blip: {"BLIP": object()}}, id="category-absent"),
        pytest.param({}, id="empty-mapping"),
    ],
)
def test_resolvers_handle_missing_image_generation_reference(
    references: dict[MODEL_REFERENCE_CATEGORY, object],
) -> None:
    """An unavailable image_generation reference yields empty sets, never a KeyError.

    A reference manager may map the category to ``None`` *or* omit the key entirely (the category failed
    to load). Every resolver method reads ``all_model_references`` for the image_generation category, so
    each must tolerate both shapes rather than indexing the key unguarded.
    """
    resolver = _resolver_with_references(references)

    assert resolver.resolve_all_model_names() == set()
    assert resolver.resolve_all_sfw_model_names() == set()
    assert resolver.resolve_all_nsfw_model_names() == set()
    assert resolver.resolve_all_inpainting_models() == set()
    assert resolver.resolve_all_models_of_baseline("stable_diffusion_1") == set()
