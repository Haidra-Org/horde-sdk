from pydantic import field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, MessageSpecifiesSharedKeyMixin
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObject,
    HordeResponseBaseModel,
)


class SharedKeySettings(HordeAPIObject):
    """Represents the settings for a SharedKey.

    v2 API Model: `SharedKeyInput`
    """

    kudos: int
    """The Kudos limit assigned to this key."""
    expiry: str
    """The date at which this API key will expire."""
    name: str
    """The Shared Key Name."""
    max_image_pixels: int
    """The maximum amount of image pixels this key can generate per job. -1 means unlimited."""
    max_image_steps: int
    """The maximum amount of image steps this key can use per job. -1 means unlimited."""
    max_text_tokens: int
    """The maximum amount of text tokens this key can generate per job. -1 means unlimited."""

    @field_validator("max_image_pixels", "max_image_steps", "max_text_tokens", mode="before")
    @classmethod
    def validate_restriction_values(cls, v: int) -> int:
        """Validate the restriction values.

        Args:
            v (int): The restriction value.

        Raises:
            ValueError: If the restriction value is invalid.

        Returns:
            int: The restriction value.
        """
        if v < -1:
            raise ValueError("Restriction values must be -1 or greater.")
        return v

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SharedKeyInput"


class SharedKeyDetailsResponse(HordeResponseBaseModel, MessageSpecifiesSharedKeyMixin, SharedKeySettings):
    """Represents the data returned from the `/v2/sharedkeys/{sharedkey_id}` endpoint.

    v2 API Model: `SharedKeyDetails`
    """

    username: str
    """The owning user's unique Username. It is a combination of their chosen alias plus their ID."""
    utilized: int
    """How much kudos has been utilized via this shared key until now."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SharedKeyDetails"

    @field_validator("max_image_pixels", "max_image_steps", "max_text_tokens", mode="before")
    @classmethod
    def validate_restriction_values(cls, v: int) -> int:
        """Validate the restriction values.

        Args:
            v (int): The restriction value.

        Raises:
            ValueError: If the restriction value is invalid.

        Returns:
            int: The restriction value.
        """
        if v < -1:
            raise ValueError("Restriction values must be -1 or greater.")
        return v


class SharedKeyDetailsRequest(BaseAIHordeRequest, MessageSpecifiesSharedKeyMixin):
    """Represents the request data for the `/v2/sharedkeys/{sharedkey_id}` endpoint.

    v2 API Model: `SharedKeyDetails`
    """

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_sharedkeys

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SharedKeyDetailsResponse]:
        return SharedKeyDetailsResponse


class SharedKeyDeleteResponse(HordeResponseBaseModel, ContainsMessageResponseMixin):
    """Represents the data returned from the DELETE `/v2/sharedkeys/{sharedkey_id}` endpoint.

    v2 API Model: None (`message` only)
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None


class SharedKeyDeleteRequest(
    BaseAIHordeRequest,
    MessageSpecifiesSharedKeyMixin,
    APIKeyAllowedInRequestMixin,
):
    """Represents the request data for the `/v2/sharedkeys/{sharedkey_id}` endpoint.

    v2 API Model: None
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return None

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.DELETE

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_sharedkeys

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SharedKeyDeleteResponse]:
        return SharedKeyDeleteResponse


class SharedKeyModifyRequest(
    BaseAIHordeRequest,
    SharedKeySettings,
    MessageSpecifiesSharedKeyMixin,
    APIKeyAllowedInRequestMixin,
):
    """Represents the request data for the PATCH `/v2/sharedkeys/{sharedkey_id}` endpoint.

    v2 API Model: `SharedKeyModify`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SharedKeyInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_sharedkeys

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SharedKeyDetailsResponse]:
        return SharedKeyDetailsResponse


class SharedKeyCreateRequest(
    BaseAIHordeRequest,
    SharedKeySettings,
    APIKeyAllowedInRequestMixin,
):
    """Represents the request data for the POST `/v2/sharedkeys` endpoint.

    v2 API Model: `SharedKeyCreate`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SharedKeyInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_sharedkeys_create

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SharedKeyDetailsResponse]:
        return SharedKeyDetailsResponse
