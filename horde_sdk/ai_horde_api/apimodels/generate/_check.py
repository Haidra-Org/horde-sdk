from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, BaseImageJobRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import BaseResponse


class ImageGenerateCheckResponse(BaseResponse):
    """Represents the data returned from the `/v2/generate/check/{id}` endpoint.

    v2 API Model: `RequestStatusCheck`
    """

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

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestStatusCheck"


class ImageGenerateCheckRequest(BaseAIHordeRequest, BaseImageJobRequest):
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
    def get_success_response_type(cls) -> type[ImageGenerateCheckResponse]:
        return ImageGenerateCheckResponse
