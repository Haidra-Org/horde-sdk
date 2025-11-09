from horde_model_reference.model_reference_manager import ModelReferenceManager
from typing_extensions import override

from horde_sdk import KNOWN_DISPATCH_SOURCE, RequestErrorResponse
from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIAsyncClientSession, AIHordeAPIClientSession
from horde_sdk.ai_horde_api.apimodels import ImageGenerateJobPopRequest, ImageGenerateJobPopResponse
from horde_sdk.consts import WORKER_TYPE
from horde_sdk.generation_parameters import ImageGenerationParameters
from horde_sdk.utils import default_bridge_agent_string
from horde_sdk.worker.dispatch.ai_horde.bridge_data import ImageWorkerBridgeData
from horde_sdk.worker.dispatch.ai_horde.image.convert import convert_image_job_pop_response_to_parameters
from horde_sdk.worker.dispatch.pop_strategy import JobPopStrategy
from horde_sdk.worker.generations import (
    ImageSingleGeneration,
)
from horde_sdk.worker.jobs import ImageWorkerJob


class AIHordeImageWorkerJobPopStrategy(JobPopStrategy[ImageSingleGeneration, ImageGenerationParameters]):
    """Job pop strategy for AI Horde image worker jobs."""

    _image_worker_bridge_data: ImageWorkerBridgeData
    _bridge_agent_string: str = default_bridge_agent_string

    _sync_client_session: AIHordeAPIClientSession | None
    _async_client_session: AIHordeAPIAsyncClientSession | None

    _model_reference_manager: ModelReferenceManager

    def __init__(
        self,
        default_job_pop_time_spacing: float = JobPopStrategy._default_job_pop_time_spacing,
        *,
        image_worker_bridge_data: ImageWorkerBridgeData,
        bridge_agent_string: str = default_bridge_agent_string,
        sync_client_session: AIHordeAPIClientSession | None = None,
        async_client_session: AIHordeAPIAsyncClientSession | None = None,
        model_reference_manager: ModelReferenceManager,
    ) -> None:
        """Initialize the AI Horde image worker job pop strategy.

        Args:
            default_job_pop_time_spacing (float): Default minimum time spacing between job pops in seconds.
            image_worker_bridge_data (ImageWorkerBridgeData): The bridge data for the image worker.
            bridge_agent_string (str): The bridge agent string to use for the worker.
            sync_client_session (AIHordeAPIClientSession | None): Optional synchronous client session for API calls.
            async_client_session (AIHordeAPIAsyncClientSession | None): Optional asynchronous client session for API
                calls.
            model_reference_manager (ModelReferenceManager): The model reference manager for handling model references.
        """
        super().__init__(default_job_pop_time_spacing)

        self._bridge_agent_string = bridge_agent_string

        self._image_worker_bridge_data = image_worker_bridge_data

        self._sync_client_session = sync_client_session
        self._async_client_session = async_client_session

        self._model_reference_manager = model_reference_manager

    @override
    def get_worker_type(self) -> WORKER_TYPE:
        return WORKER_TYPE.image

    @override
    def get_dispatch_source(self) -> KNOWN_DISPATCH_SOURCE:
        return KNOWN_DISPATCH_SOURCE.AI_HORDE_API_OFFICIAL

    @override
    def pop_job(self) -> ImageWorkerJob | None:
        if self._sync_client_session is None:
            raise ValueError("Synchronous client session is not available.")

        job_pop_request = ImageGenerateJobPopRequest(
            apikey=self._image_worker_bridge_data.api_key,
            name=self._image_worker_bridge_data.dreamer_worker_name,
            models=self._image_worker_bridge_data.image_models_to_load,
            max_pixels=self._image_worker_bridge_data.max_pixels,
            bridge_agent=self._bridge_agent_string,
            blacklist=self._image_worker_bridge_data.blacklist,
            nsfw=self._image_worker_bridge_data.nsfw,
            threads=self._image_worker_bridge_data.max_threads,
            require_upfront_kudos=self._image_worker_bridge_data.require_upfront_kudos,
            allow_img2img=self._image_worker_bridge_data.allow_img2img,
            allow_painting=self._image_worker_bridge_data.allow_inpainting,
            allow_unsafe_ipaddr=self._image_worker_bridge_data.allow_unsafe_ip,
            allow_post_processing=self._image_worker_bridge_data.allow_post_processing,
            allow_controlnet=self._image_worker_bridge_data.allow_controlnet,
            allow_sdxl_controlnet=self._image_worker_bridge_data.allow_sdxl_controlnet,
            extra_slow_worker=self._image_worker_bridge_data.extra_slow_worker,
            limit_max_steps=self._image_worker_bridge_data.limit_max_steps,
            allow_lora=self._image_worker_bridge_data.allow_lora,
            amount=self._image_worker_bridge_data.max_batch,
        )

        job_pop_response = self._sync_client_session.submit_request(
            job_pop_request,
            ImageGenerateJobPopResponse,
        )

        if isinstance(job_pop_response, RequestErrorResponse):
            print(f"Error popping job: {job_pop_response.message}")
            return None

        generation, ai_horde_dispatch_parameters = convert_image_job_pop_response_to_parameters(
            api_response=job_pop_response,
            model_reference_manager=self._model_reference_manager,
        )

        raise NotImplementedError("Conversion from job pop response to parameters is not implemented.")  # FIXME

        return ImageWorkerJob(
            generation=generation,
            ai_horde_dispatch_parameters=ai_horde_dispatch_parameters,
        )

    @override
    async def async_pop_job(self) -> ImageWorkerJob | None:
        pass
