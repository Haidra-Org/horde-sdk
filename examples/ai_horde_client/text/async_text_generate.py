import argparse
import asyncio
import sys
from pathlib import Path

import aiofiles
import aiohttp
from loguru import logger

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncClientSession, AIHordeAPIAsyncSimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    ModelGenerationInputKobold,
    TextGenerateAsyncRequest,
    TextGenerateStatusResponse,
)
from horde_sdk.ai_horde_api.exceptions import AIHordeRequestError
from horde_sdk.ai_horde_api.fields import JobID


def check_callback(response: TextGenerateStatusResponse) -> None:
    """Callback function that can be passed to the text_generate_request method to get progress updates on the
    request."""
    logger.info(f"Response: {response}")


async def async_text_generate_example(
    simple_client: AIHordeAPIAsyncSimpleClient,
    apikey: str = ANON_API_KEY,
) -> None:

    status_response: TextGenerateStatusResponse
    job_id: JobID

    try:
        status_response, job_id = await simple_client.text_generate_request(
            TextGenerateAsyncRequest(
                apikey=apikey,
                prompt="Hello, world!",
                models=["koboldcpp/LLaMA2-13B-Psyfighter2"],
                params=ModelGenerationInputKobold(
                    # dynatemp_exponent=1.0,
                    # dynatemp_range=0.0,
                    # frmtadsnsp=False,
                    # frmtrmblln=False,
                    # frmtrmspch=False,
                    # frmttriminc=False,
                    max_context_length=1024,
                    max_length=80,
                    # min_p=0.0,
                    # n=1,
                    # rep_pen=1.0,
                    # rep_pen_range=0,
                    # rep_pen_slope=0.0,
                    # sampler_order=[1, 2, 3],
                    # singleline=False,
                    # smoothing_factor=0.0,
                    # stop_sequence=["stop1", "stop2"],
                    # temperature=0.0,
                    # tfs=0.0,
                    # top_a=0.0,
                    # top_k=0,
                    # top_p=0.001,
                    # typical=0.0,
                    # use_default_badwordsids=True,
                ),
            ),
            # timeout=60*60*20, # time before cancelling the request; times out server side at 20 minutes by default
            check_callback=check_callback,
        )
    except AIHordeRequestError as e:
        logger.error(f"Server error: {e}")
        return
    except RuntimeError as e:
        logger.error(f"Runtime error: {e}")
        return

    if len(status_response.generations) == 0:
        raise ValueError("No generations returned in the response.")

    logger.debug(f"Job ID: {job_id}")
    logger.debug(f"Response: {status_response}")

    text_generated = status_response.generations[0].text

    logger.debug(f"Generated Text: {text_generated}")

    example_path = Path("requested_text")
    example_path.mkdir(exist_ok=True, parents=True)

    async with aiofiles.open(example_path / f"{job_id}_async_example.txt", "w") as f:
        await f.write(status_response.model_dump_json(indent=4))

    logger.info(f"Wrote full response JSON to {example_path / f'{job_id}_async_example.txt'}")


async def main(apikey: str) -> None:
    aiohttp_session = aiohttp.ClientSession()
    horde_client_session = AIHordeAPIAsyncClientSession(
        aiohttp_session=aiohttp_session,
    )
    async_client = AIHordeAPIAsyncSimpleClient(horde_client_session=horde_client_session)

    async with aiohttp_session, horde_client_session:
        await async_text_generate_example(async_client, apikey)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-key",
        "--apikey",
        "-k",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main(args.api_key))
