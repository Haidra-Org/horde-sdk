"""Unit tests for API models."""

import json
import os

import horde_shared_models.generic_api as generic_api
import horde_shared_models.ratings_api as ratings_api
import pydantic
import pytest

SAMPLE_DATA_FOLDER_NAME = "tests/test_data"


class Test_reflection_and_dynamic:  # noqa: D101
    def test_reflection(self) -> None:  # noqa: D102
        reflection = ratings_api.Rating_API_Reflection()
        allRequestTypes = reflection.getAllRequestTypes()
        for requestType in allRequestTypes:
            assert issubclass(requestType, generic_api.BaseRequest)

    def test_dynamic_json_load(self) -> None:
        """Attempts to create instances of all non-abstract children of `RequestBase`."""
        # This test will do a lot of heavy lifting if you're looking to make additions/changes.
        # If you're here because it failed and you're not sure why,
        # check the implementation of `BaseRequestUserSpecific` and `UserRatingsRequest`
        reflection = ratings_api.Rating_API_Reflection()

        allRequestTypes: list[type[generic_api.BaseRequest]] = reflection.getAllRequestTypes()

        for requestType in allRequestTypes:
            assert issubclass(requestType, generic_api.BaseRequest)

            responseType: type[pydantic.BaseModel] = requestType.getExpectedResponseType()
            assert isinstance(responseType, type)
            assert issubclass(responseType, pydantic.BaseModel)

            targetFile = f"{SAMPLE_DATA_FOLDER_NAME}/{responseType.__name__}.json"
            assert os.path.exists(targetFile)

            with open(targetFile) as sampleFileHandle:
                sampleDataJson = json.loads(sampleFileHandle.read())
                responseType(**sampleDataJson)


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
        with pytest.raises(pydantic.ValidationError):
            ratings_api.UserCheckRequest(
                apikey="key",
                accept="non-enum_accept_value",  # type: ignore
                user_id="123",
                divergence=3,
                minutes=180,
            )

    # def test_testImageRequest(self):
    #     ratings_api.testImageRequest(
    #         apikey="key",
    #         accept=ratings_api.RequestMetadata.AcceptTypes.json,
    #         image_id="1df9510e-8e49-4441-bacb-9e379173aa45",  # type: ignore
    #         # if you get a type-related error here in your IDE, (shouldn't in vscode)
    #         # know that pydantic will marshal the `str` literal to `UUID`
    #     )
