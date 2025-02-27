from typing import Literal

from pydantic import Field
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class _ResponseModelMessageData(HordeAPIObjectBaseModel):
    worker_id: str | None = None
    """The ID of the worker that the message is for."""
    message: str
    """The message."""
    origin: str | None = None
    """The origin of the message."""
    expiry: int | None = None
    """The number of hours after which this message expires."""


class ResponseModelMessage(HordeResponseBaseModel, _ResponseModelMessageData):

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ResponseModelMessage"


@Unhashable
@Unequatable
class ResponseModelMessages(HordeResponseRootModel[list[ResponseModelMessage]]):

    root: list[ResponseModelMessage]
    """The underlying list of messages."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class AllWorkerMessagesRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    user_id: str | None = None
    """The ID of the user to retrieve messages for. If not specified, all messages will be retrieved."""
    worker_id: str | None = None
    """The ID of the worker to retrieve messages for. If not specified, all messages will be retrieved."""
    validity: Literal["active", "expired", "all"] = "active"
    """The validity of the messages to retrieve."""
    page: int = 1
    """The page of messages to retrieve. Each page has 50 messages."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["validity", "page"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_messages

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ResponseModelMessages]:
        return ResponseModelMessages

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class SingleWorkerMessageRequest(
    BaseAIHordeRequest,
):
    message_id: str = Field(alias="id")
    """The ID of the message to retrieve."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_messages_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ResponseModelMessage]:
        return ResponseModelMessage


class CreateWorkerMessageRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    _ResponseModelMessageData,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ResponseModelMessage"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_messages

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ResponseModelMessage]:
        return ResponseModelMessage

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteWorkerMessageResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteWorkerMessageRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    message_id: str = Field(alias="id")
    """The ID of the message to delete."""

    @override
    @classmethod
    def get_api_model_name(cls) -> None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_workers_messages_single

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteWorkerMessageResponse]:
        return DeleteWorkerMessageResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
