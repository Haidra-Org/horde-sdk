from pydantic import field_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, MessageSpecifiesSharedKeyMixin
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
)


class SharedKeySettings(HordeAPIObjectBaseModel):
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
    """Information about a SharedKey, including its creating user, settings and utilization.

    The data returned in this response can vary depending on the user's permissions, (creator, owner, or admin).

    Represents the data returned from the following endpoints and http status codes:
        - /v2/sharedkeys/{sharedkey_id} | SharedKeyModifyRequest [PATCH] -> 200
        - /v2/sharedkeys/{sharedkey_id} | SharedKeyDetailsRequest [GET] -> 200
        - /v2/sharedkeys | SharedKeyCreateRequest [PUT] -> 200

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
    """Request the details of a SharedKey, including its creating user, settings, and utilization.

    The response data can vary depending on the user's permissions, (e.g., if they are a creator, owner, or admin).

    Represents a GET request to the /v2/sharedkeys/{sharedkey_id} endpoint.
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
    """Indicates that a SharedKey was successfully deleted.

    Represents the data returned from the /v2/sharedkeys/{sharedkey_id} endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SimpleResponse"


class SharedKeyDeleteRequest(
    BaseAIHordeRequest,
    MessageSpecifiesSharedKeyMixin,
    APIKeyAllowedInRequestMixin,
):
    """Request to delete a SharedKey.

    This is a privileged operation that requires the user to be the owner, a moderator, or an admin.

    Represents a DELETE request to the /v2/sharedkeys/{sharedkey_id} endpoint.
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
    """Request to modify a SharedKey.

    This is a privileged operation that requires the user to be the owner, a moderator, or an admin.

    Represents a PATCH request to the /v2/sharedkeys/{sharedkey_id} endpoint.

    v2 API Model: `SharedKeyInput`
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
    """Request to create a new SharedKey.

    Represents a PUT request to the /v2/sharedkeys endpoint.

    v2 API Model: `SharedKeyInput`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SharedKeyInput"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PUT

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_sharedkeys_create

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[SharedKeyDetailsResponse]:
        return SharedKeyDetailsResponse
