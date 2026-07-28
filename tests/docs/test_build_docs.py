"""Tests for deterministic SDK documentation generation."""

from __future__ import annotations

import importlib.util
import sys
from enum import IntEnum, StrEnum
from pathlib import Path
from typing import Any, cast

MODULE_PATH = Path(__file__).parents[2] / "docs" / "build_docs.py"
SPEC = importlib.util.spec_from_file_location("build_docs", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
build_docs = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_docs
SPEC.loader.exec_module(build_docs)


def test_manifest_includes_advanced_surfaces_and_excludes_internals() -> None:
    assert build_docs.module_is_included("horde_sdk.ai_horde_api.apimodels.generate.async_")
    assert build_docs.module_is_included("horde_sdk.worker.chaining.flow")
    assert build_docs.module_is_included("horde_sdk.utils.image_utils")
    assert not build_docs.module_is_included("horde_sdk._telemetry.metrics")
    assert not build_docs.module_is_included("horde_sdk.scripts.write_all_payload_examples_for_tests")
    assert not build_docs.module_is_included("horde_sdk.generic_api._reflection")


def test_generated_tree_is_deterministic_and_omits_facades_from_module_page(tmp_path: Path) -> None:
    code_root = tmp_path / "horde_sdk"
    module = code_root / "worker" / "jobs.py"
    module.parent.mkdir(parents=True)
    module.write_text(
        '"""Jobs."""\n\nclass ImageWorkerJob:\n    """An image job."""\n\ndef helper() -> None:\n    """Help."""\n',
        encoding="utf-8",
    )
    api_root = tmp_path / "docs" / "reference" / "api" / "horde_sdk"
    expanded = ("horde_sdk.worker.jobs.ImageWorkerJob",)

    first = build_docs.expected_api_pages(code_root, tmp_path, api_root, expanded)
    second = build_docs.expected_api_pages(code_root, tmp_path, api_root, expanded)

    assert first == second
    module_page = first[api_root / "worker" / "jobs.md"]
    assert "        - helper" in module_page
    assert "        - ImageWorkerJob" not in module_page
    assert api_root / "worker" / "jobs" / "ImageWorkerJob.md" in first
    assert "inherited_members: true" in first[api_root / "worker" / "jobs" / "ImageWorkerJob.md"]


class Method(StrEnum):
    GET = "GET"
    DELETE = "DELETE"


class Status(IntEnum):
    OK = 200


class Response:
    pass


class GetRequest:
    @classmethod
    def get_api_endpoint_subpath(cls) -> str:
        return "/v2/example"

    @classmethod
    def get_http_method(cls) -> Method:
        return Method.GET

    @classmethod
    def get_success_status_response_pairs(cls) -> dict[Status, type[Response]]:
        return {Status.OK: Response}


class DeleteRequest(GetRequest):
    @classmethod
    def get_http_method(cls) -> Method:
        return Method.DELETE


def test_endpoint_rows_keep_methods_distinct_for_the_same_path_and_status() -> None:
    request_types = cast(Any, [DeleteRequest, GetRequest])
    rows = build_docs.collect_endpoint_rows(request_types)

    assert [(row.endpoint, row.method, row.status) for row in rows] == [
        ("/v2/example", "DELETE", 200),
        ("/v2/example", "GET", 200),
    ]
