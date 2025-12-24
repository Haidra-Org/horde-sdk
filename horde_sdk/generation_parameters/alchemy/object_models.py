from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal, override

from pydantic import Field

from horde_sdk.consts import ID_TYPES, KNOWN_NSFW_DETECTOR
from horde_sdk.generation_parameters.alchemy.consts import (
    ALCHEMY_PARAMETER_FIELDS,
    KNOWN_ALCHEMY_FORMS,
    KNOWN_ALCHEMY_TYPES,
    KNOWN_CAPTION_MODELS,
    KNOWN_FACEFIXERS,
    KNOWN_INTERROGATORS,
    KNOWN_UPSCALERS,
)
from horde_sdk.generation_parameters.generic import CompositeParametersBase
from horde_sdk.generation_parameters.generic.object_models import GenerationFeatureFlags
from horde_sdk.generation_parameters.utils import (
    ResultIdAllocator,
    finalize_template_for_parameters,
    resolve_result_id_from_payload,
)


class AlchemyFeatureFlags(GenerationFeatureFlags):
    """Feature flags for an alchemy worker."""

    alchemy_types: list[KNOWN_ALCHEMY_TYPES] = Field(default_factory=list)
    """The alchemy types supported by the worker."""


class SingleAlchemyParametersTemplate(CompositeParametersBase):
    """Template for alchemy parameters with all fields optional.

    Use this class during chain construction when not all parameters are known yet.
    Convert to SingleAlchemyParameters (or subclasses) before execution.
    """

    result_id: str | None = None
    """The generation ID to use for the generation."""

    form: KNOWN_ALCHEMY_FORMS | str | None = None
    """The form to use for the generation."""

    source_image: bytes | str | None = None
    """The source image to use for the generation."""

    @override
    def get_number_expected_results(self) -> int:
        """Get the number of expected results."""
        return 1

    def to_parameters(
        self,
        *,
        result_id: ID_TYPES | None = None,
        source_image: bytes | str | None = None,
        default_form: KNOWN_ALCHEMY_FORMS | str | None = None,
        allocator: ResultIdAllocator | None = None,
        seed: str = "alchemy",
    ) -> SingleAlchemyParameters:
        """Convert this template into concrete alchemy generation parameters."""
        overrides: dict[str, object] = {}
        if source_image is not None:
            overrides[ALCHEMY_PARAMETER_FIELDS.source_image] = source_image

        current_form = self.form
        if default_form is not None and current_form is None:
            overrides[ALCHEMY_PARAMETER_FIELDS.form] = default_form

        finalization = finalize_template_for_parameters(
            self,
            overrides=overrides,
            exclude_none=False,
            fingerprint_exclude_fields=(ALCHEMY_PARAMETER_FIELDS.result_id,),
        )

        resolved_result_id = resolve_result_id_from_payload(
            explicit_id=result_id,
            payload_value=finalization.payload.get(ALCHEMY_PARAMETER_FIELDS.result_id),
            allocator=allocator,
            seed=seed,
            fingerprint=finalization.fingerprint,
        )

        finalized_template = finalization.template.model_copy(
            update={ALCHEMY_PARAMETER_FIELDS.result_id: resolved_result_id},
        )

        return self._instantiate_alchemy_parameters(finalized_template)

    @staticmethod
    def _instantiate_alchemy_parameters(
        payload: SingleAlchemyParametersTemplate | Mapping[str, object],
    ) -> SingleAlchemyParameters:
        """Instantiate the appropriate alchemy parameter model based on payload contents."""
        return instantiate_alchemy_parameters(payload)


class SingleAlchemyParameters(CompositeParametersBase):
    """Represents the common bare minimum parameters for any alchemy generation."""

    result_id: str
    """The generation ID to use for the generation."""

    form: KNOWN_ALCHEMY_FORMS | str
    """The form to use for the generation."""

    source_image: bytes | str | None
    """The source image to use for the generation."""

    @override
    def get_number_expected_results(self) -> int:
        """Get the number of expected results."""
        return 1


class UpscaleAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    """Template for upscale alchemy parameters with all fields optional."""

    upscaler: KNOWN_UPSCALERS | str | None = None


class UpscaleAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for an upscale alchemy generation."""

    form: Literal[KNOWN_ALCHEMY_FORMS.post_process] = KNOWN_ALCHEMY_FORMS.post_process

    upscaler: KNOWN_UPSCALERS | str


class FacefixAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    """Template for facefix alchemy parameters with all fields optional."""

    facefixer: KNOWN_FACEFIXERS | str | None = None


class FacefixAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a facefix alchemy generation."""

    facefixer: KNOWN_FACEFIXERS | str


class InterrogateAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    """Template for interrogate alchemy parameters with all fields optional."""

    interrogator: KNOWN_INTERROGATORS | str | None = None


class InterrogateAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for an interrogation alchemy generation."""

    interrogator: KNOWN_INTERROGATORS | str


class CaptionAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    """Template for caption alchemy parameters with all fields optional."""

    caption_model: KNOWN_CAPTION_MODELS | str | None = None


class CaptionAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a caption alchemy generation."""

    caption_model: KNOWN_CAPTION_MODELS | str


class NSFWAlchemyParametersTemplate(SingleAlchemyParametersTemplate):
    """Template for NSFW alchemy parameters with all fields optional."""

    nsfw_detector: KNOWN_NSFW_DETECTOR | str | None = None


class NSFWAlchemyParameters(SingleAlchemyParameters):
    """Represents the parameters for a NSFW alchemy generation."""

    nsfw_detector: KNOWN_NSFW_DETECTOR | str


class AlchemyParameters(CompositeParametersBase):
    """Represents the parameters for an alchemy generation."""

    upscalers: list[UpscaleAlchemyParameters] | None = None
    """The upscale operations requested."""
    facefixers: list[FacefixAlchemyParameters] | None = None
    """The facefix operations requested."""
    interrogators: list[InterrogateAlchemyParameters] | None = None
    """The interrogation operations requested."""
    captions: list[CaptionAlchemyParameters] | None = None
    """The caption operations requested."""
    nsfw_detectors: list[NSFWAlchemyParameters] | None = None
    """The NSFW detection operations requested."""

    misc_post_processors: list[SingleAlchemyParameters] | None = None
    """Any other post-processing operations requested."""

    _all_alchemy_operations: list[SingleAlchemyParameters] | None = None
    """The list of all alchemy operations requested."""

    @property
    def all_alchemy_operations(self) -> list[SingleAlchemyParameters]:
        """Get all operations."""
        if self._all_alchemy_operations is not None:
            return self._all_alchemy_operations.copy()

        all_operations: list[SingleAlchemyParameters] = []
        if self.upscalers:
            all_operations.extend(self.upscalers)
        if self.facefixers:
            all_operations.extend(self.facefixers)
        if self.interrogators:
            all_operations.extend(self.interrogators)
        if self.captions:
            all_operations.extend(self.captions)
        if self.nsfw_detectors:
            all_operations.extend(self.nsfw_detectors)
        if self.misc_post_processors:
            all_operations.extend(self.misc_post_processors)

        self._all_alchemy_operations = all_operations

        return all_operations.copy()

    @override
    def get_number_expected_results(self) -> int:
        """Get the number of expected results."""
        return len(self.all_alchemy_operations)


Predicate = Callable[[Mapping[str, object]], bool]


@dataclass(frozen=True)
class ResolverRule:
    """Ordered rule binding a predicate to the concrete parameter model it selects."""

    predicate: Predicate
    model: type[SingleAlchemyParameters]


_ALCHEMY_PARAMETER_RULES: list[ResolverRule] = []


def register_alchemy_parameter_rule(rule: ResolverRule, *, append: bool = True) -> None:
    """Register a resolver rule that may select a concrete alchemy parameter model."""
    if append:
        _ALCHEMY_PARAMETER_RULES.append(rule)
    else:
        _ALCHEMY_PARAMETER_RULES.insert(0, rule)


def unregister_alchemy_parameter_rule(rule: ResolverRule) -> None:
    """Remove a previously registered resolver rule."""
    _ALCHEMY_PARAMETER_RULES.remove(rule)


def resolve_alchemy_parameter_model(
    payload: Mapping[str, object] | SingleAlchemyParametersTemplate,
) -> type[SingleAlchemyParameters]:
    """Resolve the concrete alchemy parameter model for the supplied payload."""
    payload_mapping: Mapping[str, object]
    if isinstance(payload, CompositeParametersBase):
        payload_mapping = payload.model_dump(exclude_none=False)
    else:
        payload_mapping = payload
    for rule in _ALCHEMY_PARAMETER_RULES:
        if rule.predicate(payload_mapping):
            return rule.model
    return SingleAlchemyParameters


def instantiate_alchemy_parameters(
    payload: Mapping[str, object] | SingleAlchemyParametersTemplate,
) -> SingleAlchemyParameters:
    """Instantiate the resolved alchemy parameter model with the given payload."""
    model = resolve_alchemy_parameter_model(payload)
    if isinstance(payload, CompositeParametersBase):
        return model.model_validate(payload, from_attributes=True)
    return model(**dict(payload))


def _register_default_rules() -> None:
    def _has_field(field_name: ALCHEMY_PARAMETER_FIELDS) -> Predicate:
        return lambda payload: payload.get(field_name) is not None

    def _is_post_process_without_upscaler(payload: Mapping[str, object]) -> bool:
        form_value = payload.get(ALCHEMY_PARAMETER_FIELDS.form)
        if form_value is None:
            return False
        if str(form_value) != str(KNOWN_ALCHEMY_FORMS.post_process):
            return False
        return ALCHEMY_PARAMETER_FIELDS.upscaler not in payload

    default_rules = [
        ResolverRule(predicate=_has_field(ALCHEMY_PARAMETER_FIELDS.upscaler), model=UpscaleAlchemyParameters),
        ResolverRule(predicate=_has_field(ALCHEMY_PARAMETER_FIELDS.facefixer), model=FacefixAlchemyParameters),
        ResolverRule(predicate=_has_field(ALCHEMY_PARAMETER_FIELDS.interrogator), model=InterrogateAlchemyParameters),
        ResolverRule(predicate=_has_field(ALCHEMY_PARAMETER_FIELDS.caption_model), model=CaptionAlchemyParameters),
        ResolverRule(predicate=_has_field(ALCHEMY_PARAMETER_FIELDS.nsfw_detector), model=NSFWAlchemyParameters),
        ResolverRule(predicate=_is_post_process_without_upscaler, model=UpscaleAlchemyParameters),
    ]

    _ALCHEMY_PARAMETER_RULES.extend(default_rules)


_register_default_rules()
