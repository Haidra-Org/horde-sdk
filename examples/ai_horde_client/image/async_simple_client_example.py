import argparse
import asyncio
import sys
from pathlib import Path

import aiohttp
from loguru import logger
from PIL.Image import Image

from horde_sdk import ANON_API_KEY, RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncClientSession, AIHordeAPIAsyncSimpleClient
from horde_sdk.ai_horde_api.apimodels import (
    # ExtraTextEntry,
    ImageGenerateAsyncRequest,
    ImageGenerateStatusResponse,
    ImageGeneration,
    ImageGenerationInputPayload,
    TIPayloadEntry,
)
from horde_sdk.ai_horde_api.fields import JobID


def save_image_and_json(
    image: Image,
    generation: ImageGeneration,
    example_path: Path,
    filename_base: str,
) -> None:
    image.save(example_path / f"{filename_base}.webp")
    logger.info(f"Image saved to {example_path / f'{filename_base}.webp'}")

    with open(example_path / f"{filename_base}.json", "w") as f:
        f.write(generation.model_dump_json(indent=4))

    logger.info(f"Response JSON saved to {example_path / f'{filename_base}.json'}")


async def async_one_image_generate_example(
    simple_client: AIHordeAPIAsyncSimpleClient,
    apikey: str = ANON_API_KEY,
) -> None:
    single_generation_response: ImageGenerateStatusResponse
    job_id: JobID

    single_generation_response, job_id = await simple_client.image_generate_request(
        ImageGenerateAsyncRequest(
            apikey=apikey,
            prompt="A cat in a hat",
            models=["Deliberate"],
            params=ImageGenerationInputPayload(
                height=512,
                width=512,
                tis=[
                    TIPayloadEntry(
                        name="72437",
                        inject_ti="negprompt",
                        strength=1,
                    ),
                ],
                n=2,
            ),
        ),
    )

    if isinstance(single_generation_response, RequestErrorResponse):
        logger.error(f"Error: {single_generation_response.message}")
    else:
        example_path = Path("requested_images")
        example_path.mkdir(exist_ok=True, parents=True)

        download_image_tasks: list[asyncio.Task[tuple[Image, JobID]]] = []

        for generation in single_generation_response.generations:
            download_image_tasks.append(asyncio.create_task(simple_client.download_image_from_generation(generation)))

        downloaded_images: list[tuple[Image, JobID]] = await asyncio.gather(*download_image_tasks)

        for image, job_id in downloaded_images:
            filename_base = f"{job_id}_simple_async_example"
            save_image_and_json(image, generation, example_path, filename_base)


async def async_multi_image_generate_example(
    simple_client: AIHordeAPIAsyncSimpleClient,
    apikey: str = ANON_API_KEY,
) -> None:
    multi_generation_responses: tuple[
        tuple[ImageGenerateStatusResponse, JobID],
        tuple[ImageGenerateStatusResponse, JobID],
    ]
    multi_generation_responses = await asyncio.gather(
        simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                apikey=apikey,
                prompt="a blue stylized brain",
                models=["Anything Diffusion"],
                params=ImageGenerationInputPayload(
                    height=1024,
                    width=1024,
                    n=2,
                ),
            ),
        ),
        simple_client.image_generate_request(
            ImageGenerateAsyncRequest(
                apikey=apikey,
                prompt="a red stylized brain",
                models=["AlbedoBase XL (SDXL)"],
                params=ImageGenerationInputPayload(
                    height=1024,
                    width=1024,
                    n=2,
                ),
            ),
        ),
    )

    download_image_tasks: list[asyncio.Task[tuple[Image, JobID]]] = []

    for generation_response, _job_id in multi_generation_responses:
        if isinstance(generation_response, RequestErrorResponse):
            logger.error(f"Error: {generation_response.message}")
        else:
            example_path = Path("requested_images")
            example_path.mkdir(exist_ok=True, parents=True)

            for generation in generation_response.generations:
                download_image_tasks.append(
                    asyncio.create_task(simple_client.download_image_from_generation(generation)),
                )

    downloaded_images: list[tuple[Image, JobID]] = await asyncio.gather(*download_image_tasks)

    for image, job_id in downloaded_images:
        filename_base = f"{job_id}_simple_async_example"
        save_image_and_json(image, generation, example_path, filename_base)


async def async_simple_generate_example(apikey: str = ANON_API_KEY) -> None:
    aiohttp_session = aiohttp.ClientSession()
    horde_client_session = AIHordeAPIAsyncClientSession(aiohttp_session)

    async with aiohttp_session, horde_client_session:
        simple_client = AIHordeAPIAsyncSimpleClient(
            aiohttp_session=aiohttp_session,
            horde_client_session=horde_client_session,
        )

        # await async_one_image_generate_example(simple_client, apikey)
        await async_multi_image_generate_example(simple_client, apikey)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Horde API Manual Client Example")
    parser.add_argument(
        "--apikey",
        "--api-key",
        "-k",
        type=str,
        default=ANON_API_KEY,
        help="The API key to use. Defaults to the anon key.",
    )
    args = parser.parse_args()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the example.
    asyncio.run(async_simple_generate_example(args.apikey))
