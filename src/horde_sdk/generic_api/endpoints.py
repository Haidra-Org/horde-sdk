import functools
import urllib.parse


def url_with_path(
    *,
    base_url: str,
    path: str,
) -> str:
    """Returns the combined baseURL and endpoint path. Cached for a marginal performance boost.

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
        # TODO why does the decorator break the pylance lang server?
        # TODO this sub def side steps intellisense not working, but doesn't feel right
        parsedURL = urllib.parse.urlparse(base_url)
        if not parsedURL.scheme:
            raise ValueError(f"Missing URL scheme (e.g., http, https)!\n  Is baseURL valid? baseURL: {base_url}")
        return urllib.parse.urljoin(base_url, path)

    return _shadowed_cached_func(base_url=base_url, path=path)
