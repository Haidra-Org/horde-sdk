"""Tests for the host-aware Zensical build wrapper."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[2] / "docs" / "build_site.py"
SPEC = importlib.util.spec_from_file_location("build_site", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
build_site = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_site)


def test_canonical_url_requires_absolute_http_and_adds_trailing_slash() -> None:
    assert build_site.canonical_url("https://docs.example.test/en/latest") == ("https://docs.example.test/en/latest/")
    try:
        build_site.canonical_url("relative/path")
    except argparse.ArgumentTypeError:
        pass
    else:
        raise AssertionError("relative canonical URL was accepted")


def test_temporary_config_changes_only_site_url(tmp_path: Path) -> None:
    config = tmp_path / "zensical.toml"
    config.write_text('[project]\nsite_name = "Example"\nsite_url = "https://old.example/"\n', encoding="utf-8")
    original_root = build_site.PROJECT_ROOT
    original_config = build_site.CONFIG_PATH
    temporary: Path | None = None
    build_site.PROJECT_ROOT = tmp_path
    build_site.CONFIG_PATH = config
    try:
        temporary = build_site.temporary_config("https://new.example/en/stable/")
        rendered = temporary.read_text(encoding="utf-8")
        assert 'site_name = "Example"' in rendered
        assert 'site_url = "https://new.example/en/stable/"' in rendered
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        build_site.PROJECT_ROOT = original_root
        build_site.CONFIG_PATH = original_config
