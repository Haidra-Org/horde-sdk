from enum import Enum

AI_HORDE_BASE_URL = "https://stablehorde.net/api/"


class AI_HORDE_API_URL_Literals(str, Enum):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v1_stats_img_models = "v2/stats/img/models"
    v1_stats_img_totals = "v2/stats/img/totals"
    v1_stats_text_models = "v2/stats/text/models"
    v1_stats_text_totals = "v2/stats/text/totals"
