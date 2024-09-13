import base64
import urllib.parse

from loguru import logger
from pydantic import field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.alchemy._status import AlchemyDeleteRequest, AlchemyStatusRequest
from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    JobResponseMixin,
)
from horde_sdk.ai_horde_api.consts import KNOWN_ALCHEMY_TYPES
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.metadata import AIHordePathData
from horde_sdk.consts import HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIDataObject,
    HordeResponse,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


class AlchemyAsyncResponse(
    HordeResponseBaseModel,
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
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{AIHordePathData.id_: self.id_}]

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[AlchemyStatusRequest]:
        return AlchemyStatusRequest

    @override
    @classmethod
    def get_follow_up_request_types(  # type: ignore[override]
        cls,
    ) -> list[type[AlchemyStatusRequest]]:
        return [AlchemyStatusRequest]

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[AlchemyDeleteRequest]:
        return AlchemyDeleteRequest


class AlchemyAsyncRequestFormItem(HordeAPIDataObject):
    name: KNOWN_ALCHEMY_TYPES | str

    @field_validator("name")
    def check_name(cls, v: KNOWN_ALCHEMY_TYPES | str) -> KNOWN_ALCHEMY_TYPES | str:
        if isinstance(v, KNOWN_ALCHEMY_TYPES):
            return v
        if str(v) not in KNOWN_ALCHEMY_TYPES.__members__:
            logger.warning(f"Unknown alchemy form name {v}. Is your SDK out of date or did the API change?")
        return v


class AlchemyAsyncRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    forms: list[AlchemyAsyncRequestFormItem]
    """The list of forms (types of post-processing/interrogation/captioning/etc) to request."""
    source_image: str
    """The public URL of the source image or a base64 string to use."""
    slow_workers: bool = True
    """Whether to use the slower workers. Costs additional kudos if `False`."""
    extra_slow_workers: bool = False
    """Whether to use the super slow workers."""

    @field_validator("forms")
    def check_at_least_one_form(cls, v: list[AlchemyAsyncRequestFormItem]) -> list[AlchemyAsyncRequestFormItem]:
        if not v:
            raise ValueError("At least one form must be provided.")
        return v

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
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_interrogate_async

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AlchemyAsyncResponse]:
        return AlchemyAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponse]]:
        return {
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }

    @override
    def get_number_of_results_expected(self) -> int:
        return len(self.forms)

    @override
    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        return {"source_image"}
