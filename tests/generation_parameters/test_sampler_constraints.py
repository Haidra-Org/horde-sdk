"""Coverage and drift checks for the per-sampler constraints table.

The table restates facts that live in the image backend's source. Nothing here can prove it read that
source correctly, so the checks split in two: structural rules that must hold for any correct table,
and a committed snapshot pinning every value so a change has to be deliberate.
"""

import json
from pathlib import Path
from typing import Any

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE

from horde_sdk.generation_parameters.image.constraints import (
    CFG_PP_SAMPLERS,
    CONSTRAINT_PROVENANCE,
    CONSTRAINT_VIOLATION_KIND,
    KNOWN_SAMPLER_SOLVER_TYPES,
    MEASURED_COST_RATIO_PROVENANCE,
    MEASURED_COST_RATIO_SOURCE,
    RECOMMENDED_SAMPLERS,
    REJECTED_SAMPLER_SCHEDULER_PAIRINGS,
    SAMPLER_CONSTRAINTS,
    SAMPLER_PRESENTATION_TIER,
    SAMPLER_PRESENTATION_TIERS,
    SAMPLER_RECOMMENDATIONS,
    SAMPLER_SOLVER_KNOB,
    SCHEDULER_BASELINE_APPLICABILITY,
    applicable_knobs,
    get_sampler_constraints,
    is_knob_applicable,
    list_constraint_violations,
    presentation_tier,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS
from horde_sdk.generation_parameters.image.sampler_work import (
    AdaptiveSamplerWorkProfile,
    FixedRateSamplerWorkProfile,
    get_sampler_work_profile,
)

_SNAPSHOT_PATH = Path(__file__).parent / "sampler_constraints_snapshot.json"


def _snapshot_of_table() -> dict[str, Any]:
    """Render the table into the plain shape the committed snapshot stores."""
    snapshot: dict[str, Any] = {}

    for sampler, constraints in SAMPLER_CONSTRAINTS.items():
        snapshot[sampler.value] = {
            "backend_solver_function": constraints.backend_solver_function,
            "numeric_knob_ranges": {
                knob.value: {
                    "minimum": knob_range.minimum,
                    "maximum": knob_range.maximum,
                    "default": knob_range.default,
                    "integral": knob_range.integral,
                    "backend_keyword": knob_range.backend_keyword,
                }
                for knob, knob_range in sorted(constraints.numeric_knob_ranges.items())
            },
            "solver_type_choices": [choice.value for choice in constraints.solver_type_choices],
            "work_profile": (
                {"kind": "adaptive"}
                if isinstance(constraints.work_profile, AdaptiveSamplerWorkProfile)
                else {
                    "kind": "fixed_rate",
                    "marginal_work_units_per_trajectory_step": (
                        constraints.work_profile.marginal_work_units_per_trajectory_step
                    ),
                }
            ),
            "measured_cost_ratio_sd15": constraints.measured_cost_ratio_sd15,
            "measured_cost_ratio_sdxl": constraints.measured_cost_ratio_sdxl,
            "presentation_tier": SAMPLER_PRESENTATION_TIERS[sampler].value,
        }

    return snapshot


class TestCoverage:
    def test_every_known_sampler_has_a_record(self) -> None:
        assert set(SAMPLER_CONSTRAINTS) == set(KNOWN_IMAGE_SAMPLERS)

    def test_every_record_is_keyed_by_the_sampler_it_names(self) -> None:
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            assert constraints.sampler == sampler

    def test_every_sampler_has_an_explicit_work_profile(self) -> None:
        for sampler in KNOWN_IMAGE_SAMPLERS:
            assert get_sampler_work_profile(sampler) is not None

    def test_every_declared_range_admits_its_own_default(self) -> None:
        for constraints in SAMPLER_CONSTRAINTS.values():
            for knob, knob_range in constraints.numeric_knob_ranges.items():
                assert knob_range.contains(knob_range.default), (constraints.sampler, knob)

    def test_rejected_pairings_name_real_values(self) -> None:
        for sampler, scheduler in REJECTED_SAMPLER_SCHEDULER_PAIRINGS:
            assert sampler in KNOWN_IMAGE_SAMPLERS
            assert scheduler in KNOWN_IMAGE_SCHEDULERS

    def test_baseline_gated_schedulers_allow_at_least_one_baseline(self) -> None:
        for scheduler, baselines in SCHEDULER_BASELINE_APPLICABILITY.items():
            assert scheduler in KNOWN_IMAGE_SCHEDULERS
            assert baselines
            assert baselines <= set(KNOWN_IMAGE_GENERATION_BASELINE)


class TestKnobApplicability:
    def test_solver_type_is_only_offered_where_a_vocabulary_exists(self) -> None:
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            expected = bool(constraints.solver_type_choices)
            assert is_knob_applicable(sampler, SAMPLER_SOLVER_KNOB.solver_type) is expected, sampler

    def test_only_the_dpmpp_2m_sde_pair_takes_midpoint_or_heun(self) -> None:
        # Every other solver_type vocabulary in the backend belongs to a different solver family.
        takers = {
            sampler
            for sampler, constraints in SAMPLER_CONSTRAINTS.items()
            if KNOWN_SAMPLER_SOLVER_TYPES.midpoint in constraints.solver_type_choices
        }

        assert takers == {
            KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
            KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde_heun,
        }

    def test_the_sa_solver_family_takes_no_order_knob(self) -> None:
        # It splits the concept into a predictor order and a corrector order, which one number cannot
        # express. Unlike the multistep solvers, this is a different concept rather than another spelling.
        for sampler in (KNOWN_IMAGE_SAMPLERS.sa_solver, KNOWN_IMAGE_SAMPLERS.sa_solver_pece):
            assert not is_knob_applicable(sampler, SAMPLER_SOLVER_KNOB.order)

    def test_the_multistep_solvers_take_the_order_knob_under_their_own_spelling(self) -> None:
        # These declare `max_order`, which is the same concept. Treating the spelling difference as an
        # absence would refuse a setting that genuinely reaches them.
        for sampler in (KNOWN_IMAGE_SAMPLERS.deis, KNOWN_IMAGE_SAMPLERS.ipndm, KNOWN_IMAGE_SAMPLERS.ipndm_v):
            assert is_knob_applicable(sampler, SAMPLER_SOLVER_KNOB.order), sampler
            knob_range = SAMPLER_CONSTRAINTS[sampler].numeric_knob_ranges[SAMPLER_SOLVER_KNOB.order]
            assert knob_range.backend_keyword == "max_order", sampler

    def test_the_multistep_order_floor_is_two(self) -> None:
        # At 1 all three index their history buffer before anything is in it, which raises from inside
        # the sampling loop rather than being reported as a bad argument.
        for sampler in (KNOWN_IMAGE_SAMPLERS.deis, KNOWN_IMAGE_SAMPLERS.ipndm, KNOWN_IMAGE_SAMPLERS.ipndm_v):
            knob_range = SAMPLER_CONSTRAINTS[sampler].numeric_knob_ranges[SAMPLER_SOLVER_KNOB.order]
            assert knob_range.minimum == 2.0, sampler
            assert knob_range.maximum == 4.0, sampler

    def test_the_single_step_order_solvers_keep_their_own_spelling(self) -> None:
        # `k_lms` and `k_dpm_adaptive` declare `order` outright, so they record no separate spelling.
        for sampler in (KNOWN_IMAGE_SAMPLERS.k_lms, KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive):
            knob_range = SAMPLER_CONSTRAINTS[sampler].numeric_knob_ranges[SAMPLER_SOLVER_KNOB.order]
            assert knob_range.backend_keyword is None, sampler

    def test_a_recorded_backend_spelling_is_only_ever_for_the_order_knob(self) -> None:
        # Every other knob is spelled the same on both sides; a stray override would silently misroute it.
        for constraints in SAMPLER_CONSTRAINTS.values():
            for knob, knob_range in constraints.numeric_knob_ranges.items():
                if knob_range.backend_keyword is not None:
                    assert knob is SAMPLER_SOLVER_KNOB.order, (constraints.sampler, knob)

    def test_er_sde_takes_no_eta(self) -> None:
        # The backend's node offers an eta, but it builds a noise scaler from it rather than passing it.
        assert not is_knob_applicable(KNOWN_IMAGE_SAMPLERS.er_sde, SAMPLER_SOLVER_KNOB.eta)

    def test_gradient_estimation_takes_none_of_the_knobs(self) -> None:
        for sampler in (KNOWN_IMAGE_SAMPLERS.gradient_estimation, KNOWN_IMAGE_SAMPLERS.gradient_estimation_cfg_pp):
            assert applicable_knobs(sampler) == frozenset()

    def test_dpm_fast_takes_none_of_the_knobs(self) -> None:
        # The backend wraps it in a closure that forwards no extra options, whatever its signature says.
        assert applicable_knobs(KNOWN_IMAGE_SAMPLERS.k_dpm_fast) == frozenset()

    def test_the_churn_window_travels_with_s_churn(self) -> None:
        for sampler in KNOWN_IMAGE_SAMPLERS:
            knobs = applicable_knobs(sampler)
            if SAMPLER_SOLVER_KNOB.s_churn not in knobs:
                continue
            assert SAMPLER_SOLVER_KNOB.s_tmin in knobs, sampler
            assert SAMPLER_SOLVER_KNOB.s_tmax in knobs, sampler


class TestViolations:
    def test_a_plain_request_has_no_violations(self) -> None:
        assert (
            list_constraint_violations(
                sampler=KNOWN_IMAGE_SAMPLERS.k_euler,
                scheduler=KNOWN_IMAGE_SCHEDULERS.karras,
                baseline=KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
            )
            == []
        )

    def test_an_inapplicable_knob_is_reported(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.k_euler,
            numeric_knobs={SAMPLER_SOLVER_KNOB.eta: 0.5},
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.knob_inapplicable]

    def test_an_out_of_range_knob_is_reported(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
            numeric_knobs={SAMPLER_SOLVER_KNOB.order: 4},
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.knob_out_of_range]

    def test_an_integral_knob_rejects_a_fraction(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.k_lms,
            numeric_knobs={SAMPLER_SOLVER_KNOB.order: 2.5},
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.knob_out_of_range]

    def test_a_foreign_solver_type_is_reported(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
            solver_type=KNOWN_SAMPLER_SOLVER_TYPES.phi_1,
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.solver_type_unsupported]

    def test_a_solver_type_on_a_sampler_without_one_is_reported(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.k_euler,
            solver_type=KNOWN_SAMPLER_SOLVER_TYPES.heun,
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.knob_inapplicable]

    def test_the_divergent_pairing_is_rejected(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
            scheduler=KNOWN_IMAGE_SCHEDULERS.normal,
        )

        assert [violation.kind for violation in violations] == [CONSTRAINT_VIOLATION_KIND.sampler_scheduler_rejected]

    def test_the_same_sampler_is_fine_on_another_schedule(self) -> None:
        assert (
            list_constraint_violations(
                sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
                scheduler=KNOWN_IMAGE_SCHEDULERS.karras,
            )
            == []
        )

    def test_a_sigma_generator_on_the_wrong_baseline_is_rejected(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.k_euler,
            scheduler=KNOWN_IMAGE_SCHEDULERS.align_your_steps,
            baseline=KNOWN_IMAGE_GENERATION_BASELINE.flux_1,
        )

        assert [violation.kind for violation in violations] == [
            CONSTRAINT_VIOLATION_KIND.scheduler_baseline_unsupported,
        ]

    def test_several_violations_are_all_reported(self) -> None:
        violations = list_constraint_violations(
            sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
            scheduler=KNOWN_IMAGE_SCHEDULERS.normal,
            numeric_knobs={SAMPLER_SOLVER_KNOB.s_churn: 1.0},
        )

        assert {violation.kind for violation in violations} == {
            CONSTRAINT_VIOLATION_KIND.knob_inapplicable,
            CONSTRAINT_VIOLATION_KIND.sampler_scheduler_rejected,
        }

    def test_every_sampler_accepts_a_request_that_sets_nothing(self) -> None:
        for sampler in KNOWN_IMAGE_SAMPLERS:
            assert list_constraint_violations(sampler=sampler) == [], sampler

    def test_every_applicable_knob_accepts_its_own_default(self) -> None:
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            defaults = {
                knob: knob_range.default
                for knob, knob_range in constraints.numeric_knob_ranges.items()
                # An infinite default cannot be sent over the wire, so it is not a value to check.
                if knob_range.default != float("inf")
            }
            assert list_constraint_violations(sampler=sampler, numeric_knobs=defaults) == [], sampler


class TestRecommendations:
    def test_every_recommendation_names_real_values(self) -> None:
        for recommendation in SAMPLER_RECOMMENDATIONS:
            assert recommendation.provenance in CONSTRAINT_PROVENANCE
            assert recommendation.source
            assert recommendation.summary
            for sampler in recommendation.samplers:
                assert sampler in KNOWN_IMAGE_SAMPLERS
            for scheduler in recommendation.schedulers:
                assert scheduler in KNOWN_IMAGE_SCHEDULERS

    def test_the_third_party_matrix_is_never_credited_upstream(self) -> None:
        # Mislabelling folklore as the backend author's guidance is the specific error being guarded.
        for recommendation in SAMPLER_RECOMMENDATIONS:
            if "comfyui.dev" in recommendation.source:
                assert recommendation.provenance == CONSTRAINT_PROVENANCE.community

    def test_the_cfg_pp_set_is_exactly_the_cfg_pp_named_samplers(self) -> None:
        assert {sampler for sampler in KNOWN_IMAGE_SAMPLERS if sampler.value.endswith("_cfg_pp")} == CFG_PP_SAMPLERS


class TestMeasuredCostRatios:
    def test_the_ratios_are_labelled_as_measured(self) -> None:
        assert CONSTRAINT_PROVENANCE.measured == MEASURED_COST_RATIO_PROVENANCE
        assert MEASURED_COST_RATIO_SOURCE.endswith(".json")

    def test_every_sampler_but_the_adaptive_one_carries_both_figures(self) -> None:
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            if sampler is KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive:
                continue

            assert constraints.measured_cost_ratio_sd15 is not None, sampler
            assert constraints.measured_cost_ratio_sdxl is not None, sampler

    def test_the_adaptive_sampler_publishes_no_ratio(self) -> None:
        # It picks its own step count, so wall time per requested step is not a quantity it has.
        adaptive = SAMPLER_CONSTRAINTS[KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive]

        assert adaptive.measured_cost_ratio_sd15 is None
        assert adaptive.measured_cost_ratio_sdxl is None

    def test_the_reference_sampler_measures_as_its_own_unit(self) -> None:
        reference = SAMPLER_CONSTRAINTS[KNOWN_IMAGE_SAMPLERS.k_euler]

        assert reference.measured_cost_ratio_sd15 == 1.00
        assert reference.measured_cost_ratio_sdxl == 1.00

    def test_the_large_model_ratios_corroborate_fixed_work_rates(self) -> None:
        # The claim the measurement supports: at 1024x1024, where per-step host work is a negligible
        # fraction of a step, every sampler lands within a fifth of its evaluation family.
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            if constraints.measured_cost_ratio_sdxl is None:
                continue

            assert isinstance(constraints.work_profile, FixedRateSamplerWorkProfile)
            expected = float(constraints.work_profile.marginal_work_units_per_trajectory_step)
            assert abs(constraints.measured_cost_ratio_sdxl - expected) <= 0.2 * expected, sampler

    def test_the_small_model_ratios_are_biased_upwards_and_never_downwards(self) -> None:
        # The 512x512 step is short enough that per-step host work shows up in the ratio. That inflates
        # a sampler's figure; nothing about it can deflate one below its family.
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            if constraints.measured_cost_ratio_sd15 is None:
                continue

            assert isinstance(constraints.work_profile, FixedRateSamplerWorkProfile)
            expected = float(constraints.work_profile.marginal_work_units_per_trajectory_step)
            assert constraints.measured_cost_ratio_sd15 >= expected, sampler


class TestSnapshot:
    def test_the_table_matches_the_committed_snapshot(self) -> None:
        committed = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))

        assert _snapshot_of_table() == committed

    def test_the_lookup_helper_agrees_with_the_table(self) -> None:
        for sampler, constraints in SAMPLER_CONSTRAINTS.items():
            assert get_sampler_constraints(sampler) is constraints


class TestPresentationTiers:
    """The tier split is presentation only: it must cover the vocabulary and change nothing else."""

    def test_every_sampler_has_a_tier(self) -> None:
        assert set(SAMPLER_PRESENTATION_TIERS) == set(KNOWN_IMAGE_SAMPLERS)

    def test_the_recommended_tier_is_exactly_the_ruled_set(self) -> None:
        recommended = {
            sampler
            for sampler, tier in SAMPLER_PRESENTATION_TIERS.items()
            if tier is SAMPLER_PRESENTATION_TIER.recommended
        }

        assert recommended == {
            KNOWN_IMAGE_SAMPLERS.k_euler,
            KNOWN_IMAGE_SAMPLERS.k_euler_a,
            KNOWN_IMAGE_SAMPLERS.k_dpmpp_2m,
            KNOWN_IMAGE_SAMPLERS.dpmpp_2m_sde,
            KNOWN_IMAGE_SAMPLERS.k_dpmpp_sde,
            KNOWN_IMAGE_SAMPLERS.lcm,
            KNOWN_IMAGE_SAMPLERS.uni_pc,
            KNOWN_IMAGE_SAMPLERS.DDIM,
        }

    def test_the_recommended_set_and_the_tier_map_agree(self) -> None:
        for sampler in RECOMMENDED_SAMPLERS:
            assert presentation_tier(sampler) is SAMPLER_PRESENTATION_TIER.recommended, sampler

    def test_everything_else_is_advanced(self) -> None:
        for sampler in KNOWN_IMAGE_SAMPLERS:
            if sampler in RECOMMENDED_SAMPLERS:
                continue
            assert presentation_tier(sampler) is SAMPLER_PRESENTATION_TIER.advanced, sampler

    def test_the_tier_does_not_restrict_anything(self) -> None:
        # An advanced sampler is offered less prominently, never accepted less readily.
        for sampler in KNOWN_IMAGE_SAMPLERS:
            assert list_constraint_violations(sampler=sampler) == [], sampler


class TestRuledProvenance:
    """Claims settled by looking at renders carry user_ruled, at the strength they were settled at."""

    def _summaries_for(self, provenance: CONSTRAINT_PROVENANCE) -> str:
        return " ".join(rec.summary for rec in SAMPLER_RECOMMENDATIONS if rec.provenance is provenance)

    def test_the_cfg_pp_guidance_is_ruled_rather_than_folklore(self) -> None:
        cfg_pp_recommendations = [rec for rec in SAMPLER_RECOMMENDATIONS if "CFG++" in rec.summary]

        assert cfg_pp_recommendations
        for recommendation in cfg_pp_recommendations:
            assert recommendation.provenance is CONSTRAINT_PROVENANCE.user_ruled

    def test_the_ruled_claims_are_present(self) -> None:
        ruled = self._summaries_for(CONSTRAINT_PROVENANCE.user_ruled)

        assert "karras is not the safe choice at low step counts" in ruled
        assert "align_your_steps and gits are recommended for low step counts" in ruled
        assert "exponential and kl_optimal" in ruled
        assert "2.5" in ruled
        assert "k_euler_a collapses" in ruled

    def test_the_supplementally_settled_schedules_carry_ruled_character_claims(self) -> None:
        # These three initially returned unsure for want of rendered examples and were settled in a
        # supplemental review of dedicated renders.
        ruled = self._summaries_for(CONSTRAINT_PROVENANCE.user_ruled)
        for schedule in ("beta", "ddim_uniform", "linear_quadratic"):
            assert schedule in ruled, schedule

    def test_ddim_uniform_carries_both_claims_at_their_own_provenance(self) -> None:
        # The backend author's pairing advice and the ruled character claim are different claims about
        # the same schedule, and each keeps the provenance it was settled at.
        provenances = {
            recommendation.provenance
            for recommendation in SAMPLER_RECOMMENDATIONS
            if KNOWN_IMAGE_SCHEDULERS.ddim_uniform in recommendation.schedulers
        }
        assert provenances == {
            CONSTRAINT_PROVENANCE.upstream_author,
            CONSTRAINT_PROVENANCE.user_ruled,
        }

    def test_the_low_step_schedules_are_recommended_for_low_steps(self) -> None:
        matches = [
            rec
            for rec in SAMPLER_RECOMMENDATIONS
            if KNOWN_IMAGE_SCHEDULERS.align_your_steps in rec.schedulers
            and KNOWN_IMAGE_SCHEDULERS.gits in rec.schedulers
        ]

        assert len(matches) == 1
        assert matches[0].provenance is CONSTRAINT_PROVENANCE.user_ruled
