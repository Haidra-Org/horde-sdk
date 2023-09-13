from horde_sdk import ANON_API_KEY
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPISimpleClient
from horde_sdk.ai_horde_api.apimodels import ImageGenerateAsyncRequest, ImageGenerationInputPayload
from horde_sdk.ai_horde_api.consts import KNOWN_SAMPLERS


def simple_generate_example() -> None:
    simple_client = AIHordeAPISimpleClient()

    dry_run_response = simple_client.image_generate_request_dry_run(
        ImageGenerateAsyncRequest(
            apikey=ANON_API_KEY,
            prompt="A cat in a hat",
            params=ImageGenerationInputPayload(
                sampler_name=KNOWN_SAMPLERS.k_heun,
                denoising_strength=0.4,
                seed="42",
                height=832,
                width=832,
                karras=True,
                steps=20,
                n=1,
            ),
            models=["Deliberate"],
            dry_run=True,
        ),
    )

    print(dry_run_response)


if __name__ == "__main__":
    simple_generate_example()
