"""Tests for the `horde_sdk.generic_api.utils` module  ."""

from horde_sdk.generic_api.endpoints import url_with_path


def test_url_with_path() -> None:
    """Test that `url_with_path()` returns a valid URL."""
    example_url = "https://example.com/api/"
    example_path = "/example/path"
    example_path_no_leading_slash = "example/path"
    expected_url = "https://example.com/api/example/path"
    assert url_with_path(base_url=example_url, path=example_path) == expected_url
    assert url_with_path(base_url=example_url, path=example_path_no_leading_slash) == expected_url
