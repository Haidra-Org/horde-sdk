"""Tests for unit-safe sampler trajectory and work accounting."""

from __future__ import annotations

import pytest

from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS
from horde_sdk.generation_parameters.image.sampler_work import (
    LATEST_SAMPLER_EXECUTION_CONTRACT_VERSION,
    SAMPLER_EXECUTION_CONTRACTS,
    SAMPLER_WORK_PROFILES,
    SamplerExecutionContractVersion,
    SamplerExecutionGuarantee,
    SamplerWorkEstimationPolicy,
    SamplerWorkUnitCount,
    TrajectoryStepCount,
    estimate_sampler_work,
    maximum_adaptive_solver_iterations,
    maximum_sampler_work,
    maximum_trajectory_steps_for_work_budget,
    minimum_common_sampler_execution_contract_version,
)

_AI_HORDE_POLICY = SamplerWorkEstimationPolicy(
    adaptive_sampler_work_units={
        KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive: SamplerWorkUnitCount(40),
    },
)


def test_work_profiles_cover_every_sampler() -> None:
    assert set(SAMPLER_WORK_PROFILES) == set(KNOWN_IMAGE_SAMPLERS)


def test_execution_contract_registry_covers_versions_and_is_cumulative() -> None:
    assert set(SAMPLER_EXECUTION_CONTRACTS) == set(SamplerExecutionContractVersion)

    guarantees_seen: frozenset[SamplerExecutionGuarantee] = frozenset()
    for contract_version, execution_contract in SAMPLER_EXECUTION_CONTRACTS.items():
        assert execution_contract.version is contract_version
        assert guarantees_seen <= execution_contract.guarantees
        guarantees_seen = execution_contract.guarantees


def test_common_execution_contract_fails_closed_for_a_legacy_backend_path() -> None:
    assert (
        minimum_common_sampler_execution_contract_version(
            [LATEST_SAMPLER_EXECUTION_CONTRACT_VERSION, None],
        )
        is None
    )


@pytest.mark.parametrize(
    ("sampler", "expected_work_units"),
    [
        (KNOWN_IMAGE_SAMPLERS.k_euler, 20),
        (KNOWN_IMAGE_SAMPLERS.k_heun, 40),
        (KNOWN_IMAGE_SAMPLERS.heunpp2, 60),
    ],
)
def test_fixed_sampler_work_uses_marginal_rate(
    sampler: KNOWN_IMAGE_SAMPLERS,
    expected_work_units: int,
) -> None:
    estimate = estimate_sampler_work(
        sampler=sampler,
        trajectory_steps=TrajectoryStepCount(20),
        estimation_policy=_AI_HORDE_POLICY,
    )
    assert estimate.work_units == SamplerWorkUnitCount(expected_work_units)


@pytest.mark.parametrize("trajectory_steps", [5, 20, 100])
def test_adaptive_estimate_is_service_owned_and_request_independent(trajectory_steps: int) -> None:
    estimate = estimate_sampler_work(
        sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
        trajectory_steps=TrajectoryStepCount(trajectory_steps),
        estimation_policy=_AI_HORDE_POLICY,
    )
    assert estimate.work_units == SamplerWorkUnitCount(40)


def test_adaptive_ceiling_requires_an_execution_guarantee() -> None:
    assert (
        maximum_sampler_work(
            sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
            trajectory_steps=TrajectoryStepCount(20),
            execution_contract_version=None,
            adaptive_work_units_per_iteration=3,
        )
        is None
    )


@pytest.mark.parametrize(("order", "expected_work_units"), [(2, 50), (3, 75)])
def test_bounded_adaptive_ceiling_includes_solver_order(order: int, expected_work_units: int) -> None:
    ceiling = maximum_sampler_work(
        sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
        trajectory_steps=TrajectoryStepCount(20),
        execution_contract_version=LATEST_SAMPLER_EXECUTION_CONTRACT_VERSION,
        adaptive_work_units_per_iteration=order,
    )
    assert ceiling is not None
    assert ceiling.work_units == SamplerWorkUnitCount(expected_work_units)
    assert maximum_adaptive_solver_iterations(trajectory_steps=TrajectoryStepCount(20)) == 25


def test_fixed_budget_is_inverted_without_a_decrement_loop() -> None:
    assert maximum_trajectory_steps_for_work_budget(
        sampler=KNOWN_IMAGE_SAMPLERS.k_heun,
        requested_trajectory_steps=TrajectoryStepCount(30),
        work_budget=SamplerWorkUnitCount(40),
        estimation_policy=_AI_HORDE_POLICY,
    ) == TrajectoryStepCount(20)


def test_over_budget_adaptive_request_cannot_be_repaired_by_reducing_steps() -> None:
    assert (
        maximum_trajectory_steps_for_work_budget(
            sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
            requested_trajectory_steps=TrajectoryStepCount(30),
            work_budget=SamplerWorkUnitCount(20),
            estimation_policy=_AI_HORDE_POLICY,
        )
        is None
    )
