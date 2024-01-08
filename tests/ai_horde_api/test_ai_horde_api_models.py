"""Unit tests for AI-Horde API models."""
from horde_sdk.ai_horde_api.apimodels._find_user import (
    ContributionsDetails,
    FindUserRequest,
    FindUserResponse,
    UsageDetails,
)
from horde_sdk.ai_horde_api.apimodels.generate._async import (
    ImageGenerateAsyncRequest,
    ImageGenerationInputPayload,
)
from horde_sdk.ai_horde_api.apimodels.workers._workers_all import (
    AllWorkersDetailsResponse,
    TeamDetailsLite,
    WorkerDetailItem,
    WorkerKudosDetails,
)
from horde_sdk.ai_horde_api.consts import KNOWN_SAMPLERS, KNOWN_SOURCE_PROCESSING, WORKER_TYPE


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
            sampler_name=KNOWN_SAMPLERS.k_lms,
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
    assert test_async_request.params.sampler_name == "k_lms"
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
    FindUserResponse(
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
