from __future__ import annotations

from pydantic import BaseModel, Field

from horde_sdk.consts import GENERATION_ID_TYPES
from horde_sdk.generation_parameters.generic import BasicModelGenerationParameters, ComposedParameterSetBase


class BasicTextGenerationFormatParameters(BaseModel):  # TODO: Better field names
    """Represent common text generation formatting parameters."""

    frmtadsnsp: bool | None = Field(
        default=None,
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
        default=None,
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
        default=None,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes #/@%}{+=~|\\^<> from the output."""
    frmttriminc: bool | None = Field(
        default=None,
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
    singleline: bool | None = Field(
        default=None,
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


class KoboldAITextGenerationParameters(BaseModel):
    """Represents the parameters when using KoboldAI-based text generation."""

    use_default_bad_words_ids: bool | None = None
    """When True, uses the default KoboldAI bad word IDs."""


class BasicTextGenerationParameters(BasicModelGenerationParameters):  # TODO: Non-AI-Horde specific constraints
    """Represents the common bare minimum parameters for a text generation."""

    prompt: str
    """The prompt to use for the generation."""

    soft_prompt: str | None = None
    """The soft prompt to use for the generation."""

    max_context_length: int | None = Field(
        default=1024,
        ge=80,
        le=32000,
    )
    """Maximum number of tokens to send to the model."""
    max_length: int | None = Field(default=80, ge=16, le=1024)
    """Number of tokens to generate."""

    stop_sequence: list[str] | None = None
    """The stop sequences to use for the generation."""

    temperature: float | None = Field(default=None, ge=0.0, le=5.0)
    """Temperature value."""

    dynamic_temp_exponent: float | None = Field(default=1.0, ge=0.0, le=5.0)
    """Dynamic temperature exponent value."""
    dynamic_temp_range: float | None = Field(default=0.0, ge=0.0, le=5.0)
    """Dynamic temperature range value."""

    tfs: float | None = Field(default=None, ge=0.0, le=1.0)
    """Tail free sampling value."""
    typical: float | None = Field(default=None, ge=0.0, le=1.0)
    """Typical sampling value."""
    sampler_order: list[int] | None = None
    """The sampler order to use for the generation."""
    smoothing_factor: float | None = Field(default=0, ge=0.0, le=10.0)
    """Quadratic sampling value."""

    top_a: float | None = Field(default=None, ge=0.0, le=1.0)
    """Top-a sampling value."""
    top_k: int | None = Field(default=None, ge=0, le=100)
    """Top-k sampling value."""
    top_p: float | None = Field(default=None, ge=0.001, le=1.0)
    """Top-p sampling value."""

    min_p: float | None = Field(default=0, ge=0.0, le=1.0)
    """Min-p sampling value."""
    rep_pen: float | None = Field(default=None, ge=1.0, le=3.0)
    """Base repetition penalty value."""
    rep_pen_range: int | None = Field(default=None, ge=0, le=4096)
    """Repetition penalty range."""
    rep_pen_slope: float | None = Field(default=None, ge=0.0, le=10.0)
    """Repetition penalty slope."""


class TextGenerationParameters(ComposedParameterSetBase):
    """Represents the parameters for a text generation."""

    generation_ids: list[GENERATION_ID_TYPES]
    """The generation IDs to use for the generation."""

    base_params: BasicTextGenerationParameters
    """The basic text generation parameters for the generation."""

    format_params: BasicTextGenerationFormatParameters | None = None
    """The text generation formatting parameters."""

    koboldai_params: KoboldAITextGenerationParameters | None = None
    """The KoboldAI specific generation parameters."""
