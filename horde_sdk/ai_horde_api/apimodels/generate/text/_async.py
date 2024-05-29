from __future__ import annotations

from loguru import logger
from pydantic import Field, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    BaseAIHordeRequest,
    ExtraSourceImageEntry,
    JobResponseMixin,
    SingleWarningEntry,
)
from horde_sdk.ai_horde_api.apimodels.generate.text._status import DeleteTextGenerateRequest, TextGenerateStatusRequest
from horde_sdk.ai_horde_api.endpoints import AI_HORDE_API_ENDPOINT_SUBPATH
from horde_sdk.consts import _ANONYMOUS_MODEL, HTTPMethod, HTTPStatusCode
from horde_sdk.generic_api.apimodels import (
    APIKeyAllowedInRequestMixin,
    ContainsMessageResponseMixin,
    HordeAPIDataObject,
    HordeResponse,
    HordeResponseBaseModel,
    RequestUsesWorkerMixin,
    ResponseRequiringFollowUpMixin,
)
from horde_sdk.generic_api.decoration import Unhashable


class TextGenerateAsyncResponse(
    HordeResponseBaseModel,
    JobResponseMixin,
    ResponseRequiringFollowUpMixin,
    ContainsMessageResponseMixin,
):
    kudos: float | None = Field(
        None,
    )
    """The expected kudos consumption for this request."""
    warnings: list[SingleWarningEntry] | None = None
    """Any warnings that were generated by the server or a serving worker."""

    @model_validator(mode="after")
    def validate_warnings(self) -> TextGenerateAsyncResponse:
        if self.warnings is None:
            return self

        for warning in self.warnings:
            logger.warning(f"Warning from server ({warning.code}): {warning.message}")

        return self

    @override
    def get_follow_up_returned_params(self, *, as_python_field_name: bool = False) -> list[dict[str, object]]:
        if as_python_field_name:
            return [{"id_": self.id_}]
        return [{"id": self.id_}]

    @classmethod
    def get_follow_up_default_request_type(cls) -> type[TextGenerateStatusRequest]:
        return TextGenerateStatusRequest

    @override
    @classmethod
    def get_follow_up_request_types(  # type: ignore[override]
        cls,
    ) -> list[type[TextGenerateStatusRequest]]:
        return [TextGenerateStatusRequest]

    @override
    @classmethod
    def get_follow_up_failure_cleanup_request_type(cls) -> type[DeleteTextGenerateRequest]:
        return DeleteTextGenerateRequest

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "RequestAsync"

    def __hash__(self) -> int:
        return hash(TextGenerateAsyncResponse.__name__) + hash(self.id_)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, TextGenerateAsyncResponse) and self.id_ == __value.id_


@Unhashable
class ModelPayloadRootKobold(HordeAPIDataObject):
    dynatemp_exponent: float | None = Field(1, ge=0.0, le=5.0)
    """Dynamic temperature exponent value."""
    dynatemp_range: float | None = Field(0, ge=0.0, le=5.0)
    """Dynamic temperature range value."""
    frmtadsnsp: bool | None = Field(
        None,
        description=(
            "Input formatting option. When enabled, adds a leading space to your input if there is no trailing"
            " whitespace at the end of the previous action."
        ),
        examples=[
            False,
        ],
    )
    """Input formatting option. When enabled, adds a leading space to your input if there is no trailing whitespace at
    the end of the previous action."""
    frmtrmblln: bool | None = Field(
        None,
        description=(
            "Output formatting option. When enabled, replaces all occurrences of two or more consecutive newlines in"
            " the output with one newline."
        ),
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, replaces all occurrences of two or more consecutive newlines in the
    output with one newline."""
    frmtrmspch: bool | None = Field(
        None,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes #/@%}{+=~|\\^<> from the output."""
    frmttriminc: bool | None = Field(
        None,
        description=(
            "Output formatting option. When enabled, removes some characters from the end of the output such that the"
            " output doesn't end in the middle of a sentence. If the output is less than one sentence long, does"
            " nothing."
        ),
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes some characters from the end of the output such that the output
    doesn't end in the middle of a sentence. If the output is less than one sentence long, does nothing."""
    max_context_length: int | None = Field(
        1024,
        ge=80,
        le=32000,
    )
    """Maximum number of tokens to send to the model."""
    max_length: int | None = Field(80, ge=16, le=1024)
    """Number of tokens to generate."""
    min_p: float | None = Field(0, ge=0.0, le=1.0)
    """Min-p sampling value."""
    n: int | None = Field(None, examples=[1], ge=1, le=20)
    """The number of generations to produce."""
    rep_pen: float | None = Field(None, ge=1.0, le=3.0)
    """Base repetition penalty value."""
    rep_pen_range: int | None = Field(None, ge=0, le=4096)
    """Repetition penalty range."""
    rep_pen_slope: float | None = Field(None, ge=0.0, le=10.0)
    """Repetition penalty slope."""
    sampler_order: list[int] | None = None
    """The sampler order to use for the generation."""
    singleline: bool | None = Field(
        None,
        description=(
            "Output formatting option. When enabled, removes everything after the first line of the output, including"
            " the newline."
        ),
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes everything after the first line of the output, including the
    newline."""
    smoothing_factor: float | None = Field(0, ge=0.0, le=10.0)
    """Quadratic sampling value."""
    stop_sequence: list[str] | None = None
    """The stop sequences to use for the generation."""
    temperature: float | None = Field(None, ge=0.0, le=5.0)
    """Temperature value."""
    tfs: float | None = Field(None, ge=0.0, le=1.0)
    """Tail free sampling value."""
    top_a: float | None = Field(None, ge=0.0, le=1.0)
    """Top-a sampling value."""
    top_k: int | None = Field(None, ge=0, le=100)
    """Top-k sampling value."""
    top_p: float | None = Field(None, ge=0.001, le=1.0)
    """Top-p sampling value."""
    typical: float | None = Field(None, ge=0.0, le=1.0)
    """Typical sampling value."""
    use_default_badwordsids: bool | None = None
    """When True, uses the default KoboldAI bad word IDs."""


@Unhashable
class ModelGenerationInputKobold(ModelPayloadRootKobold):

    pass


class TextGenerateAsyncDryRunResponse(HordeResponseBaseModel):
    kudos: float
    """The expected kudos consumption for this request."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return _ANONYMOUS_MODEL


@Unhashable
class TextGenerateAsyncRequest(
    BaseAIHordeRequest,
    APIKeyAllowedInRequestMixin,
    RequestUsesWorkerMixin,
):
    """Represents the data needed to make a request to the `/v2/generate/async` endpoint.

    v2 API Model: `GenerationInputKobold`
    """

    params: ModelGenerationInputKobold | None = None
    """The parameters to use for the generation."""
    prompt: str | None = None
    """The prompt which will be sent to KoboldAI to generate text."""

    allow_downgrade: bool | None = Field(False)
    """When true and the request requires upfront kudos and the account does not have enough The request will be
    downgraded in max context and max tokens so that it does not need upfront kudos."""
    disable_batching: bool | None = Field(False)
    """When true, This request will not use batching. This will allow you to retrieve accurate seeds.
    Feature is restricted to Trusted users and Patreons."""
    extra_source_images: list[ExtraSourceImageEntry] | None = None
    """Any extra source images that should be used for this request; e.g., for multi-modal models."""
    proxied_account: str | None = Field(None)
    """If using a service account as a proxy, provide this value to identify the actual account from which this
    request is coming from."""
    softprompt: str | None = Field(
        None,
        min_length=1,
    )
    """Specify which softprompt needs to be used to service this request."""
    webhook: str | None = Field(None)
    """Provide a URL where the AI Horde will send a POST call after each delivered generation.
    The request will include the details of the job as well as the request ID."""

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationInputKobold"

    @override
    @classmethod
    def get_http_method(cls) -> HTTPMethod:
        return HTTPMethod.POST

    @override
    @classmethod
    def get_api_endpoint_subpath(cls) -> AI_HORDE_API_ENDPOINT_SUBPATH:
        return AI_HORDE_API_ENDPOINT_SUBPATH.v2_generate_text_async

    @override
    @classmethod
    def get_default_success_response_type(cls) -> type[TextGenerateAsyncResponse]:
        return TextGenerateAsyncResponse

    @override
    @classmethod
    def get_success_status_response_pairs(cls) -> dict[HTTPStatusCode, type[HordeResponse]]:
        return {
            HTTPStatusCode.OK: TextGenerateAsyncDryRunResponse,
            HTTPStatusCode.ACCEPTED: cls.get_default_success_response_type(),
        }

    @override
    def get_extra_fields_to_exclude_from_log(self) -> set[str]:
        return {"extra_source_images"}
