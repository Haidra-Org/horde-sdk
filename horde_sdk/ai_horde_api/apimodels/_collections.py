from enum import auto
from typing import Literal

from pydantic import BaseModel, Field
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
    HordeAPIData,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)


class ResponseModelStylesShort(HordeAPIObjectBaseModel):
    name: str = Field(
        description="The unique name for this style",
    )
    id_: str = Field(
        alias="id",
        description="The ID of this style",
    )


class ResponseModelCollection(HordeResponseBaseModel):
    id: str
    """The UUID of the collection. Use this to use this collection of retrieve its information in the future."""

    name: str = Field()
    """The name for the collection. Case-sensitive and unique per user."""

    type: Literal["image"] = Field()
    """The kind of styles stored in this collection."""

    info: str | None = Field(default=None)
    """Extra information about this collection."""

    public: bool = Field(default=True)
    """When true this collection will be listed among all collection publicly.When false, information about this
    collection can only be seen by people who know its ID or name."""

    styles: list[ResponseModelStylesShort] = Field()
    """The styles contained in this collection."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "ResponseModelCollection"


class AllCollectionsResponse(HordeResponseRootModel[list[ResponseModelCollection]]):

    root: list[ResponseModelCollection]
    """The underlying list of collections."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _ANONYMOUS_MODEL


class AllCollectionsRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/collections` endpoint.

    v2 API Model: `CollectionsInput`
    """

    sort: Literal["popular", "age"] = Field(
        default="popular",
        description="The sort order for the collections.",
    )

    page: int = Field(
        default=1,
        description="The page number for the collections. Each page has 25 styles.",
    )

    type_: Literal["image", "text", "all"] = Field(
        alias="type",
        default="all",
        description="The type of collections to retrieve.",
    )

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
    def get_query_fields(cls) -> list[str]:
        return ["sort", "page", "type"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AllCollectionsResponse]:
        return AllCollectionsResponse


class CollectionByIDRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/collections/{collection_id}` endpoint.

    v2 API Model: `CollectionsInput`
    """

    collection_id: str = Field(
        description="The ID of the collection.",
    )

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ResponseModelCollection]:
        return ResponseModelCollection


class CollectionByNameRequest(BaseAIHordeRequest):
    """Represents the data needed to make a request to the `/v2/collection_by_name/{collection_name}` endpoint.

    v2 API Model: `CollectionsInput`
    """

    collection_name: str = Field(
        description="The name of the collection.",
    )

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections_by_name

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ResponseModelCollection]:
        return ResponseModelCollection


class CreateCollectionResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
):
    id_: str = Field(
        alias="id",
        description="The ID of the collection.",
    )

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "StyleModify"


class _InputModelCollectionMixin(HordeAPIData):
    name: str = Field(
        min_length=1,
        max_length=100,
    )
    """The name for the collection. Case-sensitive and unique per user."""

    info: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    """Extra information about this collection."""

    public: bool = Field(
        default=True,
    )
    """When true this collection will be listed among all collections publicly.When false, information about this
    collection can only be seen by people who know its ID or name."""

    styles: list[str] = Field(
        min_length=1,
    )
    """The styles to use in this collection."""


class CreateCollectionRequest(
    _InputModelCollectionMixin,
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InputModelCollection"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[CreateCollectionResponse]:
        return CreateCollectionResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteCollectionResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "SimpleResponse"


class DeleteCollectionRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    collection_id: str = Field(
        description="The ID of the collection.",
    )

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteCollectionResponse]:
        return DeleteCollectionResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class UpdateCollectionResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "StyleModify"


class UpdateCollectionRequest(
    _InputModelCollectionMixin,
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    collection_id: str
    """The ID of the collection to update."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "InputModelCollection"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_collections_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[UpdateCollectionResponse]:
        return UpdateCollectionResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
