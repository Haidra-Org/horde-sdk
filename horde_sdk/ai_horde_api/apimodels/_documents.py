from loguru import logger
from pydantic import field_validator
from strenum import StrEnum
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    HordeAPIObject,
    HordeResponseBaseModel,
)


class DocumentFormat(StrEnum):
    html = "html"
    markdown = "markdown"


class HordeDocument(HordeResponseBaseModel):
    html: str | None = None
    """The HTML content of the document, if requested."""
    markdown: str | None = None
    """The markdown content of the document, if requested."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str:
        return "HordeDocument"


class AIHordeDocumentRequestMixin(HordeAPIObject):
    format: DocumentFormat | str = DocumentFormat.html

    """The format of the document to return. Default is markdown."""

    @field_validator("format")
    def validate_format(cls, value: DocumentFormat | str) -> DocumentFormat | str:
        if isinstance(value, DocumentFormat):
            return value

        try:
            DocumentFormat(value)
        except ValueError:
            logger.warning(f"Unknown document format: {value}. Is your SDK out of date or did the API change?")

        return value


class AIHordeGetPrivacyPolicyRequest(BaseAIHordeRequest, AIHordeDocumentRequestMixin):

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_documents_privacy

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeDocument]:
        return HordeDocument


class AIHordeGetSponsorsRequest(BaseAIHordeRequest, AIHordeDocumentRequestMixin):

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_documents_sponsors

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeDocument]:
        return HordeDocument


class AIHordeGetTermsRequest(BaseAIHordeRequest, AIHordeDocumentRequestMixin):

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
        return AI_HORDE_API_ENDPOINT_SUBPATH.vs_documents_terms

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[HordeDocument]:
        return HordeDocument
