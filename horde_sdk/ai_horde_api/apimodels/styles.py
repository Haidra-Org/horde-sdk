from enum import auto
from typing import Literal

from pydantic import Field
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest, _BaseImageGenerateParamMixin
from horde_sdk.ai_horde_api.apimodels.generate.text.async_ import _BasePayloadKoboldMixin
from horde_sdk.ai_horde_api.apimodels.sharedkeys import SharedKeyDetailsResponse
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
    HordeAPIObjectBaseModel,
    HordeResponseBaseModel,
    HordeResponseRootModel,
)
from horde_sdk.generic_api.decoration import Unequatable, Unhashable


class StyleType(StrEnum):
    """An enum representing the different types of styles."""

    image = auto()
    text = auto()


class ResponseModelStylesUser(HordeAPIObjectBaseModel):
    """Represents a style created by a user.

    v2 API Model: `ResponseModelStylesUser`
    """

    name: str
    """The name of the style."""
    id_: str = Field(alias="id")
    """The ID of the style."""
    type_: StyleType = Field(alias="type")
    """The type of the style."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ResponseModelStylesUser"


class StyleExample(HordeAPIObjectBaseModel):
    """Represents an example of an image generated by a style.

    v2 API Model: `StyleExample`
    """

    url: str = Field(
        examples=[
            "https://lemmy.dbzer0.com/pictrs/image/c9915186-ca30-4f5a-873c-a91287fb4419.webp",
        ],
    )
    """The URL of the image generated by this style."""

    primary: bool = False
    """When true this image is to be used as the primary example for this style."""

    id_: str = Field(alias="id")
    """The UUID of this example."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleExample"


class ModelStyleInputParamsStable(_BaseImageGenerateParamMixin):
    """The default parameters to use for all generations using a particular style.

    v2 API Model: `ModelStyleInputParamsStable`
    """

    steps: int = Field(
        default=20,
        examples=[
            20,
        ],
    )
    """The number of steps to use for the generation."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStyleInputParamsStable"


@Unhashable
@Unequatable
class _StyleMixin(HordeAPIObjectBaseModel):
    """A mixin representing the common fields of a style."""

    name: str
    """The name of the style."""

    info: str | None = Field(
        default=None,
        examples=[
            "photorealism excellence.",
        ],
    )
    """Extra information or comments about this style provided by its creator."""

    prompt: str
    """The prompt template which will be sent to generate an image.

    The user's prompt will be injected into this. This argument MUST include a '{p}' which specifies the part where \
    the user's prompt will be injected and an '{np}' where the user's negative prompt will be injected (if any)"""

    public: bool = True
    """When true this style will be listed among all styles publicly.

    When false, information about this style can only be seen by people who know its ID or name."""

    nsfw: bool = False
    """When true, it signified this style is expected to generate NSFW images primarily."""

    tags: list[str] | None = Field(
        default=None,
        examples=[
            "photorealistic",
        ],
    )
    """Tags associated with this style."""

    models: list[str] | None = None
    """The models which this style will attempt to use."""


class _StyleResponseMixin(_StyleMixin):
    """A mixin representing the common fields of a style endpoint response."""

    id_: str = Field(alias="id")
    """The UUID of the style. Use this to use the style or retrieve its information in the future."""

    creator: str | None = Field(
        default=None,
        examples=["db0#1"],
    )
    """The alias of the user which created this style."""

    use_count: int | None = None
    """The amount of times this style has been used in generations."""


@Unhashable
@Unequatable
class StyleStable(HordeResponseBaseModel, _StyleResponseMixin):
    """The details of a style, including its parameters and examples.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/styles/image_by_name/{style_name} | SingleStyleImageByNameRequest [GET] -> 200
        - /v2/styles/image/{style_id} | SingleStyleImageByIDRequest [GET] -> 200

    v2 API Model: `StyleStable`
    """

    params: ModelStyleInputParamsStable | None = None
    """The parameters to use for all generations using this style, if not set by the user."""

    examples: list[StyleExample] | None = None
    """A list of examples of images generated by this style."""
    shared_key: SharedKeyDetailsResponse | None = None
    """The shared key backing this style, if any."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleStable"


@Unhashable
@Unequatable
class AllStylesImageResponse(HordeResponseRootModel[list[StyleStable]]):
    """The a list of styles.

    Represents the data returned from the /v2/styles/image endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    root: list[StyleStable]
    """The underlying list of styles."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class AllStylesImageRequest(
    BaseAIHordeRequest,
):
    """Request to get image styles. Use `page` to paginate through the results.

    Represents a GET request to the /v2/styles/image endpoint.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    sort: Literal["popular", "age"] = "popular"
    """The sort order of the styles."""

    page: int = 1
    """The page of styles to retrieve. Each page has 25 styles."""

    tag: str | None = None
    """If specified, return only styles with this tag."""

    model: str | None = None
    """If specified, return only styles which use this model."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.GET

    @override
    @classmethod
    def get_query_fields(cls) -> list[str]:
        return ["sort", "page", "tag", "model"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AllStylesImageResponse]:
        return AllStylesImageResponse


class SingleStyleImageByIDRequest(
    BaseAIHordeRequest,
):
    """Request to get a single image style by its ID.

    Represents a GET request to the /v2/styles/image/{style_id} endpoint.
    """

    style_id: str
    """The ID of the style to retrieve."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleStable]:
        return StyleStable


class SingleStyleImageByNameRequest(
    BaseAIHordeRequest,
):
    """Request to get a single image style by its name.

    Represents a GET request to the /v2/styles/image_by_name/{style_name} endpoint.
    """

    style_name: str
    """The name of the style to retrieve."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_by_name

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleStable]:
        return StyleStable


class ModifyStyleImageResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
):
    """The response to modifying an image style, including any warnings.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/styles/image/{style_id} | ModifyStyleImageRequest [PATCH] -> 200
        - /v2/styles/image | CreateStyleImageRequest [POST] -> 200

    v2 API Model: `StyleModify`
    """

    id_: str = Field(alias="id")
    """The ID of the style."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleModify"


class CreateStyleImageRequest(
    _StyleMixin,
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a POST request to the /v2/styles/image endpoint.

    v2 API Model: `ModelStyleInputStable`
    """

    params: ModelStyleInputParamsStable
    """The parameters to use for all generations using this style, if not set by the user."""

    sharedkey: str | None = Field(
        default=None,
        examples=[
            "00000000-0000-0000-0000-000000000000",
        ],
        min_length=36,
        max_length=36,
    )
    """The UUID of a shared key which will be used to fulfil this style when active."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStyleInputStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyStyleImageResponse]:
        return ModifyStyleImageResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class ModifyStyleImageRequest(
    _StyleMixin,
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a PATCH request to the /v2/styles/image/{style_id} endpoint.

    v2 API Model: `ModelStylePatchStable`
    """

    style_id: str
    """The ID of the style to modify."""

    params: ModelStyleInputParamsStable
    """The parameters to use for all generations using this style, if not set by the user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStylePatchStable"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyStyleImageResponse]:
        return ModifyStyleImageResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteStyleImageResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    """Indicates that a style was successfully deleted.

    Represents the data returned from the /v2/styles/image/{style_id} endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteStyleImageRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a DELETE request to the /v2/styles/image/{style_id} endpoint."""

    style_id: str
    """The ID of the style to delete."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteStyleImageResponse]:
        return DeleteStyleImageResponse


class StyleImageExampleModifyResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
):
    """The response to modifying an image style example, including any warnings.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/styles/image/{style_id}/example/{example_id} | StyleImageExampleModifyRequest [PATCH] -> 200
        - /v2/styles/image/{style_id}/example | StyleImageExampleAddRequest [POST] -> 200

    v2 API Model: `StyleModify`
    """

    id_: str = Field(alias="id")
    """The ID of the example."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleModify"


class StyleImageExampleAddRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a POST request to the /v2/styles/image/{style_id}/example endpoint.

    v2 API Model: `InputStyleExamplePost`
    """

    style_id: str
    """The ID of the style to add the example to."""

    url: str
    """The URL of the image to add as an example."""

    primary: bool = False
    """When true this image is to be used as the primary example for this style."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "InputStyleExamplePost"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_example_by_style_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleImageExampleModifyResponse]:
        return StyleImageExampleModifyResponse


class StyleImageExampleDeleteResponse(HordeResponseBaseModel, ContainsMessageResponseMixin):
    """Indicates that an example was successfully deleted.

    Represents the data returned from the /v2/styles/image/{style_id}/example/{example_id} endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class StyleImageExampleDeleteRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a DELETE request to the /v2/styles/image/{style_id}/example/{example_id} endpoint."""

    style_id: str
    """The ID of the style to delete the example from."""

    example_id: str
    """The ID of the example to delete."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_example_by_style_id_example_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleImageExampleDeleteResponse]:
        return StyleImageExampleDeleteResponse


class StyleImageExampleModifyRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Represents a PATCH request to the /v2/styles/image/{style_id}/example/{example_id} endpoint.

    v2 API Model: `InputStyleExamplePost`
    """

    style_id: str
    """The ID of the style to modify the example of."""

    example_id: str
    """The ID of the example to modify."""

    url: str
    """The URL of the image to add as an example."""

    primary: bool = False
    """When true this image is to be used as the primary example for this style."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "InputStyleExamplePost"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_image_example_by_style_id_example_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleImageExampleModifyResponse]:
        return StyleImageExampleModifyResponse


class ModelStyleInputParamsKobold(HordeResponseBaseModel, _BasePayloadKoboldMixin):
    """The parameters than can be set for a text generation style.

    v2 API Model: `ModelStyleInputParamsKobold`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStyleInputParamsKobold"


class StyleKobold(HordeResponseBaseModel, _StyleResponseMixin):
    """The details of a text style, including its parameters.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/styles/text_by_name/{style_name} | SingleStyleTextByNameRequest [GET] -> 200
        - /v2/styles/text/{style_id} | SingleStyleTextByIDRequest [GET] -> 200

    v2 API Model: `StyleKobold`
    """

    params: ModelStyleInputParamsKobold | None = None
    """The parameters to use for all generations using this style, if not set by the user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleKobold"


@Unhashable
@Unequatable
class AllStylesTextResponse(HordeResponseRootModel[list[StyleKobold]]):
    """A list of text styles.

    Represents the data returned from the /v2/styles/text endpoint with http status code 200.

    v2 API Model: `_ANONYMOUS_MODEL`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return _ANONYMOUS_MODEL


class AllStylesTextRequest(
    BaseAIHordeRequest,
):
    """Request to get text styles. Use `page` to paginate through the results.

    Represents a GET request to the /v2/styles/text endpoint.
    """

    sort: Literal["popular", "age"] = "popular"
    """The sort order of the styles."""

    page: int = 1
    """The page of styles to retrieve. Each page has 25 styles."""

    tag: str | None = None
    """If specified, return only styles with this tag."""

    model: str | None = None
    """If specified, return only styles which use this model."""

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
        return ["sort", "page", "tag", "model"]

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[AllStylesTextResponse]:
        return AllStylesTextResponse


class SingleStyleTextByIDRequest(
    BaseAIHordeRequest,
):
    """Request to get a single text style by its ID.

    Represents a GET request to the /v2/styles/text/{style_id} endpoint.
    """

    style_id: str
    """The ID of the style to retrieve."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleKobold]:
        return StyleKobold


class SingleStyleTextByNameRequest(
    BaseAIHordeRequest,
):
    """Request to get a single text style by its name.

    Represents a GET request to the /v2/styles/text_by_name/{style_name} endpoint.
    """

    style_name: str
    """The name of the style to retrieve."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text_by_name

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[StyleKobold]:
        return StyleKobold


class ModifyStyleTextResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
    ContainsWarningsResponseMixin,
):
    """The response to modifying a text style, including any warnings.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/styles/text/{style_id} | ModifyStyleTextRequest [PATCH] -> 200
        - /v2/styles/text | CreateStyleTextRequest [POST] -> 200

    v2 API Model: `StyleModify`
    """

    id_: str = Field(alias="id")
    """The ID of the style."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "StyleModify"


class CreateStyleTextRequest(
    BaseAIHordeRequest,
    _StyleMixin,
    APIKeyAllowedInRequestMixin,
):
    """Request to create a new text style with the given parameters.

    Represents a POST request to the /v2/styles/text endpoint.

    v2 API Model: `ModelStyleInputKobold`
    """

    params: ModelStyleInputParamsKobold
    """The parameters to use for all generations using this style, if not set by the user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStyleInputKobold"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyStyleTextResponse]:
        return ModifyStyleTextResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class ModifyStyleTextRequest(
    BaseAIHordeRequest,
    _StyleMixin,
    APIKeyAllowedInRequestMixin,
):
    """Represents a PATCH request to the /v2/styles/text/{style_id} endpoint.

    v2 API Model: `ModelStylePatchKobold`
    """

    style_id: str
    """The ID of the style to modify."""

    params: ModelStyleInputParamsKobold
    """The parameters to use for all generations using this style, if not set by the user."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "ModelStylePatchKobold"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.PATCH

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[ModifyStyleTextResponse]:
        return ModifyStyleTextResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True


class DeleteStyleTextResponse(
    HordeResponseBaseModel,
    ContainsMessageResponseMixin,
):
    """Indicates that a style was successfully deleted.

    Represents the data returned from the /v2/styles/text/{style_id} endpoint with http status code 200.

    v2 API Model: `SimpleResponse`
    """

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "SimpleResponse"


class DeleteStyleTextRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
):
    """Request to delete a text style by its ID.

    Note that this is a privileged operation and requires the API key that created the style or
    admin/moderator privileges.

    Represents a DELETE request to the /v2/styles/text/{style_id} endpoint.
    """

    style_id: str
    """The ID of the style to delete."""

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_styles_text_by_id

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[DeleteStyleTextResponse]:
        return DeleteStyleTextResponse

    @override
    @classmethod
    def is_api_key_required(cls) -> bool:
        return True
