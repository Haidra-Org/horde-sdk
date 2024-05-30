from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels._users import UserDetailsResponse
from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import APIKeyAllowedInRequestMixin


class FindUserRequest(BaseAIHordeRequest, APIKeyAllowedInRequestMixin):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_find_user

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[UserDetailsResponse]:
        return UserDetailsResponse
