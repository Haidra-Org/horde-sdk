from __future__ import annotations

import uuid

import aiohttp
from loguru import logger
from pydantic import Field, field_validator, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import BaseAIHordeRequest
from horde_sdk.ai_horde_api.apimodels.generate._pop import ExtraSourceImageMixin, NoValidRequestFound, PopInput
from horde_sdk.ai_horde_api.apimodels.generate.text._async import ModelPayloadRootKobold
from horde_sdk.ai_horde_api.apimodels.generate.text._status import DeleteTextGenerateRequest, TextGenerateStatusRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.ai_horde_api.fields import JobID
from horde_sdk.consts import HTTPMethod
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)


class ModelPayloadKobold(ModelPayloadRootKobold):
    prompt: str | None = None
    """The prompt for the text generation."""


class NoValidRequestFoundKobold(NoValidRequestFound):
    max_context_length: int | None = Field(default=None)
    """How many waiting requests were skipped because they demanded a higher max_context_length than what this
    worker provides."""
    max_length: int | None = Field(default=None)
    """How many waiting requests were skipped because they demanded a higher max_length than what this
    worker provides."""
    matching_softprompt: int | None = Field(default=None)
    """How many waiting requests were skipped because they demanded an available soft-prompt which this worker does not
    have."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "NoValidRequestFoundKobold"


class TextGenerateJobPopResponse(
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
    ExtraSourceImageMixin,
):
    payload: ModelPayloadKobold
    """The settings for this text generation."""
    id_: JobID | None = Field(default=None, alias="id")
    """The UUID for this text generation."""
    ids: list[JobID]
    """The UUIDs for this text generations."""
    skipped: NoValidRequestFoundKobold = Field(NoValidRequestFoundKobold())
    """The skipped requests that were not valid for this worker."""
    softprompt: str | None = Field(default=None)
    """The soft prompt requested for this generation."""
    model: str | None = Field(default=None)
    """The model requested for this generation."""

    @field_validator("id_", mode="before")
    def validate_id(cls, v: str | JobID) -> JobID | str:
        if isinstance(v, str) and v == "":
            logger.warning("Job ID is empty")
            return JobID(root=uuid.uuid4())

        return v

    @model_validator(mode="after")
    def ids_present(self) -> TextGenerateJobPopResponse:
        """Ensure that either id_ or ids is present."""
        if self.model is None:
            if self.skipped.is_empty():
                logger.debug("No model or skipped data found in response.")
            else:
                logger.debug("No model found in response.")
            return self

        if self.id_ is None and len(self.ids) == 0:
            raise ValueError("Neither id_ nor ids were present in the response.")

        if len(self.ids) > 1:
            logger.debug("Sorting IDs")
            self.ids.sort()

        return self

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationPayloadKobold"

    @override
    @classmethod
    def get_follow_up_default_request_type(cls) -> type[TextGenerateStatusRequest]:
        return TextGenerateStatusRequest

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[DeleteTextGenerateRequest]:
        return DeleteTextGenerateRequest

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{"id": self.id_}]

    @override
    async def async_download_additional_data(self, client_session: aiohttp.ClientSession) -> None:
        await self.async_download_extra_source_images(client_session)

    @override
    def download_additional_data(self) -> None:
        raise NotImplementedError("This method has not been implemented for this class.")

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, TextGenerateJobPopResponse):
            return False

        if self.ids:
            return all(id_ in value.ids for id_ in self.ids)

        return self.id_ == value.id_

    def __hash__(self) -> int:
        if self.ids:
            return hash(tuple(self.ids))

        return hash(self.id_)


class _PopInputKobold(PopInput):
    max_length: int = Field(512)
    """The maximum amount of tokens this worker can generate."""
    max_context_length: int = Field(2048)
    """The max amount of context to submit to this AI for sampling."""
    softprompts: list[str] | None = Field(default=None)
    """The available softprompt files on this worker for the currently running model."""


class TextGenerateJobPopRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    _PopInputKobold,
):
    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "PopInputKobold"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_text_pop

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextGenerateJobPopResponse]:
        return TextGenerateJobPopResponse
