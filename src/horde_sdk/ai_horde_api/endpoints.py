from strenum import StrEnum

# AI_HORDE_BASE_URL = "https://dev.aihorde.net/api/"
AI_HORDE_BASE_URL = "http://localhost:9834/api/"


class AI_HORDE_API_URL_Literals(StrEnum):
    """The URL actions 'paths' to the endpoints. Includes find/replace strings for path (non-query) variables."""

    v2_stats_img_models = "v2/stats/img/models"
    v2_stats_img_totals = "v2/stats/img/totals"
    v2_stats_text_models = "v2/stats/text/models"
    v2_stats_text_totals = "v2/stats/text/totals"

    v2_generate_async = "v2/generate/async"

    v2_generate_pop = "v2/generate/pop"
    v2_generate_submit = "v2/generate/submit"

    # Note that `{id}`` (or any variable wrapped in curly braces) is dynamically replaced with the appropriate value
    # when a request being prepared for submission. The fields that are replaced are defined in the `GenericPathData`
    # See `horde_shared_models\generic_api\generic_client.py` for the actual replacement

    v2_generate_check = "v2/generate/check/{id}"
    v2_generate_status = "v2/generate/status/{id}"

    v2_generate_text_async = "v2/generate/text/async"
    v2_generate_text_submit = "v2/generate/text/submit"

    v2_generate_text_pop = "v2/generate/text/pop"
    v2_generate_text_status = "v2/generate/text/status/{id}"

    v2_interrogate_async = "v2/interrogate/async"
    v2_interrogate_status = "v2/interrogate/status/{id}"
    v2_interrogate_pop = "v2/interrogate/pop"
    v2_interrogate_submit = "v2/interrogate/submit"

    v2_kudos_transfer = "v2/kudos/transfer"

    v2_sharedkeys_create = "v2/sharedkeys"
    v2_sharedkeys = "v2_sharedkeys/{sharedkey_id}"

    v2_status_heartbeat = "v2/status/heartbeat"

    v2_status_models_all = "v2/status/models"
    v2_status_models = "v2/status/models/{model_id}"

    v2_status_performance = "v2/status/performance"

    v2_teams_all = "v2/teams"
    v2_teams = "v2/teams/{team_id}"

    v2_users_all = "v2/users"
    v2_users = "v2/users/{user_id}"

    v2_workers_all = "v2/workers"
    v2_workers = "v2/workers/{worker_id}"
