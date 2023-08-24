"""This module contains functions for generating API endpoints urls."""

import functools
import urllib.parse

from strenum import StrEnum


class GENERIC_API_ENDPOINT_SUBPATH(StrEnum):
    """The placeholder class, meant to extended by APIs to define the endpoint paths."""


def url_with_path(
    *,
    base_url: str,
    path: str,
) -> str:
    """Return the combined baseURL and endpoint path. Cached for a marginal performance boost.

    Args:
        path (Rating_API_URL_Literals): The API action path.
        base_url (str, optional): The internet location of the API. Defaults to RATING_API_BASE_URL.

    Raises:
        ValueError: Raised if URL seems to be invalid.

    Returns:
        str: The combined baseURL and endpoint path.
    """

    @functools.cache
    def _shadowed_cached_func(*, base_url: str, path: str) -> str:
        # This sub def is here to support intellisense for the cached function
        # VSCode doesn't seem to understand the types/parameters of cached functions
        # (perhaps for a good reason, I don't know)
        parsedURL = urllib.parse.urlparse(base_url)
        if path.startswith("/"):
            path = path[1:]
        if not parsedURL.scheme:
            raise ValueError(f"Missing URL scheme (e.g., http, https)!\n  Is baseURL valid? baseURL: {base_url}")
        return urllib.parse.urljoin(base_url, path)

    return _shadowed_cached_func(base_url=base_url, path=path)
