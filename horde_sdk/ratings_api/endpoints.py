"""Information and helper functions for URL endpoints to horde APIs."""
from strenum import StrEnum

# TODO make RATING_API_BASE_URL a env variable?
RATING_API_BASE_URL = "https://ratings.aihorde.net/api/"


class Rating_API_URL_Literals(StrEnum):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v1_user_check = "/v1/user/check/{user_id}"
    v1_image_ratings = "/v1/image/ratings/{image_id}"
    v1_user_validate = "/v1/user/validate/{user_id}"
    v1_user_ratings = "/v1/user/ratings/"
