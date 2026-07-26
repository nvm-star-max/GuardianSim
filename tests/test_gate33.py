from __future__ import annotations

import json
import math
import unittest
from dataclasses import asdict
from itertools import combinations

from guardian_sim.adversarial_benchmark import (
    PRIMARY_OBSTACLE_BY_PICK,
    classify_gate31_execution,
)
from guardian_sim.gate33_benchmark import (
    GATE33_PERTURBATION_STRATA,
    apply_gate33_scenario,
    certify_candidate_metrics,
    gate33_protocol_payload,
    gate33_scenario_asdict,
    gate33_stop_reasons,
    generate_gate33_candidates,
    generate_gate33_scenarios,
    perceived_positions,
    summarize_gate33,
    validate_gate33_payload,
)
from guardian_sim.models import CandidateMetrics, ClearanceDiagnostic
from guardian_sim.reference_backend import EntityPose, EpisodeSnapshot


class Gate33Tests(unittest.TestCase):
    @staticmethod
    def _base_snapshot() -> EpisodeSnapshot:
        pose = EntityPose(
            position=(0.50, 0.0, 0.77),
            quaternion=(1.0, 0.0, 0.0, 0.0),
        )
        return EpisodeSnapshot(
            seed=0,
            robot_qpos=(0.0,) * 9,
            object_poses={
                "011_banana": pose,
                "014_lemon": pose,
                "018_plum": pose,
                "024_bowl": pose,
            },
        )

    @staticmethod
    def _radii() -> dict[str, float]:
        return {
            "011_banana": 0.1054,
            "014_lemon": 0.0428,
            "018_plum": 0.0392,
            "024_bowl": 0.1148,
        }

    def test_protocol_balances_four_strata_on_unseen_seeds(self) -> None:
        scenarios = generate_gate33_scenarios()
        protocol = gate33_protocol_payload()

        self.assertEqual(len(scenarios), 24)
        self.assertEqual([item.seed for item in scenarios], list(range(501, 525)))
        self.assertEqual(
            {item.stratum for item in scenarios},
            set(GATE33_PERTURBATION_STRATA),
        )
        for stratum in GATE33_PERTURBATION_STRATA:
            group = [item for item in scenarios if item.stratum == stratum]
            self.assertEqual(len(group), 6)
            self.assertEqual(
                {(item.pick_object, item.layout) for item in group},
                {
                    (pick, layout)
                    for pick in ("011_banana", "014_lemon", "018_plum")
                    for layout in ("lateral_clutter", "radial_clutter")
                },
            )
        self.assertEqual(protocol["status"], "engineering_smoke_not_formal_performance_evidence")
        self.assertEqual(protocol["scenario_count"], 24)
        self.assertEqual(len(protocol["scenario_matrix_sha256"]), 64)
        self.assertEqual(len(protocol["protocol_sha256"]), 64)

    def test_changed_bearing_preserves_declared_gap(self) -> None:
        scenario = next(
            item
            for item in generate_gate33_scenarios()
            if item.stratum == "gap_bearing"
        )
        challenged = apply_gate33_scenario(
            self._base_snapshot(),
            scenario,
            footprint_radii_m=self._radii(),
        )
        target = challenged.object_poses[scenario.pick_object].position
        obstacle_name = PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object]
        obstacle = challenged.object_poses[obstacle_name].position
        separation = math.hypot(
            target[0] - obstacle[0],
            target[1] - obstacle[1],
        )

        self.assertAlmostEqual(
            separation,
            self._radii()[scenario.pick_object]
            + self._radii()[obstacle_name]
            + scenario.clutter_gap_m,
        )
        self.assertNotEqual(scenario.obstacle_bearing_offset_deg, 0.0)

    def test_every_physical_scenario_starts_without_footprint_overlap(
        self,
    ) -> None:
        radii = self._radii()
        for scenario in generate_gate33_scenarios():
            challenged = apply_gate33_scenario(
                self._base_snapshot(),
                scenario,
                footprint_radii_m=radii,
            )
            for left_name, right_name in combinations(radii, 2):
                left = challenged.object_poses[left_name].position
                right = challenged.object_poses[right_name].position
                center_distance = math.hypot(
                    left[0] - right[0],
                    left[1] - right[1],
                )
                self.assertGreaterEqual(
                    center_distance + 1e-12,
                    radii[left_name] + radii[right_name],
                    msg=(
                        f"{scenario.scenario_id} overlaps "
                        f"{left_name}/{right_name}"
                    ),
                )

    def test_perception_bias_changes_planning_pose_but_not_true_scene(self) -> None:
        scenario = next(
            item
            for item in generate_gate33_scenarios()
            if item.stratum == "perception_bias"
        )
        true_target = (0.50, 0.0, 0.77)
        true_obstacle = (0.50, 0.10, 0.77)
        perceived_target, perceived_obstacle = perceived_positions(
            scenario,
            true_target,
            true_obstacle,
        )
        candidates = generate_gate33_candidates(
            scenario,
            true_target,
            true_obstacle,
        )

        self.assertNotEqual(perceived_target, true_target)
        self.assertNotEqual(perceived_obstacle, true_obstacle)
        self.assertEqual(len(candidates), 18)
        self.assertTrue(
            all(item.target_xyz == perceived_target for item in candidates)
        )

    def test_certificate_subtracts_relative_uncertainty_and_explains_failure(
        self,
    ) -> None:
        metrics = CandidateMetrics(
            collision_margin_m=0.020,
            reachability=1.0,
            grasp_alignment=0.95,
            predicted_stability=0.85,
            path_length_m=0.4,
            perception_uncertainty=0.02,
        )
        certified, certificate = certify_candidate_metrics(
            metrics,
            relative_position_uncertainty_bound_m=0.012,
        )

        self.assertAlmostEqual(certified.collision_margin_m, 0.008)
        self.assertAlmostEqual(
            certificate.certified_clearance_lower_bound_m,
            0.008,
        )
        self.assertFalse(certificate.hard_safe)
        self.assertEqual(
            certificate.failed_gates,
            ("certified_clearance_below_minimum",),
        )

    def test_validator_accepts_partial_report_and_rejects_certificate_drift(
        self,
    ) -> None:
        scenario = generate_gate33_scenarios()[0]
        candidates = generate_gate33_candidates(
            scenario,
            (0.50, 0.0, 0.77),
            (0.50, 0.10, 0.77),
        )
        safe_metrics = CandidateMetrics(
            0.030,
            1.0,
            0.95,
            0.85,
            0.4,
            0.05,
            clearance_diagnostic=ClearanceDiagnostic(
                sample_index=2,
                step_index=10,
                link_name="hand",
                obstacle_name="018_plum",
                clearance_m=0.030,
                overlaps=False,
                overlap_depth_m=0.0,
                support_surface=False,
            ),
        )
        certified, certificate = certify_candidate_metrics(
            safe_metrics,
            relative_position_uncertainty_bound_m=(
                scenario.relative_position_uncertainty_bound_m
            ),
        )
        raw_by_id = {
            item.candidate_id: asdict(safe_metrics) for item in candidates
        }
        certified_by_id = {
            item.candidate_id: asdict(certified) for item in candidates
        }
        certificates_by_id = {
            item.candidate_id: asdict(certificate) for item in candidates
        }
        nominal = next(
            item
            for item in candidates
            if item.candidate_id == "yaw_+00.0_offset_+0.000"
        )
        classification = classify_gate31_execution(
            safe_metrics,
            minimum_stability=0.70,
            minimum_safe_clearance_m=0.010,
        )
        execution = {
            "execution_metrics": asdict(safe_metrics),
            "classification": asdict(classification),
        }
        strategy = {
            "candidate": asdict(nominal),
            "safe_stopped": False,
            "execution": execution,
        }
        episode = {
            "episode_index": 0,
            "seed": scenario.seed,
            "scenario_id": scenario.scenario_id,
            "stratum": scenario.stratum,
            "pick_object": scenario.pick_object,
            "layout": scenario.layout,
            "primary_obstacle": PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object],
            "scenario": gate33_scenario_asdict(scenario),
            "snapshot_fingerprint": "gate33-fingerprint",
            "target_xyz": [0.50, 0.0, 0.77],
            "obstacle_xyz": [0.50, 0.10, 0.77],
            "perceived_target_xyz": [0.50, 0.0, 0.77],
            "perceived_obstacle_xyz": [0.50, 0.10, 0.77],
            "relative_position_uncertainty_bound_m": (
                scenario.relative_position_uncertainty_bound_m
            ),
            "timing": {
                "planning_wall_seconds": 1.0,
                "baseline_execution_wall_seconds": 1.0,
                "guardiansim_execution_wall_seconds": 1.0,
            },
            "selection": {
                "decision": "eligible_nominal_fallback",
                "selected_candidate_id": nominal.candidate_id,
                "initial_raw_metrics_by_id": raw_by_id,
                "initial_certified_metrics_by_id": certified_by_id,
                "initial_risk_certificates_by_id": certificates_by_id,
                "confirmed_candidate_ids": [nominal.candidate_id],
                "observations_by_id": {
                    nominal.candidate_id: [
                        certified_by_id[nominal.candidate_id]
                    ]
                    * 4
                },
            },
            "baseline": strategy,
            "guardiansim": strategy,
        }
        payload = {
            "schema_version": 6,
            "protocol": gate33_protocol_payload(),
            "requested_episode_count": 24,
            "completed_episode_count": 1,
            "seed_start": 501,
            "episodes": [episode],
            "stop_reasons": [],
            "summary": summarize_gate33([episode]),
        }
        round_tripped = json.loads(json.dumps(payload))

        self.assertEqual(
            validate_gate33_payload(round_tripped, require_complete=False),
            round_tripped["episodes"],
        )
        drifted = json.loads(json.dumps(round_tripped))
        first = next(
            iter(
                drifted["episodes"][0]["selection"][
                    "initial_certified_metrics_by_id"
                ]
            )
        )
        drifted["episodes"][0]["selection"][
            "initial_certified_metrics_by_id"
        ][first]["collision_margin_m"] = 0.5
        with self.assertRaisesRegex(ValueError, "certificate/metric mismatch"):
            validate_gate33_payload(drifted, require_complete=False)

    def test_stop_rules_only_evaluate_after_complete_stratum(self) -> None:
        failed = {
            "baseline": {
                "safe_stopped": False,
                "execution": {
                    "classification": {
                        "task_succeeded": True,
                        "clutter_contact": False,
                    }
                },
            },
            "guardiansim": {
                "safe_stopped": True,
                "execution": None,
            },
        }

        self.assertEqual(gate33_stop_reasons([failed] * 5), ())
        self.assertEqual(
            gate33_stop_reasons([failed] * 6),
            (
                "guardian_task_failure_rate_above_0.25",
                "no_hard_safe_candidate_rate_above_0.20",
            ),
        )


if __name__ == "__main__":
    unittest.main()
