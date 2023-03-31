"""Information and helper functions for URL endpoints to horde APIs."""
import functools
import urllib.parse
from enum import Enum

# TODO make RATING_API_BASE_URL a env variable?
RATING_API_BASE_URL = "https://ratings.aihorde.net/api/"


class Rating_API_URL_Literals(str, Enum):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v1_user_check = "v1/user/check/{user_id}"
    v1_image_ratings = "v1/image/ratings/{image_id}"
    v1_user_validate = "v1/user/validate/{user_id}"
    v1_user_ratings = "v1/user/ratings/"


def URLWithPath(*, baseURL: str = RATING_API_BASE_URL, path: Rating_API_URL_Literals) -> str:
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
    def _shadowedCachedFunc(*, baseURL: str, path: Rating_API_URL_Literals) -> str:
        # TODO why does the decorator break the pylance lang server?
        # TODO this sub def side steps intellisense not working, but doesn't feel right
        parsedURL = urllib.parse.urlparse(baseURL)
        if not parsedURL.scheme:
            raise ValueError(f"Missing URL scheme (e.g., http, https)!\n  Is baseURL valid? baseURL: {baseURL}")
        return urllib.parse.urljoin(baseURL, path)

    return _shadowedCachedFunc(baseURL=baseURL, path=path)
