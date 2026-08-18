"""The wire shape of the sampler constraints document an AI Horde API publishes.

The facts themselves live in
[`constraints`][horde_sdk.generation_parameters.image.constraints]. A python client can import that
module directly; every other client reads them over HTTP from the API's sampler constraints endpoint.
This module is the type of that response, so both ends describe the same document rather than agreeing
by convention: the API builds one of these and serialises it, and a python client parses the response
back into the same type.

Critical public members:

- The whole served document, and the entry point for parsing a response:
  [`SamplerConstraintsDocument`][horde_sdk.generation_parameters.image.constraints_document.SamplerConstraintsDocument]
- One sampler's knobs, cost, tier and vocabulary as they are served:
  [`PublishedSamplerRecord`][horde_sdk.generation_parameters.image.constraints_document.PublishedSamplerRecord]
- One discoverable worker conformance profile:
  [`PublishedSamplerExecutionContract`][horde_sdk.generation_parameters.image.constraints_document.PublishedSamplerExecutionContract]
- The sections mirroring the API's rejections, which a client honouring them cannot construct against:
  [`PublishedHardConstraints`][horde_sdk.generation_parameters.image.constraints_document.PublishedHardConstraints]

The models here are deliberately separate from the dataclasses in `constraints`. Those describe the
rules; these describe how one API chose to publish them, including keys named after that API's own
request fields. Field names match the served JSON keys exactly, so renaming one is a wire change.
"""

from __future__ import annotations

from typing import Annotated, Literal

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from pydantic import BaseModel, Field

from horde_sdk.consts import get_default_frozen_model_config_dict
from horde_sdk.generation_parameters.image.constraints import (
    CONSTRAINT_PROVENANCE,
    KNOWN_SAMPLER_SOLVER_TYPES,
    SAMPLER_PRESENTATION_TIER,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS
from horde_sdk.generation_parameters.image.sampler_work import (
    SamplerExecutionContractVersion,
    SamplerExecutionGuarantee,
)

__all__ = [
    "AUTHORITATIVE_WORK_FIELD",
    "SAMPLER_CONSTRAINTS_DOCUMENT_SCHEMA_VERSION",
    "PublishedAdaptiveIterationCeiling",
    "PublishedAdaptiveWorkProfile",
    "PublishedAdvisories",
    "PublishedBoundedAdaptiveSamplerExecutionGuarantee",
    "PublishedFixedRateWorkProfile",
    "PublishedHardConstraints",
    "PublishedKnobRange",
    "PublishedPresentationTiers",
    "PublishedRecommendation",
    "PublishedRejectedPairing",
    "PublishedSamplerExecutionContract",
    "PublishedSamplerExecutionGuarantee",
    "PublishedSamplerRecord",
    "PublishedSamplerWorkProfile",
    "PublishedWorkAccounting",
    "SamplerConstraintsDocument",
]

AUTHORITATIVE_WORK_FIELD: Literal["work_profile"] = "work_profile"
"""The sampler-record field carrying operational work-accounting semantics.

Published alongside measured cost ratios so clients cannot mistake one-card timing evidence for the
portable work quantity used by operational policy.
"""

SAMPLER_CONSTRAINTS_DOCUMENT_SCHEMA_VERSION: Literal["1.0"] = "1.0"
"""Identify the initial public JSON shape of the sampler constraints document."""


class PublishedKnobRange(BaseModel):
    """Represents the accepted range of one numeric solver knob, as it is served.

    JSON has no literal for infinity, so an unbounded maximum, and a default meaning "the solver applies
    no limit unless you set one", are both served as null rather than as a number.
    """

    model_config = get_default_frozen_model_config_dict()

    minimum: float
    """Smallest accepted value, inclusive."""

    maximum: float | None
    """Largest accepted value, inclusive. Null where the knob has no upper limit."""

    default: float | None
    """The value the solver uses when the knob is left unset. Null where it applies no limit."""

    integer_only: bool
    """Whether the knob accepts only whole numbers."""


class PublishedFixedRateWorkProfile(BaseModel):
    """A published sampler whose marginal work scales with requested trajectory length."""

    model_config = get_default_frozen_model_config_dict()

    kind: Literal["fixed_rate"] = "fixed_rate"
    """The discriminator for trajectory-derived work."""

    marginal_work_units_per_trajectory_step: int = Field(ge=1)
    """First-order-equivalent marginal work units for one requested trajectory step."""


class PublishedAdaptiveWorkProfile(BaseModel):
    """A published adaptive sampler and the serving API's request-level estimate for it."""

    model_config = get_default_frozen_model_config_dict()

    kind: Literal["adaptive"] = "adaptive"
    """The discriminator for solver-chosen iteration counts."""

    estimated_work_units_per_request: int = Field(ge=0)
    """The serving API's stable accounting estimate, independent of requested trajectory steps."""

    finite_ceiling_contract_versions: list[SamplerExecutionContractVersion]
    """Execution contracts that make this adaptive sampler's maximum work finite."""


PublishedSamplerWorkProfile = Annotated[
    PublishedFixedRateWorkProfile | PublishedAdaptiveWorkProfile,
    Field(discriminator="kind"),
]
"""The discriminated wire representation of fixed and adaptive sampler work."""


class PublishedAdaptiveIterationCeiling(BaseModel):
    """Represents an adaptive solver's exact trajectory-derived iteration ceiling."""

    model_config = get_default_frozen_model_config_dict()

    trajectory_multiplier_numerator: int = Field(ge=1)
    """Numerator of the exact multiplier applied to requested trajectory steps."""

    trajectory_multiplier_denominator: int = Field(ge=1)
    """Denominator of the exact multiplier applied to requested trajectory steps."""

    rounding: Literal["ceiling"] = "ceiling"
    """Require fractional iteration ceilings to round upward."""


class PublishedBoundedAdaptiveSamplerExecutionGuarantee(BaseModel):
    """Represents the atomic finite-iteration guarantee for the adaptive sampler."""

    model_config = get_default_frozen_model_config_dict()

    name: Literal[SamplerExecutionGuarantee.BOUNDED_DPM_ADAPTIVE_V1] = (
        SamplerExecutionGuarantee.BOUNDED_DPM_ADAPTIVE_V1
    )
    """Stable SDK identifier for the atomic execution behavior."""

    sampler: KNOWN_IMAGE_SAMPLERS
    """Sampler whose runtime behavior this guarantee constrains."""

    maximum_solver_iterations: PublishedAdaptiveIterationCeiling
    """Exact formula for the maximum solver iterations the backend permits."""

    work_units_per_solver_iteration_source: Literal["sampler_order"] = "sampler_order"
    """Request setting that determines work units consumed by each solver iteration."""


PublishedSamplerExecutionGuarantee = Annotated[
    PublishedBoundedAdaptiveSamplerExecutionGuarantee,
    Field(discriminator="name"),
]
"""The discriminated wire representation of atomic sampler execution guarantees."""


class PublishedSamplerExecutionContract(BaseModel):
    """Represents a cumulative execution behavior profile a worker can claim to implement."""

    model_config = get_default_frozen_model_config_dict()

    version: SamplerExecutionContractVersion
    """Stable version workers advertise during check-in."""

    guarantees: list[PublishedSamplerExecutionGuarantee]
    """Atomic behavior guarantees contained by this cumulative contract version."""


class PublishedSamplerRecord(BaseModel):
    """Represents one sampler's knobs, cost, tier and vocabulary as they are served."""

    model_config = get_default_frozen_model_config_dict()

    name: KNOWN_IMAGE_SAMPLERS
    """The sampler this record describes, repeated here so an entry stands alone once read out of the map."""

    work_profile: PublishedSamplerWorkProfile
    """How operational work relates—or does not relate—to requested trajectory steps."""

    measured_cost_ratio_sd15: float | None
    """Per-step wall-clock cost relative to `k_euler` on a stable_diffusion_1 model, or null where a ratio
    is meaningless because the sampler chooses its own step count."""

    measured_cost_ratio_sdxl: float | None
    """The same ratio on a stable_diffusion_xl model, or null for the same reason."""

    presentation_tier: SAMPLER_PRESENTATION_TIER
    """How prominently the sampler is worth offering. A presentation hint that restricts nothing."""

    solver_type_choices: list[KNOWN_SAMPLER_SOLVER_TYPES]
    """The `solver_type` values this sampler accepts, empty when it takes none."""

    accepted_settings: dict[str, PublishedKnobRange]
    """The numeric knobs this sampler accepts, keyed by the request field name a client sends them under.

    The keys are the serving API's own request field names rather than the knob names the backend's
    solvers use, because a client reads this to build a request.
    """

    applies_cfg_pp: bool
    """Whether the sampler applies the CFG++ correction, which expects a much lower `cfg_scale`."""


class PublishedRejectedPairing(BaseModel):
    """Represents one sampler and scheduler pairing the API refuses outright."""

    model_config = get_default_frozen_model_config_dict()

    sampler: KNOWN_IMAGE_SAMPLERS
    """The sampler half of the refused pairing."""

    scheduler: KNOWN_IMAGE_SCHEDULERS
    """The scheduler half of the refused pairing."""


class PublishedHardConstraints(BaseModel):
    """Represents the sections that mirror the API's rejections exactly.

    A request honouring everything here cannot be one the API refuses on constraint grounds, which is
    what separates these from the advisory sections.
    """

    model_config = get_default_frozen_model_config_dict()

    rejected_sampler_scheduler_pairings: list[PublishedRejectedPairing]
    """Pairings that produce no usable image and are refused rather than substituted."""

    scheduler_baseline_applicability: dict[KNOWN_IMAGE_SCHEDULERS, list[KNOWN_IMAGE_GENERATION_BASELINE]]
    """Baselines each restricted scheduler is defined for. A scheduler absent here works on every baseline."""


class PublishedRecommendation(BaseModel):
    """Represents one advisory statement, with the provenance that qualifies it.

    Recommendations never block a request. The provenance is served because these range from statements
    by the image backend's own author to third-party folklore, and a client cannot weigh them otherwise.
    """

    model_config = get_default_frozen_model_config_dict()

    samplers: list[KNOWN_IMAGE_SAMPLERS]
    """The samplers the statement applies to, empty when it applies to all of them."""

    schedulers: list[KNOWN_IMAGE_SCHEDULERS]
    """The schedulers the statement recommends, empty when it recommends none."""

    provenance: CONSTRAINT_PROVENANCE
    """Whose statement this is."""

    source: str
    """A human-readable citation."""

    summary: str
    """The statement itself."""


class PublishedAdvisories(BaseModel):
    """Represents the quality expectations the API warns about rather than enforcing."""

    model_config = get_default_frozen_model_config_dict()

    cfg_pp_advised_max_cfg_scale: float
    """Above this `cfg_scale`, the CFG++ solvers oversaturate. The image still renders."""


class PublishedWorkAccounting(BaseModel):
    """Explains operational work figures without claiming they are the learned Kudos price.

    Served as bare numbers, measured ratios would read like portable costs. They are one card's evidence
    about marginal work. The API's learned Kudos model remains a separate sampler-plus-step calculation.
    """

    model_config = get_default_frozen_model_config_dict()

    authoritative_field: Literal["work_profile"] = AUTHORITATIVE_WORK_FIELD
    """Names the sampler-record field operational accounting and time budgeting consume."""

    authoritative_note: str
    """What that field counts, and where it is read from."""

    measured_cost_ratio_provenance: CONSTRAINT_PROVENANCE
    """The provenance both measured ratio columns carry."""

    measured_cost_ratio_source: str
    """Filename of the measurement artifact both ratio columns were read from."""

    measured_cost_ratio_note: str
    """How the ratios were derived, and why they corroborate the authoritative field rather than replace it."""

    measured_cost_ratio_sdxl_note: str
    """The model and resolution the stable_diffusion_xl column was taken on, and how to read it."""

    measured_cost_ratio_sd15_note: str
    """The model and resolution the stable_diffusion_1 column was taken on, and the bias it carries."""


class PublishedPresentationTiers(BaseModel):
    """Represents the default-offer set, and the note saying the split restricts nothing."""

    model_config = get_default_frozen_model_config_dict()

    note: str
    """States that every sampler is accepted, priced and dispatched identically whatever its tier."""

    recommended: list[KNOWN_IMAGE_SAMPLERS]
    """The samplers worth offering by default. Everything absent is advanced, not deprecated."""


class SamplerConstraintsDocument(BaseModel):
    """Represents the whole sampler constraints document an API serves.

    Only samplers and schedulers the serving API accepts appear, so a client reading this never offers a
    name that API's request models would reject as unknown.

    Examples:
        Parsing a response from the sampler constraints endpoint:

        ```python
        document = SamplerConstraintsDocument.model_validate(response.json())
        euler = document.samplers[KNOWN_IMAGE_SAMPLERS.k_euler]
        ```

    """

    model_config = get_default_frozen_model_config_dict()

    schema_version: Literal["1.0"] = SAMPLER_CONSTRAINTS_DOCUMENT_SCHEMA_VERSION
    """Version of this document's JSON shape, independent of execution conformance versions."""

    execution_contracts: dict[SamplerExecutionContractVersion, PublishedSamplerExecutionContract]
    """Discoverable execution profiles workers can claim to implement."""

    samplers: dict[KNOWN_IMAGE_SAMPLERS, PublishedSamplerRecord]
    """Every sampler the serving API accepts, keyed by name."""

    hard_constraints: PublishedHardConstraints
    """The sections that mirror the API's rejections. Honouring these avoids a refusal."""

    recommendations: list[PublishedRecommendation]
    """Advisory pairings and settings, each carrying the provenance of the claim."""

    advisories: PublishedAdvisories
    """Quality expectations the API warns about rather than enforcing."""

    work_accounting: PublishedWorkAccounting
    """What work units, estimates, ceilings, and measured ratios mean."""

    presentation_tiers: PublishedPresentationTiers
    """Which samplers are worth offering by default, and the note saying the split restricts nothing."""
