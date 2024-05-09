from __future__ import annotations

from loguru import logger
from pydantic import Field, model_validator
from typing_extensions import override

from horde_sdk.ai_horde_api.apimodels.base import (
    ExtraSourceImageEntry,
    JobResponseMixin,
    SingleWarningEntry,
)
from horde_sdk.ai_horde_api.apimodels.generate.text._status import DeleteTextGenerateRequest, TextGenerateStatusRequest
from horde_sdk.generic_api.apimodels import (
    ContainsMessageResponseMixin,
    HordeAPIDataObject,
    HordeAPIObject,
    HordeResponseBaseModel,
    ResponseRequiringFollowUpMixin,
)
from horde_sdk.generic_api.decoration import Unhashable


class TextGenerateAsyncResponse(
    HordeResponseBaseModel,
    JobResponseMixin,
    ResponseRequiringFollowUpMixin,
    ContainsMessageResponseMixin,
):
    kudos: float | None = Field(None, description="The expected kudos consumption for this request.")
    warnings: list[SingleWarningEntry] | None = None

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
        return hash(self.id_)

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, TextGenerateAsyncResponse) and self.id_ == __value.id_


@Unhashable
class ModelPayloadRootKobold(HordeAPIDataObject):
    dynatemp_exponent: float | None = Field(1, description="Dynamic temperature exponent value.", ge=0.0, le=5.0)
    dynatemp_range: float | None = Field(0, description="Dynamic temperature range value.", ge=0.0, le=5.0)
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
    frmtrmspch: bool | None = Field(
        None,
        description="Output formatting option. When enabled, removes #/@%}{+=~|\\^<> from the output.",
        examples=[
            False,
        ],
    )
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
    max_context_length: int | None = Field(
        1024,
        description="Maximum number of tokens to send to the model.",
        ge=80,
        le=32000,
    )
    max_length: int | None = Field(80, description="Number of tokens to generate.", ge=16, le=1024)
    min_p: float | None = Field(0, description="Min-p sampling value.", ge=0.0, le=1.0)
    n: int | None = Field(None, examples=[1], ge=1, le=20)
    rep_pen: float | None = Field(None, description="Base repetition penalty value.", ge=1.0, le=3.0)
    rep_pen_range: int | None = Field(None, description="Repetition penalty range.", ge=0, le=4096)
    rep_pen_slope: float | None = Field(None, description="Repetition penalty slope.", ge=0.0, le=10.0)
    sampler_order: list[int] | None = None
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
    smoothing_factor: float | None = Field(0, description="Quadratic sampling value.", ge=0.0, le=10.0)
    stop_sequence: list[str] | None = None
    temperature: float | None = Field(None, description="Temperature value.", ge=0.0, le=5.0)
    tfs: float | None = Field(None, description="Tail free sampling value.", ge=0.0, le=1.0)
    top_a: float | None = Field(None, description="Top-a sampling value.", ge=0.0, le=1.0)
    top_k: int | None = Field(None, description="Top-k sampling value.", ge=0, le=100)
    top_p: float | None = Field(None, description="Top-p sampling value.", ge=0.001, le=1.0)
    typical: float | None = Field(None, description="Typical sampling value.", ge=0.0, le=1.0)
    use_default_badwordsids: bool | None = Field(
        None,
        description="When True, uses the default KoboldAI bad word IDs.",
        examples=[True],
    )


@Unhashable
class ModelGenerationInputKobold(ModelPayloadRootKobold):
    pass


@Unhashable
class TextGenerateAsyncRequest(HordeAPIObject):
    """Represents the data needed to make a request to the `/v2/generate/async` endpoint.

    v2 API Model: `GenerationInputKobold`
    """

    allow_downgrade: bool | None = Field(
        False,
        description=(
            "When true and the request requires upfront kudos and the account does not have enough The request will be"
            " downgraded in max context and max tokens so that it does not need upfront kudos."
        ),
    )
    disable_batching: bool | None = Field(
        False,
        description=(
            "When true, This request will not use batching. This will allow you to retrieve accurate seeds. Feature is"
            " restricted to Trusted users and Patreons."
        ),
    )
    dry_run: bool | None = Field(
        False,
        description="When true, the endpoint will simply return the cost of the request in kudos and exit.",
    )
    extra_source_images: list[ExtraSourceImageEntry] | None = None
    models: list[str] | None = None
    params: ModelGenerationInputKobold | None = None
    prompt: str | None = Field(None, description="The prompt which will be sent to KoboldAI to generate text.")
    proxied_account: str | None = Field(
        None,
        description=(
            "If using a service account as a proxy, provide this value to identify the actual account from which this"
            " request is coming from."
        ),
    )
    slow_workers: bool | None = Field(
        True,
        description=(
            "When True, allows slower workers to pick up this request. Disabling this incurs an extra kudos cost."
        ),
    )
    softprompt: str | None = Field(
        None,
        description="Specify which softpompt needs to be used to service this request.",
        min_length=1,
    )
    trusted_workers: bool | None = Field(
        False,
        description=(
            "When true, only trusted workers will serve this request. When False, Evaluating workers will also be used"
            " which can increase speed but adds more risk!"
        ),
    )
    webhook: str | None = Field(
        None,
        description=(
            "Provide a URL where the AI Horde will send a POST call after each delivered generation. The request will"
            " include the details of the job as well as the request ID."
        ),
    )
    worker_blacklist: bool | None = Field(
        False,
        description="If true, the worker list will be treated as a blacklist instead of a whitelist.",
    )
    workers: list[str] | None = None

    @override
    @classmethod
    def get_api_model_name(cls) -> str | None:
        return "GenerationInputKobold"
