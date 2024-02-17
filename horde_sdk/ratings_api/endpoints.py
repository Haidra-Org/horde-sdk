"""Information and helper functions for URL endpoints to horde APIs."""

# TODO make RATING_API_BASE_URL a env variable?
from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH

RATING_API_BASE_URL = "https://ratings.aihorde.net/api/"


class RATING_API_ENDPOINT_SUBPATH(GENERIC_API_ENDPOINT_SUBPATH):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v1_user_check = "/v1/user/check/{user_id}"
    v1_image_ratings = "/v1/image/ratings/{image_id}"
    v1_user_validate = "/v1/user/validate/{user_id}"
    v1_user_ratings = "/v1/user/ratings/"
