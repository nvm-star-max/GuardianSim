from __future__ import annotations

import copy
import unittest
from collections import Counter

from guardian_sim.safety_swarm import safety_swarm_smoke_world_ids
from guardian_sim.safety_swarm_v2 import (
    SAFETY_SWARM_V2_TRIAD_CANDIDATE_IDS,
    CandidateWorldMeasurement,
    assemble_safety_swarm_v2_smoke_report,
    assign_candidate_worlds,
    build_safety_swarm_v2_candidate_catalog,
    build_safety_swarm_v2_formal_protocol,
    build_safety_swarm_v2_offline_fixture_measurements,
    build_safety_swarm_v2_smoke_protocol,
    safety_swarm_v2_candidate_catalog_sha256,
    safety_swarm_v2_tier_definition,
    validate_safety_swarm_v2_smoke_report,
)


class SafetySwarmV2Tests(unittest.TestCase):
    def _fixture_report(self) -> dict[str, object]:
        return assemble_safety_swarm_v2_smoke_report(
            build_safety_swarm_v2_offline_fixture_measurements(),
            tier="triad-4",
            wall_seconds=1.5,
            mode="offline_fixture",
            backend="deterministic_fixture",
            source_commit="fixture",
        )

    def test_candidate_catalog_and_formal_protocol_are_frozen(self) -> None:
        catalog = build_safety_swarm_v2_candidate_catalog()
        self.assertEqual(len(catalog), 18)
        self.assertEqual(
            [candidate.candidate_index for candidate in catalog],
            list(range(18)),
        )
        self.assertEqual(len({candidate.candidate_id for candidate in catalog}), 18)
        self.assertEqual(
            safety_swarm_v2_candidate_catalog_sha256(),
            "9c3af60dfb812e6128f6e849d27cf2acd0d672cdcb3aa98191656e4009054e44",
        )
        protocol = build_safety_swarm_v2_formal_protocol()
        self.assertEqual(protocol["candidate_count"], 18)
        self.assertEqual(protocol["world_count_per_candidate"], 256)
        self.assertEqual(protocol["candidate_world_count"], 4608)
        self.assertEqual(
            protocol["protocol_sha256"],
            "7fedeeeea436f3b0fe04196e4ad5ec225ccfe7bf26ad60cd3af8a7a4f4da43ac",
        )

    def test_smoke_tiers_are_predeclared_cartesian_products(self) -> None:
        expected = {"triad-4": 12, "full-4": 72, "full-16": 288}
        for tier, pair_count in expected.items():
            candidate_ids, world_ids = safety_swarm_v2_tier_definition(tier)
            assignments = assign_candidate_worlds(candidate_ids, world_ids)
            protocol = build_safety_swarm_v2_smoke_protocol(tier)
            self.assertEqual(len(assignments), pair_count)
            self.assertEqual(protocol["candidate_world_count"], pair_count)
            self.assertEqual(
                Counter(assignment.candidate_id for assignment in assignments),
                Counter({candidate_id: len(world_ids) for candidate_id in candidate_ids}),
            )
            self.assertEqual(
                Counter(assignment.world_id for assignment in assignments),
                Counter({world_id: len(candidate_ids) for world_id in world_ids}),
            )
        self.assertEqual(
            safety_swarm_v2_tier_definition("triad-4"),
            (SAFETY_SWARM_V2_TRIAD_CANDIDATE_IDS, safety_swarm_smoke_world_ids(4)),
        )

    def test_fixture_selects_only_candidate_that_passes_every_world(self) -> None:
        report = self._fixture_report()
        validation = validate_safety_swarm_v2_smoke_report(report)
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(validation["candidate_world_count"], 12)
        self.assertEqual(validation["decision"], "execute")
        self.assertEqual(
            validation["selected_candidate_id"],
            "yaw_+67.5_retreat_+0.000_approach_+0.140",
        )
        summaries = {
            summary["candidate_id"]: summary
            for summary in report["candidate_summaries"]
        }
        self.assertFalse(summaries["yaw_+00.0_offset_+0.000"]["qualifies"])
        self.assertTrue(
            summaries[
                "yaw_+67.5_retreat_+0.000_approach_+0.140"
            ]["qualifies"]
        )
        self.assertFalse(
            summaries[
                "yaw_+67.5_retreat_+0.025_approach_+0.140"
            ]["qualifies"]
        )
        self.assertFalse(report["showcase_ready"])

    def test_no_qualified_candidate_produces_typed_safe_stop(self) -> None:
        measurements = list(build_safety_swarm_v2_offline_fixture_measurements())
        winner = "yaw_+67.5_retreat_+0.000_approach_+0.140"
        measurements = [
            (
                CandidateWorldMeasurement(
                    candidate_id=value.candidate_id,
                    world_id=value.world_id,
                    minimum_clearance_m=0.005,
                    stability=value.stability,
                    reachable=value.reachable,
                    task_completed=value.task_completed,
                    clutter_contact=value.clutter_contact,
                    elapsed_environment_steps=value.elapsed_environment_steps,
                )
                if value.candidate_id == winner and value.world_id == 0
                else value
            )
            for value in measurements
        ]
        report = assemble_safety_swarm_v2_smoke_report(
            measurements,
            tier="triad-4",
            wall_seconds=1.0,
            mode="offline_fixture",
            backend="deterministic_fixture",
            source_commit="fixture",
        )
        self.assertEqual(report["summary"]["decision"], "safe_stop")
        self.assertIsNone(report["summary"]["selected_candidate_id"])
        self.assertEqual(report["summary"]["qualifying_candidate_ids"], [])

    def test_radeon_smoke_requires_amd_hip_and_telemetry(self) -> None:
        report = assemble_safety_swarm_v2_smoke_report(
            build_safety_swarm_v2_offline_fixture_measurements(),
            tier="triad-4",
            wall_seconds=2.0,
            mode="radeon_engineering_smoke",
            backend="genesis_gpu_batched",
            source_commit="a" * 40,
            device={"name": "AMD Radeon Graphics", "hip_version": "7.2"},
            gpu_telemetry={"sample_count": 3},
        )
        validation = validate_safety_swarm_v2_smoke_report(
            report,
            require_radeon=True,
        )
        self.assertEqual(validation["status"], "passed")
        self.assertFalse(validation["showcase_ready"])

    def test_validator_rejects_matrix_label_summary_and_hash_tampering(self) -> None:
        report = self._fixture_report()

        matrix = copy.deepcopy(report)
        matrix["results"][0]["perturbation"]["target_dx_m"] = 3.0
        with self.assertRaisesRegex(ValueError, "matrix drift"):
            validate_safety_swarm_v2_smoke_report(matrix)

        label = copy.deepcopy(report)
        label["results"][0]["hard_safe"] = not label["results"][0]["hard_safe"]
        with self.assertRaisesRegex(ValueError, "label drift"):
            validate_safety_swarm_v2_smoke_report(label)

        summary = copy.deepcopy(report)
        summary["summary"]["selected_candidate_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "selection summary"):
            validate_safety_swarm_v2_smoke_report(summary)

        report_hash = copy.deepcopy(report)
        report_hash["source"]["commit"] = "changed"
        with self.assertRaisesRegex(ValueError, "report hash"):
            validate_safety_swarm_v2_smoke_report(report_hash)


if __name__ == "__main__":
    unittest.main()
