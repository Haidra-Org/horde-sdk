"""Short examples of how to use."""

import argparse
import os

import pydantic

from horde_sdk.ratings_api.apimodels import (
    ImageRatingsComparisonTypes,
    SelectableReturnFormats,
    UserValidateRequest,
    UserValidateResponse,
    UserValidateResponseRecord,
)
from horde_sdk.ratings_api.ratings_client import RatingsAPIClient

# See also in horde_sdk.ratings_api:
# UserCheckRequest,
# UserCheckResponse,
# UserRatingsRequest,
# UserRatingsResponse,


def main() -> None:
    """Just a proof of concept - but several other pieces of functionality exist."""
    argParser = argparse.ArgumentParser()

    argParser.add_argument("-k", "--key", required=False, help="Your horde API key.")
    argParser.add_argument("-o", "--output_file", required=True, help="The file to write the response to.")
    argParser.add_argument("-u", "--user_id", required=True, help="The user_id (number only) to test against.")
    args = argParser.parse_args()

    env_apikey = os.environ.get("HORDE_API_KEY")

    if args.key is None and env_apikey is None:
        print(
            "You must provide an API key either via the -k/--key argument or the HORDE_API_KEY environment variable.",
        )
        exit(1)

    ratings_api_client = RatingsAPIClient()
    user_validate_request = UserValidateRequest(
        apikey=args.key,
        user_id=args.user_id,
        format=SelectableReturnFormats.json,
        rating=8,
        rating_comparison=ImageRatingsComparisonTypes.greater_than_equal,
        min_ratings=0,
    )

    print("Request URL:")
    print(user_validate_request.get_api_endpoint_url())
    print()
    print("Request Body JSON:")
    print(user_validate_request.model_dump_json())

    response: pydantic.BaseModel = ratings_api_client.submit_request(
        api_request=user_validate_request,
        # Note that the type hint is accurate on the return type of this `get_success_response_type()`
        expected_response_type=user_validate_request.get_default_success_response_type(),
    )
    if not isinstance(response, UserValidateResponse):
        raise Exception("The response type doesn't match expected one!")

    print("Response JSON:")
    responseJson = response.model_dump_json()

    print()
    print("Response pydantic representation:")
    print(responseJson)
    print()
    print("Select details from the response:")
    print(f"{response.total=}")
    first_rating: UserValidateResponseRecord = response.ratings[0]

    print(f"{first_rating.image=}")
    print(f"{first_rating.rating=}")
    print(f"{first_rating.artifacts=}")
    print(f"{first_rating.average=}")
    print(f"{first_rating.times_rated=}")

    with open(args.output_file, "w", encoding="utf-8") as fileOutHandle:
        fileOutHandle.write(first_rating.model_dump_json())


if __name__ == "__main__":
    main()
