"""Regression checks for Swagger query parameters published by the API."""

import pytest
from pydantic import ValidationError

from horde_sdk.generic_api.utils.swagger import SwaggerEndpointMethodParameter


@pytest.mark.parametrize("item_type", ["string", "integer"])
def test_repeated_array_query_parameters(item_type: str) -> None:
    expected: list[object] = ["image", "text"] if item_type == "string" else [1, 2]
    parameter = SwaggerEndpointMethodParameter.model_validate(
        {
            "name": "filter",
            "in": "query",
            "type": "array",
            "items": {"type": item_type},
            "collectionFormat": "multi",
            "enum": expected,
        },
    )

    assert parameter.items is not None
    assert parameter.items.type_ == item_type
    assert parameter.collectionFormat == "multi"
    assert parameter.enum == expected


def test_query_parameter_enum() -> None:
    parameter = SwaggerEndpointMethodParameter.model_validate(
        {"name": "sort", "in": "query", "type": "string", "enum": ["suspicion", "last_check_in"]},
    )

    assert parameter.enum == ["suspicion", "last_check_in"]


def test_unknown_query_parameter_fields_are_still_rejected() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SwaggerEndpointMethodParameter.model_validate({"name": "filter", "in": "query", "typo": "multi"})
