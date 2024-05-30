import argparse

from horde_sdk import RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import FindUserRequest
from horde_sdk.ai_horde_api.apimodels._users import UserDetailsResponse


def find_user_example(
    api_key: str,
    client: AIHordeAPIManualClient,
) -> None:
    find_user_request = FindUserRequest(
        apikey=api_key,
    )

    find_user_response: UserDetailsResponse | RequestErrorResponse
    find_user_response = client.submit_request(find_user_request, expected_response_type=UserDetailsResponse)

    if isinstance(find_user_response, RequestErrorResponse):
        print(f"Error: {find_user_response.message}")
    else:
        print(f"User found: {find_user_response.id_}")

        print()
        print(find_user_response.model_dump_json(indent=4))


if __name__ == "__main__":
    # Add the api key argument with argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-key",
        "--api_key",
        "--apikey",
        "-k",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    # Create the client
    client = AIHordeAPIManualClient()

    # Run the example
    find_user_example(api_key=args.api_key, client=client)
