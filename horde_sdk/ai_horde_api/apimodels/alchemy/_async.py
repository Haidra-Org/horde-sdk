import base64
import urllib.parse

from pydantic import BaseModel, field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.alchemy._status import AlchemyDeleteRequest, AlchemyStatusRequest
from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    JobResponseMixin,
)
from horde_sdk.ai_horde_api.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATHS
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    BaseResponse,
    ContainsMessageResponseMixin,
    ResponseRequiringFollowUpMixin,
)


class AlchemyAsyncResponse(
    BaseResponse,
    JobResponseMixin,
    ResponseRequiringFollowUpMixin,
    ContainsMessageResponseMixin,
):
    """Represents the data returned from the `/v2/alchemy/async` endpoint.

    v2 API Model: `RequestInterrogationResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestInterrogationResponse"

    @override
    def get_follow_up_returned_params(self) -> list[dict[str, object]]:
        return [{AIHordePathData.id_: self.id_}]

    @override
    @classmethod
    def get_follow_up_default_request(cls) -> type[AlchemyStatusRequest]:
        return AlchemyStatusRequest

    @override
    @classmethod
    def get_follow_up_request_types(
        cls,
    ) -> list[type[AlchemyStatusRequest]]:
        return [AlchemyStatusRequest]

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[AlchemyDeleteRequest]:
        return AlchemyDeleteRequest


class AlchemyAsyncRequestFormItem(BaseModel):
    name: KNOWN_ALCHEMY_TYPES


class AlchemyAsyncRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    forms: list[AlchemyAsyncRequestFormItem]
    source_image: str
    """The public URL of the source image or a base64 string to use."""
    slow_workers: bool = False
    """Whether to use the slower workers. Costs additional kudos if `True`."""

    @field_validator("source_image")
    def check_source_image(cls, v: str) -> str:
        if "http" in v:
            parsed_url = urllib.parse.urlparse(v)
            if parsed_url.scheme not in ["http", "https"]:
                raise ValueError("Source image must be a public URL.")
        else:
            try:
                base64.b64decode(v)
            except Exception as e:
                raise ValueError("Source image must be a base64 string.") from e

        return v

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ModelInterrogationInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> str:
        return AI_HORDE_API_ENDPOINT_SUBPATHS.v2_interrogate_async

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyAsyncResponse]:
        return AlchemyAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[BaseResponse]]:
        return {
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }
