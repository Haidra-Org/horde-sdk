"""Offline behavior of source snippets embedded in the documentation."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import PIL.Image
import pytest

from examples.docs import client_recipes, first_image
from horde_sdk.ai_horde_api.apimodels import AlchemyCaptionResult


class FakeSyncClient:
    def image_generate_request_dry_run(self, request: Any) -> SimpleNamespace:
        assert request.dry_run is True
        return SimpleNamespace(kudos=2.5)

    def image_generate_request(self, request: Any) -> tuple[SimpleNamespace, str]:
        assert request.dry_run is False
        return SimpleNamespace(generations=[SimpleNamespace(id_="generation")]), "request"

    def download_image_from_generation(self, generation: Any) -> PIL.Image.Image:
        assert generation.id_ == "generation"
        return PIL.Image.new("RGB", (2, 2), "blue")


def test_first_image_dry_run_and_live_file_are_offline_testable(tmp_path: Path) -> None:
    client = FakeSyncClient()
    output = tmp_path / "result.webp"

    assert first_image.estimate(client) == 2.5  # type: ignore[arg-type]
    assert first_image.generate(client, output) == output  # type: ignore[arg-type]
    assert output.is_file()


def test_documented_request_builders_validate_locally() -> None:
    image = client_recipes.image_request()
    text = client_recipes.text_request("example/model")

    assert image.params is not None and image.params.width == 512 and image.params.n == 1
    assert image.nsfw is False and image.censor_nsfw is True
    assert text.models == ["example/model"]
    assert text.params is not None and text.params.max_length == 80


class FakeRecipeSyncClient:
    def image_generate_request(self, request: Any) -> tuple[SimpleNamespace, str]:
        return SimpleNamespace(generations=[SimpleNamespace(id_="generation")]), "request"

    def download_image_from_generation(self, generation: Any) -> PIL.Image.Image:
        return PIL.Image.new("RGB", (2, 2), "green")

    def text_generate_request(self, request: Any) -> tuple[SimpleNamespace, str]:
        return SimpleNamespace(generations=[SimpleNamespace(text="A result")]), "request"

    def alchemy_request(self, request: Any) -> tuple[SimpleNamespace, str]:
        result = AlchemyCaptionResult(caption="A caption")
        return SimpleNamespace(forms=[SimpleNamespace(result=result)]), "request"


def test_sync_documentation_recipes_use_typed_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_recipes, "AIHordeAPISimpleClient", FakeRecipeSyncClient)

    assert client_recipes.generate_image()
    assert client_recipes.generate_text("example/model") == "A result"
    assert client_recipes.caption_image("https://example.test/image.webp") == "A caption"


class FakeAsyncClient:
    def __init__(self, **_kwargs: Any) -> None:
        pass

    async def image_generate_request(self, request: Any) -> tuple[SimpleNamespace, str]:
        return SimpleNamespace(generations=[SimpleNamespace(id_="generation")]), "request"

    async def download_image_from_generation(self, generation: Any) -> tuple[PIL.Image.Image, str]:
        return PIL.Image.new("RGB", (2, 2), "red"), "generation"


@pytest.mark.asyncio
async def test_async_documentation_recipe_closes_its_http_session(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client_recipes, "AIHordeAPIAsyncSimpleClient", FakeAsyncClient)

    assert await client_recipes.generate_image_async()
