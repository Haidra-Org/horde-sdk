import functools
import urllib.parse


def URLWithPath(*, baseURL: str, path: str) -> str:
    """Returns the combined baseURL and endpoint path.

    Args:
        path (Rating_API_URL_Literals): The API action path.
        baseURL (str, optional): The internet location of the API. Defaults to RATING_API_BASE_URL.

    Raises:
        ValueError: Raised if URL seems to be invalid.

    Returns:
        str: The combined baseURL and endpoint path.
    """

    @functools.cache
    def _shadowedCachedFunc(*, baseURL: str, path: str) -> str:
        # TODO why does the decorator break the pylance lang server?
        # TODO this sub def side steps intellisense not working, but doesn't feel right
        parsedURL = urllib.parse.urlparse(baseURL)
        if not parsedURL.scheme:
            raise ValueError(f"Missing URL scheme (e.g., http, https)!\n  Is baseURL valid? baseURL: {baseURL}")
        return urllib.parse.urljoin(baseURL, path)

    return _shadowedCachedFunc(baseURL=baseURL, path=path)
