"""Network-free tests for ``ImageModelLoadResolver`` dependency injection.

These deliberately live outside ``*api_calls.py`` so the suite's network-test gate does not skip them:
the whole point is that an injected manager keeps the resolver off the network.
"""

from unittest.mock import MagicMock

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
