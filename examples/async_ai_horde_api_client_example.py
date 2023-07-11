from __future__ import annotations

import asyncio

from horde_sdk.ai_horde_api import AIHordeAPIClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest
from horde_sdk.generic_api import RequestErrorResponse


async def main() -> None:
    print("Starting...")
    ai_horde_api_client = AIHordeAPIClient()

    image_generate_async_request = ImageGenerateAsyncRequest(
        apikey="0000000000",
        prompt="A cat in a hat",
        models=["Deliberate"],
    )

    response = await ai_horde_api_client.async_submit_request(
        image_generate_async_request,
        image_generate_async_request.get_success_response_type(),
    )

    if isinstance(response, RequestErrorResponse):
        print(f"Error: {response.message}")
        return

    # Keep making ImageGenerateCheckRequests until the job is done.
    while True:
        check_response = await ai_horde_api_client.async_get_generate_check(
            apikey="0000000000",
            generation_id=response.id_,
        )

        if isinstance(check_response, RequestErrorResponse):
            print(f"Error: {check_response.message}")
            return

        if check_response.done:
            break

        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
