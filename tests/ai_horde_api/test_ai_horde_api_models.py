"""Unit tests for AI-Horde API models."""

import base64
import io
import json
from uuid import UUID

import aiohttp
import PIL.Image
import pytest

from horde_sdk.ai_horde_api.apimodels import (
    KNOWN_ALCHEMY_TYPES,
    AlchemyPopFormPayload,
    AlchemyPopResponse,
    ImageGenerateAsyncResponse,
)
from horde_sdk.ai_horde_api.apimodels._find_user import (
    FindUserRequest,
)
from horde_sdk.ai_horde_api.apimodels._users import ContributionsDetails, UsageDetails, UserDetailsResponse
from horde_sdk.ai_horde_api.apimodels.base import GenMetadataEntry
from horde_sdk.ai_horde_api.apimodels.generate._async import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)
from horde_sdk.ai_horde_api.apimodels.generate._pop import (
    ImageGenerateJobPopPayload,
    ImageGenerateJobPopResponse,
    ImageGenerateJobPopSkippedStatus,
)
from horde_sdk.ai_horde_api.apimodels.workers._workers import (
    AllWorkersDetailsResponse,
    TeamDetailsLite,
    WorkerDetailItem,
    WorkerKudosDetails,
)
from horde_sdk.ai_horde_api.consts import (
    KNOWN_CONTROLNETS,
    KNOWN_FACEFIXERS,
    KNOWN_SAMPLERS,
    KNOWN_SOURCE_PROCESSING,
    KNOWN_UPSCALERS,
    METADATA_TYPE,
    METADATA_VALUE,
    WORKER_TYPE,
)
from horde_sdk.ai_horde_api.fields import JobID


def test_api_endpoint() -> None:
    ImageGenerateAsyncRequest.get_api_url()
    ImageGenerateAsyncRequest.get_api_endpoint_subpath()
    ImageGenerateAsyncRequest.get_api_endpoint_url()


def test_ImageGenerateAsyncRequest(ai_horde_api_key: str) -> None:
    test_async_request = ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        models=["Deliberate"],
        prompt="test prompt",
        params=ImageGenerationInputPayload(
            # sampler_name="DDIM",
            sampler_name=KNOWN_SAMPLERS.DDIM,
            cfg_scale=7.5,
            denoising_strength=1,
            seed="123456789",
            height=512,
            width=512,
            seed_variation=None,
            post_processing=[],
            karras=True,
            tiling=False,
            hires_fix=False,
            clip_skip=1,
            control_type=None,
            image_is_control=None,
            return_control_map=None,
            facefixer_strength=None,
            loras=[],
            special={},
            steps=25,
            n=1,
            use_nsfw_censor=False,
        ),
        nsfw=True,
        trusted_workers=False,
        slow_workers=False,
        extra_slow_workers=False,
        workers=[],
        censor_nsfw=False,
        source_image="test source image (usually base64)",
        source_processing=KNOWN_SOURCE_PROCESSING.txt2img,
        source_mask="test source mask (usually base64)",
        r2=True,
        shared=False,
        replacement_filter=True,
        dry_run=False,
    )
    assert test_async_request.apikey == ai_horde_api_key
    assert test_async_request.models == ["Deliberate"]
    assert test_async_request.prompt == "test prompt"
    assert test_async_request.params is not None
    assert test_async_request.params.sampler_name == "DDIM"
    assert test_async_request.params.cfg_scale == 7.5
    assert test_async_request.params.denoising_strength == 1
    assert test_async_request.params.seed is not None
    assert test_async_request.params.seed.isdigit()
    assert test_async_request.params.height == 512
    assert test_async_request.params.width == 512
    assert test_async_request.params.seed_variation is None
    assert test_async_request.params.post_processing == []
    assert test_async_request.params.karras is True
    assert test_async_request.params.tiling is False
    assert test_async_request.params.hires_fix is False
    assert test_async_request.params.clip_skip == 1
    assert test_async_request.params.control_type is None
    assert test_async_request.params.image_is_control is None
    assert test_async_request.params.return_control_map is None
    assert test_async_request.params.facefixer_strength is None
    assert test_async_request.params.loras == []
    assert test_async_request.params.special == {}
    assert test_async_request.params.steps == 25
    assert test_async_request.params.n == 1
    assert test_async_request.params.use_nsfw_censor is False
    assert test_async_request.nsfw is True
    assert test_async_request.trusted_workers is False
    assert test_async_request.slow_workers is False
    assert test_async_request.extra_slow_workers is False
    assert test_async_request.workers == []
    assert test_async_request.censor_nsfw is False
    assert test_async_request.source_image == "test source image (usually base64)"
    assert test_async_request.source_processing == KNOWN_SOURCE_PROCESSING.txt2img
    assert test_async_request.source_mask == "test source mask (usually base64)"
    assert test_async_request.r2 is True
    assert test_async_request.shared is False
    assert test_async_request.replacement_filter is True
    assert test_async_request.dry_run is False


def test_ImageGenerateAsyncRequest_unknown_sampler(ai_horde_api_key: str) -> None:
    test_async_request = ImageGenerateAsyncRequest(
        apikey=ai_horde_api_key,
        models=["Deliberate"],
        prompt="test prompt",
        params=ImageGenerationInputPayload(
            sampler_name="unknown sampler",
            cfg_scale=7.5,
            denoising_strength=1,
            seed="123456789",
            height=512,
            width=512,
            seed_variation=None,
            post_processing=[],
            karras=True,
            tiling=False,
            hires_fix=False,
            clip_skip=1,
            control_type=None,
            image_is_control=None,
            return_control_map=None,
            facefixer_strength=None,
            loras=[],
            special={},
            steps=25,
            n=1,
            use_nsfw_censor=False,
        ),
        nsfw=True,
        trusted_workers=False,
        slow_workers=False,
        extra_slow_workers=False,
        workers=[],
        censor_nsfw=False,
        source_image="test source image (usually base64)",
        source_processing=KNOWN_SOURCE_PROCESSING.txt2img,
        source_mask="test source mask (usually base64)",
        r2=True,
        shared=False,
        replacement_filter=True,
        dry_run=False,
    )
    assert test_async_request.params is not None
    assert test_async_request.params.sampler_name == "unknown sampler"


def test_TeamDetailsLite() -> None:
    test_team_details_lite = TeamDetailsLite(
        name="test team name",
        id="test team id",
    )
    assert test_team_details_lite.name == "test team name"
    assert test_team_details_lite.id_ == "test team id"


def test_WorkerKudosDetails() -> None:
    test_worker_kudos_details = WorkerKudosDetails(
        generated=1.0,
        uptime=1,
    )
    assert test_worker_kudos_details.generated == 1.0
    assert test_worker_kudos_details.uptime == 1


def test_AllWorkersDetailsResponse() -> None:
    test_all_workers_details_response = AllWorkersDetailsResponse(
        root=[
            WorkerDetailItem(
                type=WORKER_TYPE.image,
                name="test worker name",
                id="test worker id",
                online=True,
                requests_fulfilled=1,
                kudos_rewards=1.0,
                kudos_details=WorkerKudosDetails(
                    generated=1.0,
                    uptime=1,
                ),
                performance="test performance",
                threads=1,
                uptime=1,
                maintenance_mode=True,
                paused=True,
                info="test info",
                nsfw=True,
                owner="test owner",
                trusted=True,
                flagged=True,
                suspicious=1,
                uncompleted_jobs=1,
                models=["test model"],
                forms=["test form"],
                team=TeamDetailsLite(
                    name="test team name",
                    id="test team id",
                ),
                contact="test contact",
                bridge_agent="test bridge agent",
                max_pixels=1,
                megapixelsteps_generated=1,
                img2img=True,
                painting=True,
                post_processing=True,
            ),
        ],
    )
    assert test_all_workers_details_response[0].type_ == WORKER_TYPE.image
    assert test_all_workers_details_response[0].name == "test worker name"
    assert test_all_workers_details_response[0].id_ == "test worker id"
    assert test_all_workers_details_response[0].online is True
    assert test_all_workers_details_response[0].requests_fulfilled == 1
    assert test_all_workers_details_response[0].kudos_rewards == 1.0
    assert test_all_workers_details_response[0].kudos_details is not None
    assert test_all_workers_details_response[0].kudos_details.generated == 1.0
    assert test_all_workers_details_response[0].kudos_details.uptime == 1
    assert test_all_workers_details_response[0].performance == "test performance"
    assert test_all_workers_details_response[0].threads == 1
    assert test_all_workers_details_response[0].uptime == 1
    assert test_all_workers_details_response[0].maintenance_mode is True
    assert test_all_workers_details_response[0].paused is True
    assert test_all_workers_details_response[0].info == "test info"
    assert test_all_workers_details_response[0].nsfw is True
    assert test_all_workers_details_response[0].owner == "test owner"
    assert test_all_workers_details_response[0].trusted is True
    assert test_all_workers_details_response[0].flagged is True
    assert test_all_workers_details_response[0].suspicious == 1
    assert test_all_workers_details_response[0].uncompleted_jobs == 1
    assert test_all_workers_details_response[0].models == ["test model"]
    assert test_all_workers_details_response[0].forms == ["test form"]
    assert test_all_workers_details_response[0].team is not None
    assert test_all_workers_details_response[0].team.name == "test team name"
    assert test_all_workers_details_response[0].team.id_ == "test team id"
    assert test_all_workers_details_response[0].contact == "test contact"
    assert test_all_workers_details_response[0].bridge_agent == "test bridge agent"
    assert test_all_workers_details_response[0].max_pixels == 1
    assert test_all_workers_details_response[0].megapixelsteps_generated == 1
    assert test_all_workers_details_response[0].img2img is True
    assert test_all_workers_details_response[0].painting is True
    assert test_all_workers_details_response[0].post_processing is True

    assert isinstance(test_all_workers_details_response.model_dump(), list)

    print(test_all_workers_details_response.model_dump())


def test_FindUserRequest(ai_horde_api_key: str) -> None:
    FindUserRequest(apikey=ai_horde_api_key)


def test_FindUserResponse() -> None:
    UserDetailsResponse(
        account_age=1,
        concurrency=1,
        contributions=ContributionsDetails(
            fulfillments=1,
            megapixelsteps=1000,
        ),
        evaluating_kudos=1.0,
        flagged=True,
        kudos=1,
        id=1,
        moderator=False,
        pseudonymous=False,
        special=False,
        trusted=True,
        username="test username",
        usage=UsageDetails(
            megapixelsteps=1.0,
            requests=1,
        ),
        worker_count=1,
        worker_invited=False,
        vpn=False,
    )


def test_GenMetadataEntry() -> None:
    GenMetadataEntry(
        type=METADATA_TYPE.batch_index,
        value=METADATA_VALUE.see_ref,
        ref="1",
    )

    GenMetadataEntry(
        type="test key",
        value="test value",
    )


def test_ImageGenerateJobPopResponse() -> None:
    with pytest.raises(ValueError):
        _ = ImageGenerateJobPopResponse(
            id=None,
            ids=[],
            payload=ImageGenerateJobPopPayload(
                post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
                prompt="A cat in a hat",
            ),
            model="Deliberate",
            skipped=ImageGenerateJobPopSkippedStatus(),
        )

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert test_response.id_ is None
    assert test_response.has_upscaler is True
    assert test_response.has_facefixer is False

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert test_response.has_upscaler is False
    assert test_response.has_facefixer is False

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_FACEFIXERS.CodeFormers],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert test_response.has_upscaler is False
    assert test_response.has_facefixer is True

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_FACEFIXERS.CodeFormers, KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert test_response.has_upscaler is True
    assert test_response.has_facefixer is True

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=["unknown post processor"],
            control_type="unknown control type",
            sampler_name="unknown sampler",
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )
    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=["unknown post processor"],
            control_type=KNOWN_CONTROLNETS.canny,
            sampler_name="unknown sampler",
            prompt="A cat in a hat",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
    )
    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=["unknown post processor"],
            control_type="canny",
            sampler_name="unknown sampler",
            prompt="A cat in a hat",
        ),
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=["4x_AnimeSharp"],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert all(
        post_processor in KNOWN_UPSCALERS._value2member_map_
        for post_processor in test_response.payload.post_processing
    )

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.four_4x_AnimeSharp],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert all(post_processor in KNOWN_UPSCALERS for post_processor in test_response.payload.post_processing)

    test_response = ImageGenerateJobPopResponse(
        ids=[
            JobID(root=UUID("00000000-0000-0000-0000-000000000001")),
            JobID(root=UUID("00000000-0000-0000-0000-000000000002")),
            JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
        ],
        payload=ImageGenerateJobPopPayload(
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        r2_uploads=[
            "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000001.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=zxcbvfakesignature%3D&Expires=1727390285",
            "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000000.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=345567dfakes2ignature%3D&Expires=1727390285",
            "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000002.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=asdfg32fakesignature%3D&Expires=1727390285",
        ],
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    assert test_response.ids_present
    assert test_response.ids == [
        JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
        JobID(root=UUID("00000000-0000-0000-0000-000000000001")),
        JobID(root=UUID("00000000-0000-0000-0000-000000000002")),
    ]
    assert test_response.r2_uploads == [
        "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000000.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=345567dfakes2ignature%3D&Expires=1727390285",
        "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000001.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=zxcbvfakesignature%3D&Expires=1727390285",
        "https://abbaabbaabbaabbaabbaabbaabbaabba.r2.cloudflarestorage.com/horde-transient/00000000-0000-0000-0000-000000000002.webp?AWSAccessKeyId=deadbeefdeadbeefdeadbeefdeadbeef&Signature=asdfg32fakesignature%3D&Expires=1727390285",
    ]


def test_ImageGenerateJobPopResponse_hashability() -> None:
    test_response_ids = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="r2 download link",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response_ids_copy = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="parsed base64",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response2_ids = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000001"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    container = {test_response_ids}
    assert test_response_ids in container
    assert test_response_ids_copy in container
    assert test_response2_ids not in container

    container2 = {test_response2_ids}
    assert test_response2_ids in container2
    assert test_response_ids not in container2

    combined_container = {test_response_ids, test_response2_ids}
    assert test_response_ids in combined_container
    assert test_response2_ids in combined_container

    test_response_no_ids = ImageGenerateJobPopResponse(
        id=JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
        ids=[],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response_no_ids2 = ImageGenerateJobPopResponse(
        id=JobID(root=UUID("00000000-0000-0000-0000-000000000001")),
        ids=[],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    container_no_ids = {test_response_no_ids}
    assert test_response_no_ids in container_no_ids
    assert test_response_no_ids2 not in container_no_ids

    container2_no_ids = {test_response_no_ids2}
    assert test_response_no_ids2 in container2_no_ids
    assert test_response_no_ids not in container2_no_ids

    combined_container_no_ids = {test_response_no_ids, test_response_no_ids2}
    assert test_response_no_ids in combined_container_no_ids
    assert test_response_no_ids2 in combined_container_no_ids

    test_response_multiple_ids = ImageGenerateJobPopResponse(
        id=None,
        ids=[
            JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
            JobID(root=UUID("00000000-0000-0000-0000-000000000001")),
        ],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="r2 download link",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response_multiple_ids_copy = ImageGenerateJobPopResponse(
        id=None,
        ids=[
            JobID(root=UUID("00000000-0000-0000-0000-000000000001")),
            JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
        ],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="r2 download link",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    test_response_multiple_ids_2 = ImageGenerateJobPopResponse(
        id=None,
        ids=[
            JobID(root=UUID("00000000-0000-0000-0000-000000000002")),
            JobID(root=UUID("00000000-0000-0000-0000-000000000003")),
        ],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="parsed base64",
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    container_multiple_ids = {test_response_multiple_ids}
    assert test_response_multiple_ids in container_multiple_ids
    assert test_response_multiple_ids_copy in container_multiple_ids
    assert test_response_multiple_ids_2 not in container_multiple_ids

    combined_container_multiple_ids = {test_response_multiple_ids, test_response_multiple_ids_2}
    assert test_response_multiple_ids in combined_container_multiple_ids
    assert test_response_multiple_ids_copy in combined_container_multiple_ids
    assert test_response_multiple_ids_2 in combined_container_multiple_ids


@pytest.mark.asyncio
async def test_ImageGenerateJobPop_download_addtl_data() -> None:
    from horde_sdk.ai_horde_api.apimodels import ExtraSourceImageEntry

    test_response = ImageGenerateJobPopResponse(
        id=None,
        ids=[JobID(root=UUID("00000000-0000-0000-0000-000000000000"))],
        payload=ImageGenerateJobPopPayload(
            post_processing=[KNOWN_UPSCALERS.RealESRGAN_x2plus],
            prompt="A cat in a hat",
        ),
        model="Deliberate",
        source_image="https://raw.githubusercontent.com/db0/Stable-Horde/main/img_stable/0.jpg",
        source_mask="https://raw.githubusercontent.com/db0/Stable-Horde/main/img_stable/1.jpg",
        extra_source_images=[
            ExtraSourceImageEntry(
                image="https://raw.githubusercontent.com/db0/Stable-Horde/main/img_stable/2.jpg",
                strength=1.0,
            ),
            ExtraSourceImageEntry(
                image="https://raw.githubusercontent.com/db0/Stable-Horde/main/img_stable/3.jpg",
                strength=2.0,
            ),
        ],
        skipped=ImageGenerateJobPopSkippedStatus(),
    )

    client_session = aiohttp.ClientSession()

    await test_response.async_download_additional_data(client_session)

    assert test_response._downloaded_source_image is not None
    assert test_response._downloaded_source_mask is not None
    assert test_response._downloaded_extra_source_images is not None
    assert len(test_response._downloaded_extra_source_images) == 2

    downloaded_source_image = test_response.get_downloaded_source_image()
    assert downloaded_source_image is not None
    assert PIL.Image.open(io.BytesIO(base64.b64decode(downloaded_source_image)))

    downloaded_source_mask = test_response.get_downloaded_source_mask()
    assert downloaded_source_mask is not None
    assert PIL.Image.open(io.BytesIO(base64.b64decode(downloaded_source_mask)))

    downloaded_extra_source_images = test_response.get_downloaded_extra_source_images()
    assert downloaded_extra_source_images is not None
    assert len(downloaded_extra_source_images) == 2
    for extra_source_image in downloaded_extra_source_images:
        assert extra_source_image is not None
        assert extra_source_image.original_url is not None
        assert extra_source_image.original_url.startswith(
            "https://raw.githubusercontent.com/db0/Stable-Horde/main/img_stable/",
        )
        assert PIL.Image.open(io.BytesIO(base64.b64decode(extra_source_image.image)))

    assert downloaded_extra_source_images[0].strength == 1.0
    assert downloaded_extra_source_images[1].strength == 2.0


def test_AlchemyPopResponse() -> None:
    test_alchemy_pop_response = AlchemyPopResponse(
        forms=[
            AlchemyPopFormPayload(
                id=JobID(root=UUID("00000000-0000-0000-0000-000000000000")),
                form=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus,
                r2_upload="r2 download link",
                source_image="r2 download link",
            ),
        ],
    )

    assert test_alchemy_pop_response.forms is not None
    assert test_alchemy_pop_response.forms[0].id_ == JobID(root=UUID("00000000-0000-0000-0000-000000000000"))
    assert test_alchemy_pop_response.forms[0].form == KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus
    assert test_alchemy_pop_response.forms[0].r2_upload == "r2 download link"
    assert test_alchemy_pop_response.forms[0].source_image == "r2 download link"

    container = {test_alchemy_pop_response}

    assert test_alchemy_pop_response in container

    test_alchemy_pop_response_multiple_forms = AlchemyPopResponse(
        forms=[
            AlchemyPopFormPayload(
                id=JobID(root=UUID("00000000-0000-0000-0000-000000000010")),
                form=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus,
                r2_upload="r2 download link",
                source_image="r2 download link",
            ),
            AlchemyPopFormPayload(
                id=JobID(root=UUID("00000000-0000-0000-0000-000000000020")),
                form=KNOWN_ALCHEMY_TYPES.fourx_AnimeSharp,
                r2_upload="r2 download link",
                source_image="r2 download link",
            ),
        ],
    )

    test_alchemy_pop_response_multiple_forms_copy = AlchemyPopResponse(
        forms=[
            AlchemyPopFormPayload(
                id=JobID(root=UUID("00000000-0000-0000-0000-000000000020")),
                form=KNOWN_ALCHEMY_TYPES.RealESRGAN_x2plus,
                r2_upload="r2 download link",
                source_image="r2 download link",
            ),
            AlchemyPopFormPayload(
                id=JobID(root=UUID("00000000-0000-0000-0000-000000000010")),
                form=KNOWN_ALCHEMY_TYPES.fourx_AnimeSharp,
                r2_upload="r2 download link",
                source_image="r2 download link",
            ),
        ],
    )

    container_multiple_forms = {test_alchemy_pop_response_multiple_forms}
    assert test_alchemy_pop_response_multiple_forms in container_multiple_forms
    assert test_alchemy_pop_response_multiple_forms_copy in container_multiple_forms


def test_ImageGenerateJobPopSkippedStatus() -> None:
    testing_skipped_status = ImageGenerateJobPopSkippedStatus()

    assert testing_skipped_status.is_empty()


def test_problem_payload() -> None:
    json_from_api = """
                        {
                        "payload": {
                            "ddim_steps": 30,
                            "n_iter": 1,
                            "sampler_name": "k_euler_a",
                            "cfg_scale": 7.5,
                            "height": 512,
                            "width": 512,
                            "karras": false,
                            "tiling": false,
                            "hires_fix": false,
                            "image_is_control": false,
                            "return_control_map": false
                        },
                        "id": null,
                        "ids": [],
                        "skipped": {},
                        "model": null,
                        "source_image": null,
                        "source_processing": "img2img",
                        "source_mask": null,
                        "r2_upload": null,
                        "r2_uploads": null
                    }"""

    problem_payload = json.loads(json_from_api)

    ImageGenerateJobPopResponse.model_validate(problem_payload)

    json_from_api = """
                    {
                    "payload": {
                        "ddim_steps": 30,
                        "n_iter": 1,
                        "sampler_name": "k_euler_a",
                        "cfg_scale": 7.5,
                        "height": 512,
                        "width": 512,
                        "karras": false,
                        "tiling": false,
                        "hires_fix": false,
                        "image_is_control": false,
                        "return_control_map": false
                    },
                    "id": null,
                    "ids": [],
                    "skipped": {"max_pixels": 1},
                    "model": null,
                    "source_image": null,
                    "source_processing": "img2img",
                    "source_mask": null,
                    "r2_upload": null,
                    "r2_uploads": null
                }"""

    problem_payload = json.loads(json_from_api)

    ImageGenerateJobPopResponse.model_validate(problem_payload)


def test_problem_gen_request_response() -> None:

    example_json = """
                    {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "kudos": 8.0
                    }"""

    json_from_api = json.loads(example_json)

    ImageGenerateAsyncResponse.model_validate(json_from_api)
