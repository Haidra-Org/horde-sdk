"""Unit tests for Ratings API models."""


import horde_shared_models.generic_api as generic_api
import horde_shared_models.ratings_api as ratings_api
import pydantic
import pytest


class Test_validators:
    """If you are unfamiliar with pydantic, this demonstrates some of the validation functionality."""

    def test_user_check_request(self) -> None:
        """Shows some of the types of data expected."""
        with pytest.raises(pydantic.ValidationError, match=r".*user_id.*"):
            ratings_api.UserCheckRequest(
                apikey="key",
                accept=generic_api.GenericAcceptTypes.json,
                user_id="non_numeric_userid",
                divergence=3,
                minutes=180,
            )
        with pytest.raises(pydantic.ValidationError, match=r".*divergence.*"):
            ratings_api.UserCheckRequest(
                apikey="key",
                accept=generic_api.GenericAcceptTypes.json,
                user_id="123",
                divergence=-1,
                minutes=180,
            )
        with pytest.raises(pydantic.ValidationError, match=r".*user_id.*"):
            ratings_api.UserCheckRequest(
                apikey="key",
                accept=generic_api.GenericAcceptTypes.json,
                user_id="non_numeric_userid",  # user_id has to be a str with only numbers
                divergence=3,
                minutes=180,
            )
            ratings_api.UserCheckRequest(
                apikey="key",
                accept="non-enum_accept_value",
                user_id="123",
                divergence=3,
                minutes=180,
            )
