from strenum import StrEnum

AI_HORDE_BASE_URL = "https://stablehorde.net/api/"


class AI_HORDE_API_URL_Literals(StrEnum):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v2_stats_img_models = "v2/stats/img/models"
    v2_stats_img_totals = "v2/stats/img/totals"
    v2_stats_text_models = "v2/stats/text/models"
    v2_stats_text_totals = "v2/stats/text/totals"

    v2_generate_async = "v2/generate/async"

    v2_generate_pop = "v2/generate/pop"
