from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._base import BaseImageGenerateJobRequest
from horde_sdk.ai_horde_api.apimodels._shared import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_URL_Literals
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse


class ImageGenerateCheckRequest(BaseAIHordeRequest, BaseImageGenerateJobRequest):
    """Represents a GET request to the `/v2/generate/check/{id}` endpoint."""

    __api_model_name__ = None
    __http_method__ = HTTPMethod.GET

    @override
    @staticmethod
    def get_endpoint_subpath() -> str:
        return AI_HORDE_API_URL_Literals.v2_generate_check

    @override
    @staticmethod
    def get_expected_response_type() -> type[BaseResponse]:
        return ImageGenerateCheckResponse


class ImageGenerateCheckResponse(BaseResponse):
    """Represents the data returned from the `/v2/generate/check/{id}` endpoint.

    v2 API Model: `RequestStatusCheck`
    """

    __api_model_name__ = "RequestStatusCheck"

    finished: int
    """The amount of finished jobs in this request."""
    processing: int
    """The amount of still processing jobs in this request."""
    restarted: int
    """The amount of jobs that timed out and had to be restarted or were reported as failed by a worker."""
    waiting: int
    """The amount of jobs waiting to be picked up by a worker."""
    done: bool
    """True when all jobs in this request are done. Else False."""
    faulted: bool = False
    """True when this request caused an internal server error and could not be completed."""
    wait_time: int
    """The expected amount to wait (in seconds) to generate all jobs in this request."""
    queue_position: int
    """The position in the requests queue. This position is determined by relative Kudos amounts."""
    kudos: float
    """The amount of total Kudos this request has consumed until now."""
    is_possible: bool = True
    """If False, this request will not be able to be completed with the pool of workers currently available."""
