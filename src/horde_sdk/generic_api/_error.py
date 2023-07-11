from typing_extensions import override

from horde_sdk.generic_api.apimodels import BaseResponse


class RequestErrorResponse(BaseResponse):
    """The catch all error response for any request to any Horde API.

    v2 API Model: `RequestError`
    """

    message: str = ""

    object_data: object = None
    """This is a catch all for any additional data that may be returned by the API relevant to the error."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestError"
