from loguru import logger
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, JobRequestMixin
from horde_sdk.ai_horde_api.apimodels.generate._progress import ResponseGenerationProgressMixin
from horde_sdk.ai_horde_api.apimodels.generate._status import ImageGenerateStatusRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse, ResponseWithProgressMixin


class ImageGenerateCheckResponse(
    BaseResponse,
    ResponseWithProgressMixin,
    ResponseGenerationProgressMixin,
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

    @classmethod
    def get_finalize_success_request_type(cls) -> type[ImageGenerateStatusRequest] | None:
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
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_generate_check

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ImageGenerateCheckResponse]:
        return ImageGenerateCheckResponse
