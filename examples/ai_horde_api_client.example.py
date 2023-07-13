from horde_sdk.ai_horde_api import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest
from horde_sdk.generic_api.apimodels import RequestErrorResponse


def do_generate_check(ai_horde_api_client: AIHordeAPISimpleClient) -> None:
    pass


def main() -> None:
    """Just a proof of concept - but several other pieces of functionality exist."""

    ai_horde_api_client = AIHordeAPISimpleClient()

    image_generate_async_request = ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="A cat in a hat",
        models=["Deliberate"],
    )

    response = ai_horde_api_client.submit_request(
        image_generate_async_request,
        image_generate_async_request.get_success_response_type(),
    )

    if isinstance(response, RequestErrorResponse):
        print(f"Error: {response.message}")
        return

    print(f"Job ID: {response.id_}")


if __name__ == "__main__":
    main()
