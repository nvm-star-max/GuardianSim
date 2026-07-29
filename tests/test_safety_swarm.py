from __future__ import annotations

import copy
import unittest
from collections import Counter

from guardian_sim.safety_swarm import (
    SAFETY_SWARM_WORLD_COUNT,
    SafetySwarmMeasurement,
    assemble_safety_swarm_smoke_report,
    assemble_safety_swarm_report,
    build_offline_fixture_measurements,
    build_safety_swarm_matrix,
    build_safety_swarm_protocol,
    build_safety_swarm_smoke_protocol,
    classify_safety_swarm_world,
    safety_swarm_matrix_sha256,
    safety_swarm_smoke_world_ids,
    validate_safety_swarm_report,
    validate_safety_swarm_smoke_report,
    wilson_lower_bound,
)
from guardian_sim.safety_swarm_genesis import (
    build_safety_swarm_placements,
    delayed_trajectory_alphas,
)


class SafetySwarmTests(unittest.TestCase):
    def _safe_measurements(self) -> list[SafetySwarmMeasurement]:
        return [
            SafetySwarmMeasurement(
                world_id=world.world_id,
                minimum_clearance_m=0.020,
                stability=0.90,
                reachable=True,
                task_completed=True,
                clutter_contact=False,
                elapsed_environment_steps=640,
            )
            for world in build_safety_swarm_matrix()
        ]

    def _formal_report(self) -> dict[str, object]:
        return assemble_safety_swarm_report(
            self._safe_measurements(),
            candidate_id="yaw_+67.5_offset_+0.140",
            wall_seconds=8.0,
            mode="radeon_formal",
            backend="genesis_gpu_batched",
            source_commit="a" * 40,
            device={
                "name": "AMD Radeon PRO W7900",
                "hip_version": "7.2",
            },
            gpu_telemetry={"sample_count": 4},
        )

    def test_matrix_is_complete_unique_balanced_and_hashed(self) -> None:
        matrix = build_safety_swarm_matrix()
        self.assertEqual(len(matrix), SAFETY_SWARM_WORLD_COUNT)
        self.assertEqual([world.world_id for world in matrix], list(range(256)))
        self.assertEqual(
            {(world.row, world.column) for world in matrix},
            {(row, column) for row in range(16) for column in range(16)},
        )
        for attribute in (
            "target_pose_level",
            "clutter_geometry_level",
            "end_effector_bias_level",
            "action_delay_level",
        ):
            self.assertEqual(
                Counter(getattr(world, attribute) for world in matrix),
                Counter({0: 64, 1: 64, 2: 64, 3: 64}),
            )
        protocol = build_safety_swarm_protocol()
        self.assertEqual(protocol["matrix_sha256"], safety_swarm_matrix_sha256())
        self.assertEqual(len(protocol["protocol_sha256"]), 64)

    def test_typed_costs_explain_every_failed_gate(self) -> None:
        world = build_safety_swarm_matrix()[0]
        result = classify_safety_swarm_world(
            world,
            SafetySwarmMeasurement(
                world_id=0,
                minimum_clearance_m=0.004,
                stability=0.60,
                reachable=False,
                task_completed=False,
                clutter_contact=True,
                elapsed_environment_steps=620,
            ),
        )
        self.assertFalse(result["hard_safe"])
        self.assertEqual(result["primary_stop_reason"], "clutter_contact")
        self.assertEqual(
            result["failed_gates"],
            [
                "clutter_contact",
                "unreachable",
                "clearance_below_minimum",
                "stability_below_minimum",
                "task_failure",
            ],
        )
        self.assertEqual(result["costs"]["contact"], 1)
        self.assertAlmostEqual(result["costs"]["clearance_m"], 0.006)
        self.assertAlmostEqual(result["costs"]["stability"], 0.10)
        self.assertEqual(result["costs"]["task_failure"], 1)

    def test_formal_report_recomputes_summary_and_passes_strict_validation(
        self,
    ) -> None:
        report = self._formal_report()
        validated = validate_safety_swarm_report(report, require_radeon=True)
        self.assertEqual(validated["status"], "passed")
        self.assertEqual(validated["world_count"], 256)
        self.assertEqual(validated["decision"], "execute")
        self.assertEqual(validated["safe_world_count"], 256)
        self.assertTrue(validated["showcase_ready"])
        self.assertAlmostEqual(
            report["summary"]["environment_steps_per_second"],
            20_480.0,
        )
        self.assertGreater(wilson_lower_bound(256, 256), 0.98)

    def test_validator_rejects_matrix_label_summary_and_hash_tampering(
        self,
    ) -> None:
        report = self._formal_report()

        matrix_tampered = copy.deepcopy(report)
        matrix_tampered["results"][0]["perturbation"]["target_dx_m"] = 99.0
        with self.assertRaisesRegex(ValueError, "matrix drift"):
            validate_safety_swarm_report(matrix_tampered)

        label_tampered = copy.deepcopy(report)
        label_tampered["results"][0]["hard_safe"] = False
        with self.assertRaisesRegex(ValueError, "label or cost drift"):
            validate_safety_swarm_report(label_tampered)

        summary_tampered = copy.deepcopy(report)
        summary_tampered["summary"]["safe_world_count"] = 255
        with self.assertRaisesRegex(ValueError, "safe_world_count"):
            validate_safety_swarm_report(summary_tampered)

        hash_tampered = copy.deepcopy(report)
        hash_tampered["source"]["candidate_id"] = "changed"
        with self.assertRaisesRegex(ValueError, "report hash"):
            validate_safety_swarm_report(hash_tampered)

    def test_offline_fixture_is_explicitly_not_radeon_evidence(self) -> None:
        report = assemble_safety_swarm_report(
            build_offline_fixture_measurements(),
            candidate_id="ui-fixture-candidate",
            wall_seconds=1.0,
            mode="offline_fixture",
            backend="deterministic_fixture",
            source_commit="fixture",
        )
        validated = validate_safety_swarm_report(report)
        self.assertEqual(validated["status"], "passed")
        self.assertFalse(validated["showcase_ready"])
        self.assertEqual(report["evidence_status"], "ui_validation_only")
        self.assertEqual(report["summary"]["decision"], "safe_stop")
        with self.assertRaisesRegex(ValueError, "requires a Radeon formal"):
            validate_safety_swarm_report(report, require_radeon=True)

    def test_smoke_subsets_are_predeclared_balanced_and_formally_isolated(
        self,
    ) -> None:
        self.assertEqual(safety_swarm_smoke_world_ids(4), (0, 85, 170, 255))
        matrix = build_safety_swarm_matrix()
        for count in (4, 16):
            selected = [matrix[index] for index in safety_swarm_smoke_world_ids(count)]
            for attribute in (
                "target_pose_level",
                "clutter_geometry_level",
                "end_effector_bias_level",
                "action_delay_level",
            ):
                self.assertEqual(
                    Counter(getattr(world, attribute) for world in selected),
                    Counter({level: count // 4 for level in range(4)}),
                )
            smoke = build_safety_swarm_smoke_protocol(count)
            formal = build_safety_swarm_protocol()
            self.assertEqual(
                smoke["formal_protocol_sha256"],
                formal["protocol_sha256"],
            )
            self.assertEqual(smoke["formal_matrix_sha256"], formal["matrix_sha256"])
            self.assertNotEqual(smoke["report_name"], formal["report_name"])

    def test_smoke_report_passes_strict_validation_but_is_not_showcase_ready(
        self,
    ) -> None:
        world_ids = safety_swarm_smoke_world_ids(4)
        report = assemble_safety_swarm_smoke_report(
            [
                SafetySwarmMeasurement(
                    world_id=world_id,
                    minimum_clearance_m=0.02,
                    stability=0.9,
                    reachable=True,
                    task_completed=True,
                    clutter_contact=False,
                    elapsed_environment_steps=644,
                )
                for world_id in world_ids
            ],
            candidate_id="yaw_+67.5_retreat_+0.025_approach_+0.140",
            wall_seconds=2.0,
            source_commit="b" * 40,
            backend="genesis_gpu_batched",
            device={"name": "AMD Radeon Graphics", "hip_version": "7.2"},
            gpu_telemetry={"sample_count": 2},
        )
        validation = validate_safety_swarm_smoke_report(
            report,
            require_radeon=True,
        )
        self.assertEqual(validation["status"], "passed")
        self.assertEqual(validation["world_count"], 4)
        self.assertEqual(validation["smoke_status"], "passed")
        self.assertFalse(validation["showcase_ready"])

        tampered = copy.deepcopy(report)
        tampered["results"][0]["perturbation"]["target_dx_m"] = 2.0
        with self.assertRaisesRegex(ValueError, "matrix drift"):
            validate_safety_swarm_smoke_report(tampered)

    def test_scene_placements_and_delays_are_per_world(self) -> None:
        matrix = build_safety_swarm_matrix()
        worlds = [matrix[index] for index in safety_swarm_smoke_world_ids(4)]
        placements = build_safety_swarm_placements(
            worlds,
            base_target_xyz=(0.31, 0.22, 0.78),
            target_radius_xy_m=0.04,
            obstacle_radius_xy_m=0.03,
            obstacle_z_m=0.77,
        )
        self.assertEqual([value.world_id for value in placements], [0, 85, 170, 255])
        self.assertEqual(
            [value.action_start_delay_steps for value in placements],
            [0, 1, 2, 4],
        )
        for world, placement in zip(worlds, placements, strict=True):
            separation = (
                (placement.obstacle_xyz[0] - placement.target_xyz[0]) ** 2
                + (placement.obstacle_xyz[1] - placement.target_xyz[1]) ** 2
            ) ** 0.5
            self.assertAlmostEqual(
                separation,
                0.04 + 0.03 + 0.012 + world.clutter_gap_delta_m,
            )

        self.assertEqual(
            delayed_trajectory_alphas(
                [0, 1, 2, 4],
                step_index=1,
                trajectory_steps=4,
            ),
            (0.25, 0.0, 0.0, 0.0),
        )
        self.assertEqual(
            delayed_trajectory_alphas(
                [0, 1, 2, 4],
                step_index=8,
                trajectory_steps=4,
            ),
            (1.0, 1.0, 1.0, 1.0),
        )


if __name__ == "__main__":
    unittest.main()
