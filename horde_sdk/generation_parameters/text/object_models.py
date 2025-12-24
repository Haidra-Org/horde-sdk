from __future__ import annotations

from collections.abc import Sequence
from enum import auto
from typing import Self, override

from pydantic import Field
from strenum import StrEnum

from horde_sdk import get_default_frozen_model_config_dict
from horde_sdk.consts import ID_TYPES
from horde_sdk.generation_parameters.generic import (
    CompositeParametersBase,
    GenerationParameterBaseModel,
    GenerationWithModelParameters,
)
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.utils import (
    ResultIdAllocator,
    TemplateFinalization,
    finalize_template_for_parameters,
    resolve_result_ids_from_payload,
)


class FormatImplementationStandard(StrEnum):
    """The standards for format implementations."""

    KOBOLD_AI = auto()
    """The KoboldAI standard for a format implementation."""


class FormatFeatureFlags(GenerationFeatureFlags):
    """Represents the feature flags for text generation formatting."""

    format_implementation_standard: FormatImplementationStandard | None = Field(
        default=None,
        examples=[
            FormatImplementationStandard.KOBOLD_AI,
        ],
    )
    """The standard for format implementations."""

    leading_space_to_input_when_missing: bool = Field(
        default=False,
        examples=[
            False,
        ],
    )
    """Input formatting option. When enabled, adds a leading space to your input if there is no trailing whitespace at
    the end of the previous action."""

    remove_consecutive_newlines: bool = Field(
        default=False,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, replaces all occurrences of two or more consecutive newlines in the
    output with one newline."""

    remove_special_characters: bool = Field(
        default=False,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes #/@%}{+=~|\\^<> from the output."""

    remove_end_of_sentence: bool = Field(
        default=False,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes some characters from the end of the output such that the output
    doesn't end in the middle of a sentence. If the output is less than one sentence long, does nothing."""

    remove_after_first_line: bool = Field(
        default=False,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes everything after the first line of the output, including the
    newline."""


class BasicTextGenerationFormatParameters(GenerationParameterBaseModel):  # TODO: Better field names
    """Represent common text generation formatting parameters."""

    frmtadsnsp: bool | None = Field(
        default=None,
        examples=[
            False,
        ],
    )
    """Input formatting option. When enabled, adds a leading space to your input if there is no trailing whitespace at
    the end of the previous action."""
    frmtrmblln: bool | None = Field(
        default=None,
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
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes some characters from the end of the output such that the output
    doesn't end in the middle of a sentence. If the output is less than one sentence long, does nothing."""
    singleline: bool | None = Field(
        default=None,
        examples=[
            False,
        ],
    )
    """Output formatting option. When enabled, removes everything after the first line of the output, including the
    newline."""


class BasicTextGenerationParametersTemplate(GenerationWithModelParameters):  # TODO: Non-AI-Horde specific constraints
    """Represents the common parameters for a text generation."""

    prompt: str | None = None
    """The prompt to use for the generation."""

    soft_prompt: str | None = None
    """The soft prompt to use for the generation."""

    max_context_length: int | None = Field(
        default=None,
        ge=80,
        le=32000,
    )
    """Maximum number of tokens to send to the model."""

    max_length: int | None = Field(default=None, ge=16, le=1024)
    """Number of tokens to generate."""

    stop_sequence: list[str] | None = None
    """The stop sequences to use for the generation."""

    temperature: float | None = Field(default=None, ge=0.0, le=5.0)
    """Temperature value."""

    dynamic_temp_exponent: float | None = Field(default=None, ge=0.0, le=5.0)
    """Dynamic temperature exponent value."""
    dynamic_temp_range: float | None = Field(default=None, ge=0.0, le=5.0)
    """Dynamic temperature range value."""

    tfs: float | None = Field(default=None, ge=0.0, le=1.0)
    """Tail free sampling value."""
    typical: float | None = Field(default=None, ge=0.0, le=1.0)
    """Typical sampling value."""
    sampler_order: list[int] | None = None
    """The sampler order to use for the generation."""
    smoothing_factor: float | None = Field(default=None, ge=0.0, le=10.0)
    """Quadratic sampling value."""

    top_a: float | None = Field(default=None, ge=0.0, le=1.0)
    """Top-a sampling value."""
    top_k: int | None = Field(default=None, ge=0, le=100)
    """Top-k sampling value."""
    top_p: float | None = Field(default=None, ge=0.001, le=1.0)
    """Top-p sampling value."""

    min_p: float | None = Field(default=None, ge=0.0, le=1.0)
    """Min-p sampling value."""
    rep_pen: float | None = Field(default=None, ge=1.0, le=3.0)
    """Base repetition penalty value."""
    rep_pen_range: int | None = Field(default=None, ge=0, le=4096)
    """Repetition penalty range."""
    rep_pen_slope: float | None = Field(default=None, ge=0.0, le=10.0)
    """Repetition penalty slope."""


class BasicTextGenerationParameters(BasicTextGenerationParametersTemplate):  # TODO: Non-AI-Horde specific constraints
    """Represents the common bare-minimum parameters for a text generation."""

    model_config = get_default_frozen_model_config_dict()

    model: str
    """The model to use for the generation."""

    prompt: str  # pyright: ignore[reportGeneralTypeIssues, reportIncompatibleVariableOverride]
    """The prompt to use for the generation."""


class TextGenerationParametersTemplate(CompositeParametersBase):
    """Represents the parameters for a text generation."""

    base_params: BasicTextGenerationParametersTemplate | None = None
    """The basic text generation parameters for the generation."""

    format_params: BasicTextGenerationFormatParameters | None = None
    """The text generation formatting parameters."""

    @override
    def get_number_expected_results(self) -> int:
        """Return the number of expected results for this parameter set.

        Returns:
            int: The number of expected results.
        """
        return 1

    def to_parameters(
        self,
        *,
        base_param_updates: BasicTextGenerationParametersTemplate | None = None,
        result_ids: Sequence[ID_TYPES] | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "text",
    ) -> TextGenerationParameters:
        """Convert this template into concrete text generation parameters."""
        base_params = self.base_params
        if base_params is None:
            raise ValueError("Text generation templates must define base_params before conversion.")

        overrides: dict[str, object] | None = None
        if base_param_updates:
            overrides = {
                "base_params": base_params.model_copy(update=base_param_updates.model_dump(exclude_none=True)),
            }

        def _inject_base_params_into_fingerprint(
            finalization: TemplateFinalization[Self],
            fingerprint_payload: dict[str, object],
        ) -> None:
            fingerprint_base_params = finalization.template.base_params
            if fingerprint_base_params is None:
                raise ValueError("Text generation templates must define base_params before conversion.")
            fingerprint_payload["base_params"] = fingerprint_base_params.model_dump(exclude_none=False)

        finalization = finalize_template_for_parameters(
            self,
            overrides=overrides,
            exclude_none=False,
            fingerprint_exclude_fields=("result_ids",),
            fingerprint_transform=_inject_base_params_into_fingerprint,
        )

        finalized_template = finalization.template
        resolved_base_params = finalized_template.base_params
        if resolved_base_params is None:
            raise ValueError("Text generation templates must define base_params before conversion.")

        resolved_result_ids = resolve_result_ids_from_payload(
            explicit_ids=result_ids,
            payload_value=finalization.payload.get("result_ids"),
            count=1,
            allocator=allocator,
            seed=seed,
            fingerprint=finalization.fingerprint,
        )

        concrete_base_params = BasicTextGenerationParameters.model_validate(
            resolved_base_params,
            from_attributes=True,
        )

        parameter_payload = finalized_template.model_copy(
            update={
                "base_params": concrete_base_params,
                "result_ids": resolved_result_ids,
            },
        )

        return TextGenerationParameters.model_validate(
            parameter_payload,
            from_attributes=True,
        )


class TextGenerationParameters(TextGenerationParametersTemplate):
    """Represents the common bare-minium parameters for a text generation."""

    result_ids: list[ID_TYPES]
    """The generation IDs to assign to the resulting discrete generations."""

    base_params: BasicTextGenerationParameters
    """The basic text generation parameters for the generation."""


class KoboldAITextGenerationParameters(TextGenerationParameters):
    """Represents koboldAI text generation parameters."""

    use_default_bad_words_ids: bool | None = None
    """When True, uses the default KoboldAI bad word IDs."""
