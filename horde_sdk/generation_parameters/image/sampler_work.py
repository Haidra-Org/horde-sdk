"""Typed sampler trajectory, accounting, and execution-ceiling semantics.

A trajectory step describes progress through a denoising schedule. A sampler work unit instead
describes the marginal inference work of one ordinary first-order model evaluation at the same
payload. Work units deliberately are not exact neural-function-evaluation counts or wall-clock time:
fixed higher-order samplers have terminal-step special cases, and adaptive samplers choose their own
iteration count.

The module keeps those meanings separate. Atomic guarantees describe individual backend behaviors;
cumulative execution contracts give workers one discoverable conformance version to advertise.

Critical public members:

- Worker conformance is identified by
  [`SamplerExecutionContractVersion`][horde_sdk.generation_parameters.image.sampler_work.SamplerExecutionContractVersion].
- [`SAMPLER_WORK_PROFILES`][horde_sdk.generation_parameters.image.sampler_work.SAMPLER_WORK_PROFILES]
  defines marginal work for every sampler.
- [`maximum_sampler_work`][horde_sdk.generation_parameters.image.sampler_work.maximum_sampler_work]
  returns a finite ceiling only when the advertised execution contract proves one.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from strenum import StrEnum

from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS

__all__ = [
    "BOUNDED_DPM_ADAPTIVE_V1",
    "LATEST_SAMPLER_EXECUTION_CONTRACT_VERSION",
    "SAMPLER_EXECUTION_CONTRACTS",
    "SAMPLER_WORK_PROFILES",
    "AdaptiveSamplerExecutionPolicy",
    "AdaptiveSamplerWorkProfile",
    "FixedRateSamplerWorkProfile",
    "SamplerExecutionContract",
    "SamplerExecutionContractVersion",
    "SamplerExecutionGuarantee",
    "SamplerWorkCeiling",
    "SamplerWorkEstimate",
    "SamplerWorkEstimationPolicy",
    "SamplerWorkProfile",
    "SamplerWorkUnitCount",
    "TrajectoryStepCount",
    "estimate_sampler_work",
    "get_sampler_execution_contract",
    "get_sampler_work_profile",
    "maximum_adaptive_solver_iterations",
    "maximum_sampler_work",
    "maximum_trajectory_steps_for_work_budget",
    "minimum_common_sampler_execution_contract_version",
]


@dataclass(frozen=True, slots=True, order=True)
class TrajectoryStepCount:
    """Represents a positive number of requested denoising-schedule steps."""

    value: int

    def __post_init__(self) -> None:
        """Reject values that cannot represent an API image-generation request."""
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 1:
            raise ValueError("Trajectory steps must be a positive integer.")


@dataclass(frozen=True, slots=True, order=True)
class SamplerWorkUnitCount:
    """Represents a non-negative count of first-order-equivalent marginal sampler work units."""

    value: int

    def __post_init__(self) -> None:
        """Reject negative or boolean work-unit counts."""
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 0:
            raise ValueError("Sampler work units must be a non-negative integer.")


@dataclass(frozen=True, slots=True)
class FixedRateSamplerWorkProfile:
    """Represents a sampler whose marginal work is a fixed multiple of trajectory steps."""

    marginal_work_units_per_trajectory_step: int

    def __post_init__(self) -> None:
        """Require a usable positive marginal rate."""
        if (
            not isinstance(self.marginal_work_units_per_trajectory_step, int)
            or isinstance(self.marginal_work_units_per_trajectory_step, bool)
            or self.marginal_work_units_per_trajectory_step < 1
        ):
            raise ValueError("A fixed sampler work rate must be a positive integer.")


@dataclass(frozen=True, slots=True)
class AdaptiveSamplerWorkProfile:
    """Represents a sampler whose trajectory length does not determine its actual iteration count."""


type SamplerWorkProfile = FixedRateSamplerWorkProfile | AdaptiveSamplerWorkProfile


class SamplerExecutionGuarantee(StrEnum):
    """Identify one atomic sampler execution behavior contained by cumulative contracts."""

    BOUNDED_DPM_ADAPTIVE_V1 = "bounded_dpm_adaptive_v1"
    """DPM adaptive stops after ``ceil(5 / 4 * trajectory_steps)`` solver iterations."""


class SamplerExecutionContractVersion(StrEnum):
    """Identify a cumulative SDK-defined sampler execution behavior contract."""

    V1 = "1.0"
    """Require every execution guarantee introduced by sampler execution contract 1.0."""


@dataclass(frozen=True, slots=True)
class SamplerExecutionContract:
    """Represents a cumulative set of sampler execution guarantees a backend can implement."""

    version: SamplerExecutionContractVersion
    """Stable worker-facing conformance version."""

    guarantees: frozenset[SamplerExecutionGuarantee]
    """Atomic backend behaviors required by this cumulative version."""


@dataclass(frozen=True, slots=True)
class AdaptiveSamplerExecutionPolicy:
    """Represents the exact iteration ceiling promised by an adaptive execution guarantee."""

    guarantee: SamplerExecutionGuarantee
    sampler: KNOWN_IMAGE_SAMPLERS
    iteration_multiplier_numerator: int
    iteration_multiplier_denominator: int

    def __post_init__(self) -> None:
        """Require an exact positive rational multiplier."""
        terms = (self.iteration_multiplier_numerator, self.iteration_multiplier_denominator)
        if any(not isinstance(term, int) or isinstance(term, bool) or term < 1 for term in terms):
            raise ValueError("Adaptive iteration multiplier terms must be positive integers.")


BOUNDED_DPM_ADAPTIVE_V1: Final[AdaptiveSamplerExecutionPolicy] = AdaptiveSamplerExecutionPolicy(
    guarantee=SamplerExecutionGuarantee.BOUNDED_DPM_ADAPTIVE_V1,
    sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
    iteration_multiplier_numerator=5,
    iteration_multiplier_denominator=4,
)
"""The canonical finite execution policy for DPM adaptive."""


SAMPLER_EXECUTION_CONTRACTS: Mapping[SamplerExecutionContractVersion, SamplerExecutionContract] = MappingProxyType(
    {
        SamplerExecutionContractVersion.V1: SamplerExecutionContract(
            version=SamplerExecutionContractVersion.V1,
            guarantees=frozenset({SamplerExecutionGuarantee.BOUNDED_DPM_ADAPTIVE_V1}),
        ),
    },
)
"""All SDK-defined sampler execution contracts, ordered by their cumulative version."""

LATEST_SAMPLER_EXECUTION_CONTRACT_VERSION: Final[SamplerExecutionContractVersion] = (
    SamplerExecutionContractVersion.V1
)
"""The most recent sampler execution contract defined by this SDK release."""

_SAMPLER_EXECUTION_CONTRACT_ORDER: tuple[SamplerExecutionContractVersion, ...] = tuple(
    SAMPLER_EXECUTION_CONTRACTS,
)


@dataclass(frozen=True, slots=True)
class SamplerWorkEstimationPolicy:
    """Represents service-owned estimates for work that is not trajectory-derived."""

    adaptive_sampler_work_units: Mapping[KNOWN_IMAGE_SAMPLERS, SamplerWorkUnitCount]

    def __post_init__(self) -> None:
        """Freeze and validate the adaptive estimate map."""
        copied = dict(self.adaptive_sampler_work_units)
        for sampler in copied:
            if not isinstance(SAMPLER_WORK_PROFILES.get(sampler), AdaptiveSamplerWorkProfile):
                raise ValueError(f"{sampler!s} is not an adaptive sampler.")
        object.__setattr__(self, "adaptive_sampler_work_units", MappingProxyType(copied))


@dataclass(frozen=True, slots=True)
class SamplerWorkEstimate:
    """Represents a request's trajectory length and service-accounting work estimate."""

    sampler: KNOWN_IMAGE_SAMPLERS
    trajectory_steps: TrajectoryStepCount
    work_units: SamplerWorkUnitCount


@dataclass(frozen=True, slots=True)
class SamplerWorkCeiling:
    """Represents a finite upper bound guaranteed by the selected execution contract."""

    sampler: KNOWN_IMAGE_SAMPLERS
    trajectory_steps: TrajectoryStepCount
    work_units: SamplerWorkUnitCount
    execution_guarantee: SamplerExecutionGuarantee | None


SAMPLER_WORK_PROFILES: Mapping[KNOWN_IMAGE_SAMPLERS, SamplerWorkProfile] = MappingProxyType(
    {
        KNOWN_IMAGE_SAMPLERS.k_lms: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.k_heun: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.k_euler: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.k_euler_a: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.k_dpm_2: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.k_dpm_2_a: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.k_dpm_fast: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive: AdaptiveSamplerWorkProfile(),
        KNOWN_IMAGE_SAMPLERS.k_dpmpp_2s_a: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.dpmsolver: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.lcm: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.DDIM: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.uni_pc: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.uni_pc_bh2: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.ddpm: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.deis: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.ipndm: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.res_multistep: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.gradient_estimation: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.heunpp2: FixedRateSamplerWorkProfile(3),
        KNOWN_IMAGE_SAMPLERS.er_sde: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.sa_solver: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.euler_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.euler_ancestral_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.exp_heun_2_x0: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.exp_heun_2_x0_sde: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.dpmpp_2s_ancestral_cfg_pp: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.dpmpp_2m_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde_heun: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.ipndm_v: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.res_multistep_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.res_multistep_ancestral: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.res_multistep_ancestral_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.gradient_estimation_cfg_pp: FixedRateSamplerWorkProfile(1),
        KNOWN_IMAGE_SAMPLERS.seeds_2: FixedRateSamplerWorkProfile(2),
        KNOWN_IMAGE_SAMPLERS.seeds_3: FixedRateSamplerWorkProfile(3),
        KNOWN_IMAGE_SAMPLERS.sa_solver_pece: FixedRateSamplerWorkProfile(2),
    },
)
"""One work profile for every SDK sampler."""


def get_sampler_work_profile(sampler: KNOWN_IMAGE_SAMPLERS) -> SamplerWorkProfile:
    """Return the work profile for ``sampler``.

    Args:
        sampler: Sampler whose marginal work profile is required.

    Returns:
        The sampler's fixed-rate or adaptive work profile.

    Raises:
        KeyError: If the profile registry has drifted from the sampler enum.
    """
    return SAMPLER_WORK_PROFILES[sampler]


def get_sampler_execution_contract(
    version: SamplerExecutionContractVersion,
) -> SamplerExecutionContract:
    """Return the sampler execution contract identified by ``version``.

    Args:
        version: Stable execution contract version advertised by a worker.

    Returns:
        The cumulative contract associated with the version.

    Raises:
        KeyError: If the SDK's version enum and execution-contract registry have drifted.
    """
    return SAMPLER_EXECUTION_CONTRACTS[version]


def minimum_common_sampler_execution_contract_version(
    versions: Collection[SamplerExecutionContractVersion | None],
) -> SamplerExecutionContractVersion | None:
    """Return the newest contract guaranteed by every represented backend path.

    Contract versions are cumulative. A missing version therefore makes the combined profile legacy,
    while combining newer and older contracts yields the older shared contract.

    Args:
        versions: Contract versions for every backend path represented by a worker profile.

    Returns:
        The newest shared contract, or ``None`` when any path is legacy.

    Raises:
        ValueError: If ``versions`` is empty.
    """
    if not versions:
        raise ValueError("At least one sampler execution contract version is required.")
    if any(version is None for version in versions):
        return None

    contract_ranks = {version: rank for rank, version in enumerate(_SAMPLER_EXECUTION_CONTRACT_ORDER)}
    concrete_versions = [version for version in versions if version is not None]
    return min(concrete_versions, key=contract_ranks.__getitem__)


def estimate_sampler_work(
    *,
    sampler: KNOWN_IMAGE_SAMPLERS,
    trajectory_steps: TrajectoryStepCount,
    estimation_policy: SamplerWorkEstimationPolicy,
) -> SamplerWorkEstimate:
    """Return estimated service-accounting work without claiming an execution ceiling.

    Args:
        sampler: Sampler selected by the request.
        trajectory_steps: Requested denoising-schedule length.
        estimation_policy: Service-owned adaptive work estimates.

    Returns:
        The request's typed trajectory and estimated work values.

    Raises:
        ValueError: If an adaptive sampler has no service estimate.
    """
    profile = get_sampler_work_profile(sampler)
    if isinstance(profile, FixedRateSamplerWorkProfile):
        work_units = trajectory_steps.value * profile.marginal_work_units_per_trajectory_step
    else:
        try:
            work_units = estimation_policy.adaptive_sampler_work_units[sampler].value
        except KeyError as error:
            raise ValueError(f"No adaptive work estimate is configured for {sampler!s}.") from error
    return SamplerWorkEstimate(sampler, trajectory_steps, SamplerWorkUnitCount(work_units))


def maximum_adaptive_solver_iterations(
    *,
    trajectory_steps: TrajectoryStepCount,
    execution_policy: AdaptiveSamplerExecutionPolicy = BOUNDED_DPM_ADAPTIVE_V1,
) -> int:
    """Return the exact integer iteration ceiling for an adaptive execution policy.

    Args:
        trajectory_steps: Requested denoising-schedule length.
        execution_policy: Adaptive policy whose rational ceiling is enforced.

    Returns:
        Maximum permitted solver iterations, rounded upward.
    """
    numerator = trajectory_steps.value * execution_policy.iteration_multiplier_numerator
    denominator = execution_policy.iteration_multiplier_denominator
    return max(1, (numerator + denominator - 1) // denominator)


def maximum_sampler_work(
    *,
    sampler: KNOWN_IMAGE_SAMPLERS,
    trajectory_steps: TrajectoryStepCount,
    execution_contract_version: SamplerExecutionContractVersion | None,
    adaptive_work_units_per_iteration: int | None = None,
) -> SamplerWorkCeiling | None:
    """Return a finite work ceiling when the backend contract proves one.

    Args:
        sampler: Sampler selected by the request.
        trajectory_steps: Requested denoising-schedule length.
        execution_contract_version: Cumulative execution contract advertised by the backend.
        adaptive_work_units_per_iteration: Work units consumed by each adaptive solver iteration.

    Returns:
        A typed finite ceiling, or ``None`` when no finite ceiling is guaranteed.

    Raises:
        ValueError: If adaptive work per iteration is missing or invalid for a bounded contract.
    """
    profile = get_sampler_work_profile(sampler)
    if isinstance(profile, FixedRateSamplerWorkProfile):
        return SamplerWorkCeiling(
            sampler,
            trajectory_steps,
            SamplerWorkUnitCount(trajectory_steps.value * profile.marginal_work_units_per_trajectory_step),
            None,
        )

    if execution_contract_version is None:
        return None
    execution_contract = get_sampler_execution_contract(execution_contract_version)
    guarantee = SamplerExecutionGuarantee.BOUNDED_DPM_ADAPTIVE_V1
    if sampler is not BOUNDED_DPM_ADAPTIVE_V1.sampler or guarantee not in execution_contract.guarantees:
        return None
    if (
        not isinstance(adaptive_work_units_per_iteration, int)
        or isinstance(adaptive_work_units_per_iteration, bool)
        or adaptive_work_units_per_iteration < 1
    ):
        raise ValueError("Adaptive work ceilings require positive work units per solver iteration.")
    iterations = maximum_adaptive_solver_iterations(trajectory_steps=trajectory_steps)
    return SamplerWorkCeiling(
        sampler,
        trajectory_steps,
        SamplerWorkUnitCount(iterations * adaptive_work_units_per_iteration),
        guarantee,
    )


def maximum_trajectory_steps_for_work_budget(
    *,
    sampler: KNOWN_IMAGE_SAMPLERS,
    requested_trajectory_steps: TrajectoryStepCount,
    work_budget: SamplerWorkUnitCount,
    estimation_policy: SamplerWorkEstimationPolicy,
) -> TrajectoryStepCount | None:
    """Return the largest requested trajectory length within an estimated-work budget.

    An adaptive service estimate is request-independent. Reducing requested steps therefore cannot
    make an over-budget adaptive request fit; callers must reject it without changing sampler identity.

    Args:
        sampler: Sampler selected by the request.
        requested_trajectory_steps: Requested denoising-schedule length.
        work_budget: Maximum estimated work the service permits.
        estimation_policy: Service-owned adaptive work estimates.

    Returns:
        The largest permitted trajectory length, or ``None`` when step reduction cannot fit the budget.
    """
    profile = get_sampler_work_profile(sampler)
    if isinstance(profile, AdaptiveSamplerWorkProfile):
        estimate = estimate_sampler_work(
            sampler=sampler,
            trajectory_steps=requested_trajectory_steps,
            estimation_policy=estimation_policy,
        )
        return requested_trajectory_steps if estimate.work_units <= work_budget else None

    maximum_steps = min(
        requested_trajectory_steps.value,
        work_budget.value // profile.marginal_work_units_per_trajectory_step,
    )
    return TrajectoryStepCount(maximum_steps) if maximum_steps >= 1 else None
