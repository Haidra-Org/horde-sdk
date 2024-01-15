from loguru import logger
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate._progress import ResponseGenerationProgressInfoMixin
from horde_sdk.ai_horde_api.apimodels.generate._status import ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import HordeResponseBaseModel, ResponseWithProgressMixin


class ImageGenerateCheckResponse(
    HordeResponseBaseModel,
    ResponseWithProgressMixin,
    ResponseGenerationProgressInfoMixin,
):
    """Represents the data returned from the `/v2/generate/check/{id}` endpoint.

    v2 API Model: `RequestStatusCheck`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestStatusCheck"

    @override
    def is_job_complete(self, number_of_result_expected: int) -> bool:
        if self.done and self.finished != number_of_result_expected:
            logger.error(
                "There is a mismatch between the number of results expected and the number of results "
                "finished. This should not happen - tell the developers about this error.",
            )
        return self.done

    @override
    def is_job_possible(self) -> bool:
        return self.is_possible

    @override
    @classmethod
    def get_finalize_success_request_type(cls) -> type[ImageGenerateStatusRequest]:
        return ImageGenerateStatusRequest


class ImageGenerateCheckRequest(BaseAIHordeRequest, JobRequestMixin):
    """Represents a GET request to the `/v2/generate/check/{id}` endpoint."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_check

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateCheckResponse]:
        return ImageGenerateCheckResponse
