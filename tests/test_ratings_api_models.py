"""Unit tests for Ratings API models."""

import pydantic
import pytest

from horde_sdk.generic_api.metadata import GenericAcceptTypes
from horde_sdk.ratings_api.apimodels import UserCheckRequest


class Test_validators:
    """If you are unfamiliar with pydantic, this may demonstrates some of the validation functionality."""

    def test_user_check_request(self) -> None:
        """Shows some of the types of data expected."""
        with pytest.raises(pydantic.ValidationError, match=r".*user_id.*"):
            UserCheckRequest(
                apikey="key",
                accept=GenericAcceptTypes.json,
                user_id="non_numeric_userid",
                divergence=3,
                minutes=180,
            )
        with pytest.raises(pydantic.ValidationError, match=r".*divergence.*"):
            UserCheckRequest(
                apikey="key",
                accept=GenericAcceptTypes.json,
                user_id="123",
                divergence=-1,
                minutes=180,
            )
        with pytest.raises(pydantic.ValidationError, match=r".*user_id.*"):
            UserCheckRequest(
                apikey="key",
                accept=GenericAcceptTypes.json,
                user_id="non_numeric_userid",  # user_id has to be a str with only numbers
                divergence=3,
                minutes=180,
            )
            UserCheckRequest(
                apikey="key",
                accept="non-enum_accept_value",
                user_id="123",
                divergence=3,
                minutes=180,
            )
