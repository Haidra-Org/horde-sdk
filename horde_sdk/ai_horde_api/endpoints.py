"""This module contains the URL endpoints for the AI Horde API."""

import os

from horde_sdk.generic_api.endpoints import GENERIC_API_ENDPOINT_SUBPATH, url_with_path

# TODO: Defer setting this?
AI_HORDE_BASE_URL = "https://aihorde.net/api/"

if os.environ.get("AI_HORDE_URL", None):
    AI_HORDE_BASE_URL = os.environ["AI_HORDE_URL"]

if os.environ.get("AI_HORDE_DEV_URL", None):
    AI_HORDE_BASE_URL = os.environ["AI_HORDE_DEV_URL"]


class AI_HORDE_API_ENDPOINT_SUBPATH(GENERIC_API_ENDPOINT_SUBPATH):
    """The URL actions 'paths' to the endpoints.

    Includes the find/replace strings in brackets for path (non-query) variables.
    """

    swagger = "/swagger.json"

    # Note that the leading slash is included for consistency with the swagger docs,
    # but it is dropped when the URL is actually constructed (see `url_with_path` in `horde_sdk.generic_api.endpoints`)
    v2_stats_img_models = "/v2/stats/img/models"
    v2_stats_img_totals = "/v2/stats/img/totals"
    v2_stats_text_models = "/v2/stats/text/models"
    v2_stats_text_totals = "/v2/stats/text/totals"

    v2_generate_async = "/v2/generate/async"

    v2_generate_pop = "/v2/generate/pop"
    v2_generate_pop_multi = "/v2/generate/pop_multi"
    v2_generate_submit = "/v2/generate/submit"

    # Note that `{id}`` (or any variable wrapped in curly braces) is dynamically replaced with the appropriate value
    # when a request being prepared for submission. The fields that are replaced are defined in the `AIHordePathData`
    # class in `metadata.py`.
    #
    # See `horde_shared_models\generic_api\generic_client.py` for the actual replacement

    v2_generate_check = "/v2/generate/check/{id}"
    v2_generate_status = "/v2/generate/status/{id}"

    v2_generate_text_async = "/v2/generate/text/async"
    v2_generate_text_submit = "/v2/generate/text/submit"

    v2_generate_text_pop = "/v2/generate/text/pop"
    v2_generate_text_status = "/v2/generate/text/status/{id}"

    v2_generate_rate_id = "/v2/generate/rate/{id}"

    v2_interrogate_async = "/v2/interrogate/async"
    v2_interrogate_status = "/v2/interrogate/status/{id}"
    v2_interrogate_pop = "/v2/interrogate/pop"
    v2_interrogate_submit = "/v2/interrogate/submit"

    v2_kudos_award = "/v2/kudos/award"
    v2_kudos_transfer = "/v2/kudos/transfer"

    v2_sharedkeys_create = "/v2/sharedkeys"
    v2_sharedkeys = "/v2/sharedkeys/{sharedkey_id}"

    v2_status_heartbeat = "/v2/status/heartbeat"
    v2_status_modes = "/v2/status/modes"
    v2_status_news = "/v2/status/news"

    v2_status_models_all = "/v2/status/models"
    v2_status_models_single = "/v2/status/models/{model_name}"

    v2_status_performance = "/v2/status/performance"

    v2_teams_all = "/v2/teams"
    v2_teams = "/v2/teams/{team_id}"

    v2_find_user = "/v2/find_user"
    """Note that this is an API key lookup, not a user ID lookup."""

    v2_users_all = "/v2/users"
    v2_users_single = "/v2/users/{user_id}"

    v2_workers_all = "/v2/workers"
    v2_workers_single = "/v2/workers/{worker_id}"
    v2_workers_single_name = "/v2/workers/name/{worker_name}"

    v2_filters = "/v2/filters"
    v2_filters_regex = "/v2/filters/regex"
    v2_filters_regex_single = "/v2/filters/{filter_id}"

    v2_operations_block_worker_ipaddr_single = "/v2/operations/block_worker_ipaddr/{worker_id}"
    v2_operations_ipaddr = "/v2/operations/ipaddr"
    v2_operations_ipaddr_single = "/v2/operations/ipaddr/{ipaddr}"

    v2_documents_privacy = "/v2/documents/privacy"
    v2_documents_sponsors = "/v2/documents/sponsors"
    vs_documents_terms = "/v2/documents/terms"


def get_ai_horde_swagger_url() -> str:
    """Get the URL for the AI Horde API swagger docs."""
    return url_with_path(
        base_url=AI_HORDE_BASE_URL,
        path=AI_HORDE_API_ENDPOINT_SUBPATH.swagger,
    )
