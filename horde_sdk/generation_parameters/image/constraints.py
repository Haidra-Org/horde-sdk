"""Per-sampler capability and constraint data shared by clients, the API and workers.

The image backend accepts a different set of solver knobs for every sampler, and rejects the rest with
a type error raised from inside the render graph. This module states, once, which knobs each sampler
takes, over what range, what a step of it costs, and which sampler/scheduler/baseline combinations are
known to produce no usable image. Requests can then be checked before anything is dispatched.

Critical public members:

- [`SAMPLER_CONSTRAINTS`][horde_sdk.generation_parameters.image.constraints.SAMPLER_CONSTRAINTS]: one
  [`SamplerConstraints`][horde_sdk.generation_parameters.image.constraints.SamplerConstraints] record
  for every member of
  [`KNOWN_IMAGE_SAMPLERS`][horde_sdk.generation_parameters.image.consts.KNOWN_IMAGE_SAMPLERS].
- [`list_constraint_violations`][horde_sdk.generation_parameters.image.constraints.list_constraint_violations]:
  the hard check, returning every reason a request cannot be served as asked.
- [`evaluations_per_step`][horde_sdk.generation_parameters.image.constraints.evaluations_per_step]: the
  number of model evaluations a sampler performs per step, which is what a step actually costs.
- [`SAMPLER_RECOMMENDATIONS`][horde_sdk.generation_parameters.image.constraints.SAMPLER_RECOMMENDATIONS]:
  advisory pairings, each carrying the provenance of the claim.

Every fact here is separated into two kinds. Hard constraints and knob applicability are read out of
the backend's own source: a knob is applicable when the solver function accepts a keyword of that name,
and a numeric range is the one the backend's own node for that sampler declares. Recommendations are
opinions, and each carries a
[`CONSTRAINT_PROVENANCE`][horde_sdk.generation_parameters.image.constraints.CONSTRAINT_PROVENANCE]
saying whose opinion it is.

This module imports only from
[`consts`][horde_sdk.generation_parameters.image.consts] and the model reference, so the wire models
and the worker feature flags can both depend on it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import auto
from types import MappingProxyType

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE
from strenum import StrEnum

from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS


class CONSTRAINT_PROVENANCE(StrEnum):
    """Where a statement about a sampler came from, and therefore how much weight it carries."""

    upstream_author = auto()
    """Stated by the image backend's own author. The strongest non-code source."""

    community = auto()
    """Third-party folklore. Widely repeated, not endorsed by the backend's authors, unverified here."""

    measured = auto()
    """Timed on real hardware through the production render pipeline, and reproducible from its artifact.

    A measurement describes the card, resolution and pipeline it was taken on. It is evidence about
    cost, not a rule about it.
    """

    user_ruled = auto()
    """Settled by a deliberate ruling after review, and authoritative for this project."""


class SAMPLER_SOLVER_KNOB(StrEnum):
    """The solver knobs a request may set, named as the backend's solver functions name them."""

    eta = auto()
    """Stochastic strength. At zero an SDE solver collapses onto its deterministic twin."""

    s_noise = auto()
    """Multiplier on the noise added per step."""

    s_churn = auto()
    """Total extra noise injected across the run, spread over the steps within the churn window."""

    s_tmin = auto()
    """Lower sigma bound of the churn window."""

    s_tmax = auto()
    """Upper sigma bound of the churn window."""

    solver_type = auto()
    """Which second-order correction the solver applies. The vocabulary differs per sampler."""

    order = auto()
    """Solver order: how many evaluations the step is built from, or may reuse.

    The solvers spell it differently. The single-step solvers declare `order`; the multistep ones declare
    `max_order`, which is the same concept under another name, and each record carries the spelling its
    solver uses. The sa_solver family is excluded rather than renamed: it splits the concept into a
    predictor order and a corrector order, which one number cannot express.
    """


class SAMPLER_PRESENTATION_TIER(StrEnum):
    """How prominently a sampler is worth offering, now that the vocabulary is long enough to overwhelm.

    This is a presentation concern and nothing else: every sampler here is accepted, priced and
    dispatched identically whatever its tier. A client may default to showing only the recommended tier
    and put the rest behind an "advanced" affordance, which is what the split is for.
    """

    recommended = auto()
    """Worth offering by default: together these span the meaningful choices a requester has."""

    advanced = auto()
    """Legitimate, but largely an equivalent variant of something in the recommended tier.

    Nothing here is deprecated or discouraged. These are for a requester who already knows which one
    they want, and listing them all by default costs more in choice than it returns in capability.
    """


class KNOWN_SAMPLER_SOLVER_TYPES(StrEnum):
    """Every `solver_type` value any sampler accepts.

    No sampler accepts all of them. The `midpoint`/`heun` pair and the `phi_1`/`phi_2` pair belong to
    different solver families; see
    [`SamplerConstraints.solver_type_choices`][horde_sdk.generation_parameters.image.constraints.SamplerConstraints.solver_type_choices].
    """

    midpoint = auto()
    heun = auto()
    phi_1 = auto()
    phi_2 = auto()


class CONSTRAINT_VIOLATION_KIND(StrEnum):
    """Why a request cannot be served as asked."""

    knob_inapplicable = auto()
    """The sampler's solver function takes no keyword of that name, so setting it would do nothing."""

    knob_out_of_range = auto()
    """The value falls outside the range the backend declares for that sampler and knob."""

    solver_type_unsupported = auto()
    """The sampler accepts a `solver_type`, but not this one."""

    sampler_scheduler_rejected = auto()
    """The pairing is known to produce no usable image at any step count."""

    scheduler_baseline_unsupported = auto()
    """The scheduler has no definition for this baseline, so it cannot generate sigmas for it."""


@dataclass(frozen=True)
class NumericKnobRange:
    """Represents the accepted range of one numeric solver knob for one sampler.

    Attributes:
        minimum: Smallest accepted value, inclusive.
        maximum: Largest accepted value, inclusive. May be infinite.
        default: The value the backend uses when the knob is left unset.
        integral: Whether the knob only accepts whole numbers.
        backend_keyword: The keyword the solver function itself declares, when it differs from the knob's
            own name. `None` means the two agree. This exists because the same concept is spelled
            differently between solvers: the multistep solvers call their order `max_order`, and a
            request that named only `order` would be silently dropped by the backend's own filter.

    """

    minimum: float
    maximum: float
    default: float
    integral: bool = False
    backend_keyword: str | None = None

    def contains(self, value: float) -> bool:
        """Return whether the value is one this knob accepts."""
        if self.integral and value != int(value):
            return False

        return self.minimum <= value <= self.maximum


@dataclass(frozen=True)
class SamplerConstraints:
    """Represents everything known about one sampler's knobs, cost and identity.

    Attributes:
        sampler: The sampler these constraints describe.
        backend_solver_function: The backend function the sampler resolves to, for traceability.
        numeric_knob_ranges: The numeric knobs the sampler accepts, and their ranges. A knob absent
            from this mapping is one the sampler's solver function does not take.
        solver_type_choices: The `solver_type` values the sampler accepts, empty when it takes none.
        evaluations_per_step: How many model evaluations one step performs. This, rather than the step
            count alone, is what a run costs.
        measured_cost_ratio_sd15: Measured per-step wall-clock cost relative to `k_euler` on a
            stable_diffusion_1 model at 512x512, or `None` where a ratio is meaningless. Carries a small
            positive bias on the one-evaluation samplers, because per-step host work is a visible
            fraction of a 512x512 step.
        measured_cost_ratio_sdxl: The same ratio on a stable_diffusion_xl model at 1024x1024. The larger
            step swamps the per-step host work, so this is the figure that reflects what the sampler
            itself costs. See
            [`MEASURED_COST_RATIO_PROVENANCE`][horde_sdk.generation_parameters.image.constraints.MEASURED_COST_RATIO_PROVENANCE].

    """

    sampler: KNOWN_IMAGE_SAMPLERS
    backend_solver_function: str
    numeric_knob_ranges: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange]
    solver_type_choices: tuple[KNOWN_SAMPLER_SOLVER_TYPES, ...]
    evaluations_per_step: int
    measured_cost_ratio_sd15: float | None
    measured_cost_ratio_sdxl: float | None

    def accepts_knob(self, knob: SAMPLER_SOLVER_KNOB) -> bool:
        """Return whether the sampler's solver function takes this knob."""
        if knob is SAMPLER_SOLVER_KNOB.solver_type:
            return bool(self.solver_type_choices)

        return knob in self.numeric_knob_ranges


@dataclass(frozen=True)
class ConstraintViolation:
    """Represents one reason a request cannot be served as asked.

    Attributes:
        kind: Which rule the request breaks.
        detail: A sentence naming the offending value and what would be accepted instead.

    """

    kind: CONSTRAINT_VIOLATION_KIND
    detail: str


@dataclass(frozen=True)
class SamplerRecommendation:
    """Represents one advisory statement about how a sampler is best used.

    Recommendations never block a request. They exist so clients can offer a sensible default and can
    say where the suggestion came from.

    Attributes:
        samplers: The samplers the statement applies to, empty when it applies to all of them.
        schedulers: The schedulers the statement recommends, empty when it recommends none.
        provenance: Whose statement this is.
        source: A human-readable citation.
        summary: The statement itself.

    """

    samplers: tuple[KNOWN_IMAGE_SAMPLERS, ...]
    schedulers: tuple[KNOWN_IMAGE_SCHEDULERS, ...]
    provenance: CONSTRAINT_PROVENANCE
    source: str
    summary: str


MEASURED_COST_RATIO_PROVENANCE = CONSTRAINT_PROVENANCE.measured
"""The provenance both measured cost ratios carry.

The figures come from
[`MEASURED_COST_RATIO_SOURCE`][horde_sdk.generation_parameters.image.constraints.MEASURED_COST_RATIO_SOURCE]:
renders taken through the production image pipeline on one card, at step counts 10, 20, 30 and 40, three
repeats each, warmups discarded, with the seed, prompt and cfg scale held fixed. Each ratio is the slope
of an ordinary least-squares fit of median wall time against step count, divided by `k_euler`'s slope on
the same model. Fitting the slope is what separates per-step cost from the fixed per-render overhead,
which is around 0.29s at 512x512 and 1.40s at 1024x1024.

The measurement corroborates
[`evaluations_per_step`][horde_sdk.generation_parameters.image.constraints.evaluations_per_step]: at
1024x1024 every sampler lands within a fifth of its evaluation family. Pricing and time budgeting still
read `evaluations_per_step`, which is counted out of the backend's own solver implementations and holds
on any hardware; these ratios are one card's evidence that the count is right.
"""

MEASURED_COST_RATIO_SOURCE = "sampler-cost-2026-08-03T23-02-56.165788Z.json"
"""Filename of the measurement artifact both ratio columns were read from.

Published alongside the other parameter-sweep measurements, and carrying every timing sample, fit
coefficient and setting behind the two rounded numbers held here.
"""


# The backend declares no node-level bounds for eta beyond 0 to 100, and defaults it to 1 everywhere it
# is exposed. `dpm_adaptive` is the one sampler whose solver function defaults it to 0 instead.
_ETA_RANGE = NumericKnobRange(minimum=0.0, maximum=100.0, default=1.0)
_ETA_RANGE_OFF_BY_DEFAULT = NumericKnobRange(minimum=0.0, maximum=100.0, default=0.0)
# The CFG++ ancestral node is the only one that caps eta at 1 and s_noise at 10.
_ETA_RANGE_UNIT = NumericKnobRange(minimum=0.0, maximum=1.0, default=1.0)
_S_NOISE_RANGE_NARROW = NumericKnobRange(minimum=0.0, maximum=10.0, default=1.0)

_S_NOISE_RANGE = NumericKnobRange(minimum=0.0, maximum=100.0, default=1.0)

# No backend node exposes the churn window, so no upstream bound exists for these three. The maxima
# below follow the bound the backend uses for every other float knob, and the defaults are the ones the
# solver functions declare.
_S_CHURN_RANGE = NumericKnobRange(minimum=0.0, maximum=100.0, default=0.0)
_S_TMIN_RANGE = NumericKnobRange(minimum=0.0, maximum=100.0, default=0.0)
_S_TMAX_RANGE = NumericKnobRange(minimum=0.0, maximum=math.inf, default=math.inf)

_LMS_ORDER_RANGE = NumericKnobRange(minimum=1.0, maximum=100.0, default=4.0, integral=True)
_DPM_ADAPTIVE_ORDER_RANGE = NumericKnobRange(minimum=2.0, maximum=3.0, default=3.0, integral=True)

# The multistep solvers spell their order `max_order`, and it is the same concept: how many past
# evaluations the step may reuse. No node declares bounds for it, so these come from the solvers
# themselves. The ceiling is 4, which is both the highest order any of them implements and the documented
# limit of the DEIS coefficient table. The floor is 2 rather than 1: at 1 all three index their history
# buffer before anything is in it, which raises from inside the sampling loop.
_DEIS_MAX_ORDER_RANGE = NumericKnobRange(
    minimum=2.0,
    maximum=4.0,
    default=3.0,
    integral=True,
    backend_keyword="max_order",
)
_IPNDM_MAX_ORDER_RANGE = NumericKnobRange(
    minimum=2.0,
    maximum=4.0,
    default=4.0,
    integral=True,
    backend_keyword="max_order",
)

_NO_NUMERIC_KNOBS: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange] = MappingProxyType({})
_ANCESTRAL_KNOBS: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange] = MappingProxyType(
    {
        SAMPLER_SOLVER_KNOB.eta: _ETA_RANGE,
        SAMPLER_SOLVER_KNOB.s_noise: _S_NOISE_RANGE,
    },
)
_CHURN_KNOBS: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange] = MappingProxyType(
    {
        SAMPLER_SOLVER_KNOB.s_churn: _S_CHURN_RANGE,
        SAMPLER_SOLVER_KNOB.s_tmin: _S_TMIN_RANGE,
        SAMPLER_SOLVER_KNOB.s_tmax: _S_TMAX_RANGE,
        SAMPLER_SOLVER_KNOB.s_noise: _S_NOISE_RANGE,
    },
)
_S_NOISE_ONLY: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange] = MappingProxyType(
    {SAMPLER_SOLVER_KNOB.s_noise: _S_NOISE_RANGE},
)

_MIDPOINT_OR_HEUN = (KNOWN_SAMPLER_SOLVER_TYPES.midpoint, KNOWN_SAMPLER_SOLVER_TYPES.heun)
_PHI_1_OR_PHI_2 = (KNOWN_SAMPLER_SOLVER_TYPES.phi_1, KNOWN_SAMPLER_SOLVER_TYPES.phi_2)
_NO_SOLVER_TYPES: tuple[KNOWN_SAMPLER_SOLVER_TYPES, ...] = ()


def _constraints(
    *,
    sampler: KNOWN_IMAGE_SAMPLERS,
    backend_solver_function: str,
    numeric_knob_ranges: Mapping[SAMPLER_SOLVER_KNOB, NumericKnobRange] = _NO_NUMERIC_KNOBS,
    solver_type_choices: tuple[KNOWN_SAMPLER_SOLVER_TYPES, ...] = _NO_SOLVER_TYPES,
    evaluations_per_step: int,
    measured_cost_ratio_sd15: float | None = None,
    measured_cost_ratio_sdxl: float | None = None,
) -> tuple[KNOWN_IMAGE_SAMPLERS, SamplerConstraints]:
    """Create one table entry, keyed by its sampler."""
    return sampler, SamplerConstraints(
        sampler=sampler,
        backend_solver_function=backend_solver_function,
        numeric_knob_ranges=numeric_knob_ranges,
        solver_type_choices=solver_type_choices,
        evaluations_per_step=evaluations_per_step,
        measured_cost_ratio_sd15=measured_cost_ratio_sd15,
        measured_cost_ratio_sdxl=measured_cost_ratio_sdxl,
    )


SAMPLER_CONSTRAINTS: Mapping[KNOWN_IMAGE_SAMPLERS, SamplerConstraints] = MappingProxyType(
    dict(
        (
            # Knob applicability is the set of keywords each solver function declares, and nothing more.
            # `dpm_fast` is the notable case: the backend wraps it in a closure that forwards no extra
            # options at all, so it takes none of these knobs however its own signature reads.
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_lms,
                backend_solver_function="sample_lms",
                numeric_knob_ranges=MappingProxyType({SAMPLER_SOLVER_KNOB.order: _LMS_ORDER_RANGE}),
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.02,
                measured_cost_ratio_sdxl=1.00,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_heun,
                backend_solver_function="sample_heun",
                numeric_knob_ranges=_CHURN_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.03,
                measured_cost_ratio_sdxl=1.87,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_euler,
                backend_solver_function="sample_euler",
                numeric_knob_ranges=_CHURN_KNOBS,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.00,
                measured_cost_ratio_sdxl=1.00,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_euler_a,
                backend_solver_function="sample_euler_ancestral",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.08,
                measured_cost_ratio_sdxl=1.01,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_2,
                backend_solver_function="sample_dpm_2",
                numeric_knob_ranges=_CHURN_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.17,
                measured_cost_ratio_sdxl=1.94,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_2_a,
                backend_solver_function="sample_dpm_2_ancestral",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.22,
                measured_cost_ratio_sdxl=1.97,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_fast,
                backend_solver_function="sample_dpm_fast",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.16,
                measured_cost_ratio_sdxl=0.97,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
                backend_solver_function="sample_dpm_adaptive",
                numeric_knob_ranges=MappingProxyType(
                    {
                        SAMPLER_SOLVER_KNOB.eta: _ETA_RANGE_OFF_BY_DEFAULT,
                        SAMPLER_SOLVER_KNOB.s_noise: _S_NOISE_RANGE,
                        SAMPLER_SOLVER_KNOB.order: _DPM_ADAPTIVE_ORDER_RANGE,
                    },
                ),
                # This solver chooses its own step size, so its true evaluation count is adaptive and is
                # not a function of the requested step count at all. The 1 below is the pricing
                # convention for it rather than a count read out of the solver.
                evaluations_per_step=1,
                # Both ratios are left unset for the same reason. Wall time per requested step is not a
                # quantity this solver has: the measurement fits it at an r-squared near 0.6 on both
                # baselines, against better than 0.97 for every other sampler, and attributes ten
                # seconds of a 1024x1024 render to fixed overhead because the step count it was asked
                # for barely moves what it does.
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpmpp_2s_a,
                backend_solver_function="sample_dpmpp_2s_ancestral",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.35,
                measured_cost_ratio_sdxl=2.01,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m,
                backend_solver_function="sample_dpmpp_2m",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.08,
                measured_cost_ratio_sdxl=0.98,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmsolver,
                backend_solver_function="sample_dpmpp_2m",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.12,
                measured_cost_ratio_sdxl=1.00,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde,
                backend_solver_function="sample_dpmpp_sde",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.58,
                measured_cost_ratio_sdxl=2.22,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.lcm,
                backend_solver_function="sample_lcm",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.21,
                measured_cost_ratio_sdxl=0.96,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.DDIM,
                backend_solver_function="sample_euler",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.13,
                measured_cost_ratio_sdxl=0.96,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.uni_pc,
                backend_solver_function="sample_unipc",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.34,
                measured_cost_ratio_sdxl=0.98,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.uni_pc_bh2,
                backend_solver_function="sample_unipc_bh2",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.17,
                measured_cost_ratio_sdxl=0.99,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
                backend_solver_function="sample_dpmpp_2m_sde",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                solver_type_choices=_MIDPOINT_OR_HEUN,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.33,
                measured_cost_ratio_sdxl=1.14,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
                backend_solver_function="sample_dpmpp_3m_sde",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.18,
                measured_cost_ratio_sdxl=1.12,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.ddpm,
                backend_solver_function="sample_ddpm",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.05,
                measured_cost_ratio_sdxl=1.03,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.deis,
                backend_solver_function="sample_deis",
                numeric_knob_ranges=MappingProxyType({SAMPLER_SOLVER_KNOB.order: _DEIS_MAX_ORDER_RANGE}),
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.13,
                measured_cost_ratio_sdxl=0.96,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.ipndm,
                backend_solver_function="sample_ipndm",
                numeric_knob_ranges=MappingProxyType({SAMPLER_SOLVER_KNOB.order: _IPNDM_MAX_ORDER_RANGE}),
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.01,
                measured_cost_ratio_sdxl=1.00,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.res_multistep,
                backend_solver_function="sample_res_multistep",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.01,
                measured_cost_ratio_sdxl=0.98,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.gradient_estimation,
                backend_solver_function="sample_gradient_estimation",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.18,
                measured_cost_ratio_sdxl=0.99,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.heunpp2,
                backend_solver_function="sample_heunpp2",
                numeric_knob_ranges=_CHURN_KNOBS,
                evaluations_per_step=3,
                measured_cost_ratio_sd15=3.21,
                measured_cost_ratio_sdxl=2.93,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.er_sde,
                backend_solver_function="sample_er_sde",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.07,
                measured_cost_ratio_sdxl=0.98,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.sa_solver,
                backend_solver_function="sample_sa_solver",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.08,
                measured_cost_ratio_sdxl=0.94,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.euler_cfg_pp,
                backend_solver_function="sample_euler_cfg_pp",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.11,
                measured_cost_ratio_sdxl=1.10,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.euler_ancestral_cfg_pp,
                backend_solver_function="sample_euler_ancestral_cfg_pp",
                numeric_knob_ranges=MappingProxyType(
                    {
                        SAMPLER_SOLVER_KNOB.eta: _ETA_RANGE_UNIT,
                        SAMPLER_SOLVER_KNOB.s_noise: _S_NOISE_RANGE_NARROW,
                    },
                ),
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.15,
                measured_cost_ratio_sdxl=0.99,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.exp_heun_2_x0,
                backend_solver_function="sample_exp_heun_2_x0",
                solver_type_choices=_PHI_1_OR_PHI_2,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.08,
                measured_cost_ratio_sdxl=2.39,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.exp_heun_2_x0_sde,
                backend_solver_function="sample_exp_heun_2_x0_sde",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                solver_type_choices=_PHI_1_OR_PHI_2,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.27,
                measured_cost_ratio_sdxl=1.99,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_2s_ancestral_cfg_pp,
                backend_solver_function="sample_dpmpp_2s_ancestral_cfg_pp",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.14,
                measured_cost_ratio_sdxl=2.02,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_2m_cfg_pp,
                backend_solver_function="sample_dpmpp_2m_cfg_pp",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.01,
                measured_cost_ratio_sdxl=1.05,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde_heun,
                backend_solver_function="sample_dpmpp_2m_sde_heun",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                solver_type_choices=_MIDPOINT_OR_HEUN,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.27,
                measured_cost_ratio_sdxl=1.10,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.ipndm_v,
                backend_solver_function="sample_ipndm_v",
                numeric_knob_ranges=MappingProxyType({SAMPLER_SOLVER_KNOB.order: _IPNDM_MAX_ORDER_RANGE}),
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.11,
                measured_cost_ratio_sdxl=1.15,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.res_multistep_cfg_pp,
                backend_solver_function="sample_res_multistep_cfg_pp",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.08,
                measured_cost_ratio_sdxl=1.03,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.res_multistep_ancestral,
                backend_solver_function="sample_res_multistep_ancestral",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.13,
                measured_cost_ratio_sdxl=1.14,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.res_multistep_ancestral_cfg_pp,
                backend_solver_function="sample_res_multistep_ancestral_cfg_pp",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.11,
                measured_cost_ratio_sdxl=1.04,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.gradient_estimation_cfg_pp,
                backend_solver_function="sample_gradient_estimation_cfg_pp",
                evaluations_per_step=1,
                measured_cost_ratio_sd15=1.20,
                measured_cost_ratio_sdxl=1.02,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.seeds_2,
                backend_solver_function="sample_seeds_2",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                solver_type_choices=_PHI_1_OR_PHI_2,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.26,
                measured_cost_ratio_sdxl=1.88,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.seeds_3,
                backend_solver_function="sample_seeds_3",
                numeric_knob_ranges=_ANCESTRAL_KNOBS,
                evaluations_per_step=3,
                measured_cost_ratio_sd15=3.52,
                measured_cost_ratio_sdxl=2.82,
            ),
            _constraints(
                sampler=KNOWN_IMAGE_SAMPLERS.sa_solver_pece,
                backend_solver_function="sample_sa_solver_pece",
                numeric_knob_ranges=_S_NOISE_ONLY,
                evaluations_per_step=2,
                measured_cost_ratio_sd15=2.38,
                measured_cost_ratio_sdxl=2.11,
            ),
        ),
    ),
)
"""One record per known sampler, covering knob applicability, ranges, cost and identity."""


REJECTED_SAMPLER_SCHEDULER_PAIRINGS: frozenset[tuple[KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS]] = frozenset(
    {
        # Reproduces through the backend's own nodes with nothing else in the path: renders taken that
        # way, on both SD1.5 and SDXL at 8 and 25 steps, were judged on inspection to be static or
        # overcooked in every case. The substitute schedule was judged good on both baselines at 25
        # steps, which is what makes substitution a real alternative rather than a different failure.
        #
        # The substitute is not established at low step counts: at 8 steps it was judged static or
        # overcooked on SD1.5, and underbaked on SDXL by an estimated 3 to 7 steps. Anything relying on
        # this pairing being recoverable below roughly 12 steps is unverified.
        (KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde, KNOWN_IMAGE_SCHEDULERS.normal),
    },
)
"""Sampler and scheduler pairings that produce no usable image and are refused rather than substituted."""


SCHEDULER_BASELINE_APPLICABILITY: Mapping[KNOWN_IMAGE_SCHEDULERS, frozenset[KNOWN_IMAGE_GENERATION_BASELINE]] = (
    MappingProxyType(
        {
            # Both generate from a fixed sigma table rather than from the model, so neither is defined
            # for a family its table was not built for. The align_your_steps node says which families
            # those are: it takes a model family as an input and offers SD1 and SDXL, plus SVD, which is
            # not an image baseline.
            KNOWN_IMAGE_SCHEDULERS.align_your_steps: frozenset(
                {
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl,
                },
            ),
            # The gits node names no family at all: its tables are keyed by a coefficient. This
            # restriction is therefore a policy choice rather than something the backend declares, made
            # because the tables it ships are the ones published for the SD1 era. It stands until the
            # pairing is verified more broadly.
            KNOWN_IMAGE_SCHEDULERS.gits: frozenset(
                {
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl,
                },
            ),
        },
    )
)
"""Baselines each restricted scheduler is defined for. A scheduler absent here works on every baseline."""


CFG_PP_SAMPLERS: frozenset[KNOWN_IMAGE_SAMPLERS] = frozenset(
    {
        KNOWN_IMAGE_SAMPLERS.euler_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.euler_ancestral_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.dpmpp_2s_ancestral_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.dpmpp_2m_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.res_multistep_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.res_multistep_ancestral_cfg_pp,
        KNOWN_IMAGE_SAMPLERS.gradient_estimation_cfg_pp,
    },
)
"""The samplers applying the CFG++ correction, which expect a much lower `cfg_scale` than the rest."""


RECOMMENDED_SAMPLERS: frozenset[KNOWN_IMAGE_SAMPLERS] = frozenset(
    {
        KNOWN_IMAGE_SAMPLERS.k_euler,
        KNOWN_IMAGE_SAMPLERS.k_euler_a,
        KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m,
        KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
        KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde,
        KNOWN_IMAGE_SAMPLERS.lcm,
        KNOWN_IMAGE_SAMPLERS.uni_pc,
        KNOWN_IMAGE_SAMPLERS.DDIM,
    },
)
"""The samplers worth offering by default, settled by review rather than derived from the table.

Between them these cover the choices that actually differ: a cheap deterministic default, an ancestral
one, the multistep workhorse and its SDE variant, a second-order SDE, the few-step distilled case, a
predictor-corrector, and the reference solver.
"""


def presentation_tier(sampler: KNOWN_IMAGE_SAMPLERS) -> SAMPLER_PRESENTATION_TIER:
    """Return how prominently a sampler is worth offering.

    Args:
        sampler: The sampler to look up.

    Returns:
        `recommended` for the default-offer set, `advanced` for everything else.

    """
    if sampler in RECOMMENDED_SAMPLERS:
        return SAMPLER_PRESENTATION_TIER.recommended

    return SAMPLER_PRESENTATION_TIER.advanced


SAMPLER_PRESENTATION_TIERS: Mapping[KNOWN_IMAGE_SAMPLERS, SAMPLER_PRESENTATION_TIER] = MappingProxyType(
    {sampler: presentation_tier(sampler) for sampler in KNOWN_IMAGE_SAMPLERS},
)
"""The presentation tier of every known sampler, covering the vocabulary exhaustively."""


_COMFYANONYMOUS_DISCUSSION_227 = "comfyanonymous, ComfyUI GitHub discussion #227 (2023-03-23)"
_COMFYUI_DEV_MATRIX = (
    "comfyui.dev sampler/scheduler matrix. A third-party site with no affiliation to the backend's "
    "authors, and not endorsed by them."
)
_PROJECT_VISUAL_RULING = (
    "Project ruling, made by inspecting rendered comparisons of the claim against a fixed seed. "
    "Authoritative for this project, and the only evidence here that speaks to colour and to "
    "perceived quality, which the similarity measurements cannot."
)

SAMPLER_RECOMMENDATIONS: tuple[SamplerRecommendation, ...] = (
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.karras, KNOWN_IMAGE_SCHEDULERS.normal),
        provenance=CONSTRAINT_PROVENANCE.upstream_author,
        source=_COMFYANONYMOUS_DISCUSSION_227,
        summary="karras and normal are the schedules to use for most samplers.",
    ),
    SamplerRecommendation(
        samplers=(KNOWN_IMAGE_SAMPLERS.DDIM,),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.ddim_uniform,),
        provenance=CONSTRAINT_PROVENANCE.upstream_author,
        source=_COMFYANONYMOUS_DISCUSSION_227,
        summary="ddim_uniform is the schedule ddim is meant to be used with, matching the reference implementation.",
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.simple,),
        provenance=CONSTRAINT_PROVENANCE.upstream_author,
        source=_COMFYANONYMOUS_DISCUSSION_227,
        summary="simple worked well in some scenarios, such as the second pass of a hires fix.",
    ),
    SamplerRecommendation(
        samplers=(KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m, KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.karras,),
        provenance=CONSTRAINT_PROVENANCE.community,
        source=_COMFYUI_DEV_MATRIX,
        summary="The dpmpp_2m family is commonly paired with karras for smooth gradients and clean surfaces.",
    ),
    SamplerRecommendation(
        samplers=(KNOWN_IMAGE_SAMPLERS.k_euler, KNOWN_IMAGE_SAMPLERS.k_euler_a),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.normal, KNOWN_IMAGE_SCHEDULERS.simple),
        provenance=CONSTRAINT_PROVENANCE.community,
        source=_COMFYUI_DEV_MATRIX,
        summary="The euler family is commonly paired with normal or simple as an inexpensive general default.",
    ),
    SamplerRecommendation(
        samplers=(KNOWN_IMAGE_SAMPLERS.lcm,),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.sgm_uniform, KNOWN_IMAGE_SCHEDULERS.simple),
        provenance=CONSTRAINT_PROVENANCE.community,
        source=_COMFYUI_DEV_MATRIX,
        summary="Distilled and few-step solvers are commonly paired with a uniform schedule.",
    ),
    SamplerRecommendation(
        samplers=tuple(sorted(CFG_PP_SAMPLERS)),
        schedulers=(),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary="CFG++ solvers expect a cfg_scale near 1.0 to 2.0; the usual range oversaturates them.",
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.karras,),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "karras is not the safe choice at low step counts. Reach for it for fine detail at a normal "
            "step budget, not because the budget is short."
        ),
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.align_your_steps, KNOWN_IMAGE_SCHEDULERS.gits),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "align_your_steps and gits are recommended for low step counts, on the baselines they are "
            "defined for. Both exist to make a short step budget work."
        ),
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.exponential, KNOWN_IMAGE_SCHEDULERS.kl_optimal),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "exponential and kl_optimal render coherently but shift colour noticeably, toward a red or "
            "magenta cast. Treat that as a distinctive look to choose deliberately rather than a fault."
        ),
    ),
    SamplerRecommendation(
        samplers=(
            KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
            KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde_heun,
            KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
            KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde,
        ),
        schedulers=(),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary="The dpmpp SDE family stays usable with sampler_eta out to about 2.5.",
    ),
    SamplerRecommendation(
        samplers=(KNOWN_IMAGE_SAMPLERS.k_euler_a,),
        schedulers=(),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary="k_euler_a collapses with sampler_eta above about 1.0.",
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.beta,),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "beta shows a colour cast and posterisation at low step counts; at a normal step budget it "
            "renders cleanly with no cast."
        ),
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.ddim_uniform,),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "ddim_uniform degrades to glitchy static at very low step counts, but at a normal step "
            "budget it is not noticeably worse than simple."
        ),
    ),
    SamplerRecommendation(
        samplers=(),
        schedulers=(KNOWN_IMAGE_SCHEDULERS.linear_quadratic,),
        provenance=CONSTRAINT_PROVENANCE.user_ruled,
        source=_PROJECT_VISUAL_RULING,
        summary=(
            "linear_quadratic blurs heavily at every tested step count on both SD1.5 and SDXL, and "
            "stays largely unusable even at a normal step budget."
        ),
    ),
)
"""Advisory pairings and settings, each carrying the provenance of the claim.

Nothing here is enforced. The `community` entries in particular are folklore recorded for
completeness, not guidance the backend's authors have endorsed. The `user_ruled` entries were settled
by looking at rendered output and are authoritative for this project.

Every schedule-character claim that went to review is recorded here at `user_ruled`; `beta`,
`ddim_uniform` and `linear_quadratic` initially returned unsure for want of rendered examples and
were settled in a supplemental review of dedicated renders.
"""


def get_sampler_constraints(sampler: KNOWN_IMAGE_SAMPLERS) -> SamplerConstraints:
    """Return the constraint record for a sampler.

    Args:
        sampler: The sampler to look up.

    Returns:
        The record describing that sampler's knobs, cost and identity.

    Raises:
        KeyError: If the sampler has no record, which means the table has drifted from the enum.

    """
    return SAMPLER_CONSTRAINTS[sampler]


def evaluations_per_step(sampler: KNOWN_IMAGE_SAMPLERS) -> int:
    """Return how many model evaluations one step of this sampler performs.

    This is the durable, code-derived cost fact: a second-order sampler evaluates the model twice per
    step and therefore costs about twice as much as a first-order one at the same step count.

    The one sampler this does not describe is `k_dpm_adaptive`, which chooses its own step size and so
    performs a count unrelated to the requested steps. Its entry carries the pricing convention of 1.

    Args:
        sampler: The sampler to look up.

    Returns:
        The evaluation count for one step.

    """
    return SAMPLER_CONSTRAINTS[sampler].evaluations_per_step


def is_knob_applicable(sampler: KNOWN_IMAGE_SAMPLERS, knob: SAMPLER_SOLVER_KNOB) -> bool:
    """Return whether setting this knob on this sampler would have any effect.

    Args:
        sampler: The sampler the request names.
        knob: The knob the request wants to set.

    Returns:
        Whether the sampler's solver function accepts a keyword of that name.

    """
    return SAMPLER_CONSTRAINTS[sampler].accepts_knob(knob)


def applicable_knobs(sampler: KNOWN_IMAGE_SAMPLERS) -> frozenset[SAMPLER_SOLVER_KNOB]:
    """Return every knob this sampler accepts.

    Args:
        sampler: The sampler to look up.

    Returns:
        The knobs a request may set for it.

    """
    constraints = SAMPLER_CONSTRAINTS[sampler]
    knobs = set(constraints.numeric_knob_ranges)

    if constraints.solver_type_choices:
        knobs.add(SAMPLER_SOLVER_KNOB.solver_type)

    return frozenset(knobs)


def is_scheduler_applicable(scheduler: KNOWN_IMAGE_SCHEDULERS, baseline: KNOWN_IMAGE_GENERATION_BASELINE) -> bool:
    """Return whether a scheduler can generate sigmas for a baseline.

    Args:
        scheduler: The scheduler the request names.
        baseline: The baseline of the model the request names.

    Returns:
        Whether the pairing is defined. Schedulers with no baseline restriction are always applicable.

    """
    allowed_baselines = SCHEDULER_BASELINE_APPLICABILITY.get(scheduler)

    return allowed_baselines is None or baseline in allowed_baselines


def _numeric_knob_violations(
    constraints: SamplerConstraints,
    numeric_knobs: Mapping[SAMPLER_SOLVER_KNOB, float],
) -> list[ConstraintViolation]:
    """Return every violation among the numeric knobs a request set."""
    violations: list[ConstraintViolation] = []

    for knob, value in numeric_knobs.items():
        knob_range = constraints.numeric_knob_ranges.get(knob)

        if knob_range is None:
            violations.append(
                ConstraintViolation(
                    kind=CONSTRAINT_VIOLATION_KIND.knob_inapplicable,
                    detail=f"{constraints.sampler} does not accept {knob}.",
                ),
            )
            continue

        if not knob_range.contains(value):
            bounds = f"{knob_range.minimum} to {knob_range.maximum}"
            violations.append(
                ConstraintViolation(
                    kind=CONSTRAINT_VIOLATION_KIND.knob_out_of_range,
                    detail=f"{knob} on {constraints.sampler} must be within {bounds}, not {value}.",
                ),
            )

    return violations


def _solver_type_violations(
    constraints: SamplerConstraints,
    solver_type: KNOWN_SAMPLER_SOLVER_TYPES,
) -> list[ConstraintViolation]:
    """Return every violation arising from the `solver_type` a request set."""
    if not constraints.solver_type_choices:
        return [
            ConstraintViolation(
                kind=CONSTRAINT_VIOLATION_KIND.knob_inapplicable,
                detail=f"{constraints.sampler} does not accept {SAMPLER_SOLVER_KNOB.solver_type}.",
            ),
        ]

    if solver_type in constraints.solver_type_choices:
        return []

    accepted = ", ".join(constraints.solver_type_choices)

    return [
        ConstraintViolation(
            kind=CONSTRAINT_VIOLATION_KIND.solver_type_unsupported,
            detail=f"{constraints.sampler} accepts {accepted} as a solver type, not {solver_type}.",
        ),
    ]


def list_constraint_violations(
    *,
    sampler: KNOWN_IMAGE_SAMPLERS,
    scheduler: KNOWN_IMAGE_SCHEDULERS | None = None,
    baseline: KNOWN_IMAGE_GENERATION_BASELINE | None = None,
    numeric_knobs: Mapping[SAMPLER_SOLVER_KNOB, float] | None = None,
    solver_type: KNOWN_SAMPLER_SOLVER_TYPES | None = None,
) -> list[ConstraintViolation]:
    """Return every reason a request cannot be served exactly as asked.

    An empty list means the combination is renderable. A non-empty one is grounds for rejection rather
    than substitution: the caller asked for something the backend cannot do, and quietly doing something
    else would return an image nobody requested.

    Args:
        sampler: The sampler the request names.
        scheduler: The scheduler the request resolved to, if any.
        baseline: The baseline of the model the request names, if known.
        numeric_knobs: The numeric solver knobs the request set, keyed by knob.
        solver_type: The solver type the request set, if any.

    Returns:
        One entry per broken rule, in the order the rules are checked.

    Raises:
        KeyError: If the sampler has no constraint record.

    """
    constraints = SAMPLER_CONSTRAINTS[sampler]
    violations: list[ConstraintViolation] = []

    if numeric_knobs:
        violations.extend(_numeric_knob_violations(constraints, numeric_knobs))

    if solver_type is not None:
        violations.extend(_solver_type_violations(constraints, solver_type))

    if scheduler is not None and (sampler, scheduler) in REJECTED_SAMPLER_SCHEDULER_PAIRINGS:
        violations.append(
            ConstraintViolation(
                kind=CONSTRAINT_VIOLATION_KIND.sampler_scheduler_rejected,
                detail=f"{sampler} does not converge on the {scheduler} schedule.",
            ),
        )

    if scheduler is not None and baseline is not None and not is_scheduler_applicable(scheduler, baseline):
        allowed = ", ".join(sorted(SCHEDULER_BASELINE_APPLICABILITY[scheduler]))
        violations.append(
            ConstraintViolation(
                kind=CONSTRAINT_VIOLATION_KIND.scheduler_baseline_unsupported,
                detail=f"{scheduler} is only defined for {allowed}, not {baseline}.",
            ),
        )

    return violations
