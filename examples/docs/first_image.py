"""Estimate and optionally run one anonymous AI Horde image request."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload


# --8<-- [start:first-image]
def build_request(*, dry_run: bool) -> ImageGenerateAsyncRequest:
    """Build the same small request for estimation or generation."""
    return ImageGenerateAsyncRequest(
        apikey=ANON_API_KEY,
        prompt="A small glass greenhouse in a mossy forest, morning light",
        models=["AlbedoBase XL (SDXL)"],
        params=ImageGenerationInputPayload(width=512, height=512, steps=20, n=1),
        nsfw=False,
        censor_nsfw=True,
        dry_run=dry_run,
    )


def estimate(client: AIHordeAPISimpleClient) -> float:
    """Return the estimated kudos cost without creating an image."""
    response = client.image_generate_request_dry_run(build_request(dry_run=True))
    return response.kudos


def generate(client: AIHordeAPISimpleClient, output: Path) -> Path:
    """Generate one image, save it, and verify that Pillow can decode it."""
    status, _request_id = client.image_generate_request(build_request(dry_run=False))
    if not status.generations:
        raise RuntimeError("The request completed without an image")

    image = client.download_image_from_generation(status.generations[0])
    image.save(output)
    with Image.open(output) as saved:
        saved.verify()
    return output


# --8<-- [end:first-image]


def main() -> None:
    """Run a dry run by default and require an explicit flag for live generation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Submit and wait for the image after estimating its cost")
    parser.add_argument("--output", type=Path, default=Path("horde-sdk-first-image.webp"))
    args = parser.parse_args()

    client = AIHordeAPISimpleClient()
    print(f"Estimated cost: {estimate(client):g} kudos")
    if args.live:
        print(f"Verified image: {generate(client, args.output).resolve()}")


if __name__ == "__main__":
    main()
