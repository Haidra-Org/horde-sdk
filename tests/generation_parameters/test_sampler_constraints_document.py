"""Structural and drift checks for the sampler constraints document's wire type.

These models are the type of an HTTP response an API already serves, so their field names are the
served JSON keys and renaming one breaks every client parsing it. The checks split the same way as for
the table itself: structural rules that must hold for any correct type, and a committed snapshot of the
JSON schema so a change to the wire shape has to be deliberate.
"""

import json
from pathlib import Path
from typing import Any

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE

from horde_sdk.generation_parameters.image.constraints import (
    CONSTRAINT_PROVENANCE,
    KNOWN_SAMPLER_SOLVER_TYPES,
    SAMPLER_PRESENTATION_TIER,
)
from horde_sdk.generation_parameters.image.constraints_document import (
    AUTHORITATIVE_WORK_FIELD,
    SAMPLER_CONSTRAINTS_DOCUMENT_SCHEMA_VERSION,
    PublishedAdaptiveIterationCeiling,
    PublishedAdaptiveWorkProfile,
    PublishedAdvisories,
    PublishedBoundedAdaptiveSamplerExecutionGuarantee,
    PublishedFixedRateWorkProfile,
    PublishedHardConstraints,
    PublishedKnobRange,
    PublishedPresentationTiers,
    PublishedRecommendation,
    PublishedRejectedPairing,
    PublishedSamplerExecutionContract,
    PublishedSamplerRecord,
    PublishedWorkAccounting,
    SamplerConstraintsDocument,
)
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS
from horde_sdk.generation_parameters.image.sampler_work import (
    SamplerExecutionContractVersion,
)

_SCHEMA_SNAPSHOT_PATH = Path(__file__).parent / "sampler_constraints_document_schema_snapshot.json"


def _example_document() -> SamplerConstraintsDocument:
    """Create a document exercising every model in the tree, including the nullable fields."""
    return SamplerConstraintsDocument(
        samplers={
            KNOWN_IMAGE_SAMPLERS.k_euler: PublishedSamplerRecord(
                name=KNOWN_IMAGE_SAMPLERS.k_euler,
                work_profile=PublishedFixedRateWorkProfile(marginal_work_units_per_trajectory_step=1),
                measured_cost_ratio_sd15=1.0,
                measured_cost_ratio_sdxl=1.0,
                presentation_tier=SAMPLER_PRESENTATION_TIER.recommended,
                solver_type_choices=[],
                accepted_settings={
                    "sampler_s_tmax": PublishedKnobRange(
                        minimum=0.0,
                        maximum=None,
                        default=None,
                        integer_only=False,
                    ),
                },
                applies_cfg_pp=False,
            ),
            KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive: PublishedSamplerRecord(
                name=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
                work_profile=PublishedAdaptiveWorkProfile(
                    estimated_work_units_per_request=40,
                    finite_ceiling_contract_versions=[SamplerExecutionContractVersion.V1],
                ),
                measured_cost_ratio_sd15=None,
                measured_cost_ratio_sdxl=None,
                presentation_tier=SAMPLER_PRESENTATION_TIER.advanced,
                solver_type_choices=[KNOWN_SAMPLER_SOLVER_TYPES.midpoint, KNOWN_SAMPLER_SOLVER_TYPES.heun],
                accepted_settings={
                    "sampler_eta": PublishedKnobRange(minimum=0.0, maximum=100.0, default=1.0, integer_only=False),
                },
                applies_cfg_pp=False,
            ),
        },
        execution_contracts={
            SamplerExecutionContractVersion.V1: PublishedSamplerExecutionContract(
                version=SamplerExecutionContractVersion.V1,
                guarantees=[
                    PublishedBoundedAdaptiveSamplerExecutionGuarantee(
                        sampler=KNOWN_IMAGE_SAMPLERS.k_dpm_adaptive,
                        maximum_solver_iterations=PublishedAdaptiveIterationCeiling(
                            trajectory_multiplier_numerator=5,
                            trajectory_multiplier_denominator=4,
                        ),
                    ),
                ],
            ),
        },
        hard_constraints=PublishedHardConstraints(
            rejected_sampler_scheduler_pairings=[
                PublishedRejectedPairing(
                    sampler=KNOWN_IMAGE_SAMPLERS.dpmpp_3m_sde,
                    scheduler=KNOWN_IMAGE_SCHEDULERS.normal,
                ),
            ],
            scheduler_baseline_applicability={
                KNOWN_IMAGE_SCHEDULERS.align_your_steps: [
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_1,
                    KNOWN_IMAGE_GENERATION_BASELINE.stable_diffusion_xl,
                ],
            },
        ),
        recommendations=[
            PublishedRecommendation(
                samplers=[KNOWN_IMAGE_SAMPLERS.k_euler],
                schedulers=[KNOWN_IMAGE_SCHEDULERS.normal],
                provenance=CONSTRAINT_PROVENANCE.upstream_author,
                source="a citation",
                summary="a statement",
            ),
        ],
        advisories=PublishedAdvisories(cfg_pp_advised_max_cfg_scale=2.0),
        work_accounting=PublishedWorkAccounting(
            authoritative_note="what the authoritative field counts",
            measured_cost_ratio_provenance=CONSTRAINT_PROVENANCE.measured,
            measured_cost_ratio_source="an-artifact.json",
            measured_cost_ratio_note="how the ratios were derived",
            measured_cost_ratio_sdxl_note="the large model figure",
            measured_cost_ratio_sd15_note="the small model figure",
        ),
        presentation_tiers=PublishedPresentationTiers(
            note="the tier restricts nothing",
            recommended=[KNOWN_IMAGE_SAMPLERS.k_euler],
        ),
    )


class TestRoundTrip:
    def test_a_document_survives_serialisation_and_parsing(self) -> None:
        document = _example_document()
        served: dict[str, Any] = document.model_dump(mode="json")

        assert SamplerConstraintsDocument.model_validate(served) == document

    def test_the_served_form_is_strict_json(self) -> None:
        # An unbounded knob maximum is the obvious way to emit an infinity, which is not valid JSON.
        rendered = json.dumps(_example_document().model_dump(mode="json"), allow_nan=False)

        assert "Infinity" not in rendered

    def test_the_enum_valued_fields_serialise_to_their_wire_spellings(self) -> None:
        served = _example_document().model_dump(mode="json")

        assert set(served["samplers"]) == {"k_euler", "k_dpm_adaptive"}
        assert served["samplers"]["k_euler"]["presentation_tier"] == "recommended"
        assert served["recommendations"][0]["provenance"] == "upstream_author"
        assert served["hard_constraints"]["rejected_sampler_scheduler_pairings"][0] == {
            "sampler": "dpmpp_3m_sde",
            "scheduler": "normal",
        }

    def test_an_unbounded_knob_keeps_its_nulls(self) -> None:
        # Coercing these to a number would publish a bound the backend does not have.
        served = _example_document().model_dump(mode="json")
        tmax = served["samplers"]["k_euler"]["accepted_settings"]["sampler_s_tmax"]

        assert tmax["maximum"] is None
        assert tmax["default"] is None

    def test_the_operational_work_field_is_constant(self) -> None:
        assert _example_document().work_accounting.authoritative_field == AUTHORITATIVE_WORK_FIELD

    def test_document_and_execution_contract_versions_are_independent(self) -> None:
        document = _example_document()

        assert document.schema_version == SAMPLER_CONSTRAINTS_DOCUMENT_SCHEMA_VERSION
        assert set(document.execution_contracts) == {SamplerExecutionContractVersion.V1}


class TestSchemaSnapshot:
    def test_the_wire_shape_matches_the_committed_snapshot(self) -> None:
        # The schema is what a non-python client builds against, so a change to it is a change to the
        # published contract and has to be made on purpose. The snapshot is taken under the suite's own
        # model config, which forbids extra fields where production allows them, so `additionalProperties`
        # reads `false` here and `true` when a server derives the same schema.
        committed = json.loads(_SCHEMA_SNAPSHOT_PATH.read_text(encoding="utf-8"))

        assert SamplerConstraintsDocument.model_json_schema() == committed
