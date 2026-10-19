"""Boolean query values must be accepted by both HTTP clients."""

from typing import override

import pytest
from yarl import URL

from horde_sdk.ai_horde_api.apimodels import AllStylesImageRequest
from horde_sdk.generic_api.generic_clients import GenericHordeAPIManualClient
from horde_sdk.generic_api.metadata import GenericQueryFields


class _QueryFields(GenericQueryFields):
    enabled = "enabled"


class _BooleanQueryRequest(AllStylesImageRequest):
    enabled: bool
    body_flag: bool

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return [*super().get_query_fields(), "enabled"]


@pytest.mark.parametrize("value", [True, False])
@pytest.mark.parametrize("query_fields", [GenericQueryFields, _QueryFields])
def test_boolean_queries_are_encoded_without_changing_payload_booleans(
    value: bool,
    query_fields: type[GenericQueryFields],
) -> None:
    client = GenericHordeAPIManualClient(query_fields=query_fields)
    request = _BooleanQueryRequest(enabled=value, body_flag=value)
    parsed = client._validate_and_prepare_request(request)

    query = URL(parsed.endpoint_no_query).with_query(parsed.request_queries).query
    assert query["enabled"] == ("true" if value else "false")
    assert parsed.request_body is not None
    assert parsed.request_body["body_flag"] is value
