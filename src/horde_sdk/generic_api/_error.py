from collections.abc import Callable

from typing_extensions import override

from horde_sdk.consts import HTTPStatusCode
from horde_sdk.generic_api.apimodels import BaseResponse


class RequestErrorResponse(BaseResponse):
    """The catch all error response for any request to any Horde API.

    v2 API Model: `RequestError`
    """

    message: str

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestError"

    @override
    @classmethod
    def get_expected_http_status_codes(cls) -> dict[HTTPStatusCode, Callable]:
        def dummy_func(x):
            return x

        return {
            HTTPStatusCode.BAD_REQUEST: dummy_func,
            HTTPStatusCode.UNAUTHORIZED: dummy_func,
            HTTPStatusCode.FORBIDDEN: dummy_func,
            HTTPStatusCode.NOT_FOUND: dummy_func,
            HTTPStatusCode.METHOD_NOT_ALLOWED: dummy_func,
            HTTPStatusCode.NOT_ACCEPTABLE: dummy_func,
            HTTPStatusCode.REQUEST_TIMEOUT: dummy_func,
            HTTPStatusCode.CONFLICT: dummy_func,
            HTTPStatusCode.GONE: dummy_func,
            HTTPStatusCode.UNPROCESSABLE_ENTITY: dummy_func,
            HTTPStatusCode.TOO_MANY_REQUESTS: dummy_func,
            HTTPStatusCode.INTERNAL_SERVER_ERROR: dummy_func,
            HTTPStatusCode.NOT_IMPLEMENTED: dummy_func,
            HTTPStatusCode.SERVICE_UNAVAILABLE: dummy_func,
            HTTPStatusCode.GATEWAY_TIMEOUT: dummy_func,
        }
