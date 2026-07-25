from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from guardian_sim.benchmark import BenchmarkEpisode, run_benchmark, summarize, write_report
from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.evaluator import evaluate_candidates
from guardian_sim.failure import diagnose_outcome
from guardian_sim.genesis_adapter import GenesisCandidateEvaluator, GenesisRolloutMeasurement
from guardian_sim.models import (
    CandidateMetrics,
    ClearanceDiagnostic,
    ExecutionOutcome,
    FailureType,
    RecoveryAction,
)
from guardian_sim.planner import execute_ranked_plan
from guardian_sim.reference_backend import (
    EntityPose,
    EpisodeSnapshot,
    GenesisSceneDriver,
    ReferenceSceneRolloutBackend,
)
from guardian_sim.reference_motion import candidate_grasp_pose
from guardian_sim.real_benchmark import (
    execution_succeeded,
    perturb_snapshot,
    summarize_real_benchmark,
    validate_resume_payload,
)
from guardian_sim.recovery import choose_recovery
from guardian_sim.rollout_metrics import (
    RolloutTrace,
    aabb_clearance,
    aabb_overlap_depth,
    measure_rollout,
)
from guardian_sim.robust_selection import select_robust_candidate
from guardian_sim.scoring import rank_candidates, score_candidate
from guardian_sim.serialization import json_default


class CandidateTests(unittest.TestCase):
    def test_default_candidate_matrix_contains_fifteen_actions(self) -> None:
        candidates = generate_grasp_candidates((0.5, 0.0, 0.04))

        self.assertEqual(len(candidates), 15)
        self.assertEqual(
            {candidate.lateral_offset_m for candidate in candidates},
            {-0.02, 0.0, 0.02},
        )

    def test_generates_cartesian_candidate_set(self) -> None:
        candidates = generate_grasp_candidates(
            (0.5, 0.0, 0.04),
            yaw_degrees=(-20.0, 0.0, 20.0),
            lateral_offsets_m=(-0.01, 0.01),
        )
        self.assertEqual(len(candidates), 6)
        self.assertEqual(len({candidate.candidate_id for candidate in candidates}), 6)


class ScoringTests(unittest.TestCase):
    def test_prefers_safe_stable_candidate(self) -> None:
        candidates = generate_grasp_candidates(
            (0.5, 0.0, 0.04),
            yaw_degrees=(0.0,),
            lateral_offsets_m=(-0.01, 0.01),
        )
        unsafe, safe = candidates
        metrics = {
            unsafe.candidate_id: CandidateMetrics(0.005, 1.0, 1.0, 0.40, 0.3, 0.05),
            safe.candidate_id: CandidateMetrics(0.09, 0.92, 0.92, 0.95, 0.5, 0.08),
        }
        ranked = rank_candidates(candidates, metrics)
        self.assertEqual(ranked[0].candidate, safe)
        self.assertLess(ranked[0].risk, ranked[1].risk)

    def test_support_contact_does_not_change_collision_risk(self) -> None:
        candidate = generate_grasp_candidates(
            (0.5, 0.0, 0.04),
            yaw_degrees=(0.0,),
            lateral_offsets_m=(0.0,),
        )[0]
        support_contact = ClearanceDiagnostic(
            sample_index=10,
            step_index=50,
            link_name="right_finger",
            obstacle_name="table_top",
            clearance_m=0.0,
            overlaps=True,
            overlap_depth_m=0.0015,
            support_surface=True,
        )
        without_contact = CandidateMetrics(0.08, 1.0, 1.0, 0.90, 0.4, 0.05)
        with_contact = CandidateMetrics(
            0.08,
            1.0,
            1.0,
            0.90,
            0.4,
            0.05,
            support_contact_diagnostic=support_contact,
        )

        self.assertEqual(
            score_candidate(candidate, without_contact).risk,
            score_candidate(candidate, with_contact).risk,
        )


class SerializationTests(unittest.TestCase):
    def test_serializes_numpy_scalars_and_arrays(self) -> None:
        class ScalarLike:
            def item(self) -> float:
                return 0.125

        class ArrayLike:
            def tolist(self) -> list[int]:
                return [1, 2]

        payload = {
            "scalar": ScalarLike(),
            "array": ArrayLike(),
        }

        rendered = json.dumps(payload, default=json_default)

        self.assertEqual(json.loads(rendered), {"scalar": 0.125, "array": [1, 2]})


class FailureTests(unittest.TestCase):
    def test_detects_slip_and_selects_recovery(self) -> None:
        diagnosis = diagnose_outcome(ExecutionOutcome(True, 0.08, 0.02, 3.0, 0.05))
        self.assertEqual(diagnosis.failure_type, FailureType.SLIP)
        self.assertEqual(choose_recovery(diagnosis, 1), RecoveryAction.WIDEN_GRIP)

    def test_stops_after_attempt_budget(self) -> None:
        diagnosis = diagnose_outcome(ExecutionOutcome(False, 0.0, 0.3, 2.0, 0.0))
        self.assertEqual(choose_recovery(diagnosis, 3, max_attempts=3), RecoveryAction.SAFE_STOP)


class PlannerTests(unittest.TestCase):
    def test_recovers_after_first_failure(self) -> None:
        candidates = generate_grasp_candidates(
            (0.5, 0.0, 0.04),
            yaw_degrees=(0.0,),
            lateral_offsets_m=(-0.01, 0.01),
        )
        metrics = {
            candidate.candidate_id: CandidateMetrics(0.08, 0.95, 0.95, 0.90, 0.4, 0.05)
            for candidate in candidates
        }
        outcomes = iter(
            [
                ExecutionOutcome(False, 0.0, 0.3, 2.0, 0.0),
                ExecutionOutcome(True, 0.08, 0.02, 3.0, 0.005),
            ]
        )
        result = execute_ranked_plan(candidates, metrics, lambda _: next(outcomes), max_attempts=2)
        self.assertTrue(result.succeeded)
        self.assertEqual(len(result.attempts), 2)
        self.assertEqual(result.attempts[0].recovery, RecoveryAction.CHANGE_GRASP_POSE)
        self.assertEqual(result.attempts[1].recovery, RecoveryAction.FINISH)


class EvaluatorTests(unittest.TestCase):
    def test_genesis_adapter_restores_state_for_every_candidate(self) -> None:
        clutter_diagnostic = ClearanceDiagnostic(
            sample_index=4,
            step_index=20,
            link_name="hand",
            obstacle_name="014_lemon",
            clearance_m=0.08,
            overlaps=False,
            overlap_depth_m=0.0,
            support_surface=False,
        )
        support_diagnostic = ClearanceDiagnostic(
            sample_index=5,
            step_index=25,
            link_name="right_finger",
            obstacle_name="table_top",
            clearance_m=0.0,
            overlaps=True,
            overlap_depth_m=0.0015,
            support_surface=True,
        )

        class FakeBackend:
            restores = 0

            def restore_reference_state(self) -> None:
                self.restores += 1

            def rollout(self, candidate):
                return GenesisRolloutMeasurement(
                    0.08,
                    True,
                    9.0,
                    0.09,
                    0.10,
                    0.4,
                    0.05,
                    clutter_diagnostic,
                    support_diagnostic,
                )

        backend = FakeBackend()
        candidates = generate_grasp_candidates(
            (0.5, 0.0, 0.04),
            yaw_degrees=(0.0,),
            lateral_offsets_m=(-0.01, 0.01),
        )
        metrics = evaluate_candidates(GenesisCandidateEvaluator(backend), candidates)
        self.assertEqual(backend.restores, 2)
        self.assertEqual(set(metrics), {candidate.candidate_id for candidate in candidates})
        self.assertAlmostEqual(next(iter(metrics.values())).predicted_stability, 0.9)
        self.assertEqual(
            next(iter(metrics.values())).clearance_diagnostic,
            clutter_diagnostic,
        )
        self.assertEqual(
            next(iter(metrics.values())).support_contact_diagnostic,
            support_diagnostic,
        )


class ReferenceBackendTests(unittest.TestCase):
    def test_restores_the_captured_episode_before_rollouts(self) -> None:
        initial = EpisodeSnapshot(
            seed=17,
            robot_qpos=(0.0, -0.7, 0.0, -2.2, 0.0, 1.5, 0.7, 0.04, 0.04),
            object_poses={
                "011_banana": EntityPose(
                    position=(0.31, 0.22, 0.77),
                    quaternion=(1.0, 0.0, 0.0, 0.0),
                )
            },
        )

        class FakeSceneDriver:
            state = initial

            def capture_snapshot(self) -> EpisodeSnapshot:
                return self.state

            def restore_snapshot(self, snapshot: EpisodeSnapshot) -> None:
                self.state = snapshot

            def rollout_candidate(self, candidate):
                return GenesisRolloutMeasurement(0.08, True, 9.0, 0.09, 0.10, 0.4, 0.05)

        driver = FakeSceneDriver()
        backend = ReferenceSceneRolloutBackend.from_current_state(driver)
        driver.state = EpisodeSnapshot(seed=99, robot_qpos=(1.0,), object_poses={})

        backend.restore_reference_state()

        self.assertEqual(driver.state, initial)

    def test_genesis_driver_round_trips_robot_and_object_state(self) -> None:
        class FakeEntity:
            def __init__(self, *, qpos=(), position=(), quaternion=()) -> None:
                self.qpos = tuple(qpos)
                self.position = tuple(position)
                self.quaternion = tuple(quaternion)

            def get_qpos(self):
                return self.qpos

            def get_pos(self):
                return self.position

            def get_quat(self):
                return self.quaternion

            def set_qpos(self, value, *, zero_velocity):
                self.qpos = tuple(value)

            def set_pos(self, value, *, zero_velocity):
                self.position = tuple(value)

            def set_quat(self, value, *, zero_velocity):
                self.quaternion = tuple(value)

        class FakeBundle:
            franka = FakeEntity(qpos=(0.0, -0.7, 0.04, 0.04))
            ycb = {
                "011_banana": FakeEntity(
                    position=(0.31, 0.22, 0.77),
                    quaternion=(1.0, 0.0, 0.0, 0.0),
                )
            }

        bundle = FakeBundle()
        driver = GenesisSceneDriver(bundle, seed=23)
        snapshot = driver.capture_snapshot()
        bundle.franka.qpos = (9.0,)
        bundle.ycb["011_banana"].position = (8.0, 8.0, 8.0)

        driver.restore_snapshot(snapshot)

        self.assertEqual(bundle.franka.qpos, snapshot.robot_qpos)
        self.assertEqual(
            bundle.ycb["011_banana"].position,
            snapshot.object_poses["011_banana"].position,
        )
        self.assertEqual(
            bundle.ycb["011_banana"].quaternion,
            snapshot.object_poses["011_banana"].quaternion,
        )

    def test_snapshot_fingerprint_is_stable_across_object_mapping_order(self) -> None:
        banana = EntityPose((0.31, 0.22, 0.77), (1.0, 0.0, 0.0, 0.0))
        bowl = EntityPose((0.50, -0.10, 0.78), (1.0, 0.0, 0.0, 0.0))
        first = EpisodeSnapshot(
            seed=31,
            robot_qpos=(0.0, -0.7, 0.04, 0.04),
            object_poses={"011_banana": banana, "024_bowl": bowl},
        )
        reordered = EpisodeSnapshot(
            seed=31,
            robot_qpos=(0.0, -0.7, 0.04, 0.04),
            object_poses={"024_bowl": bowl, "011_banana": banana},
        )
        changed = EpisodeSnapshot(
            seed=31,
            robot_qpos=(0.0, -0.7, 0.04, 0.04),
            object_poses={
                "011_banana": EntityPose((0.32, 0.22, 0.77), banana.quaternion),
                "024_bowl": bowl,
            },
        )

        self.assertEqual(first.fingerprint(), reordered.fingerprint())
        self.assertNotEqual(first.fingerprint(), changed.fingerprint())


class RolloutMeasurementTests(unittest.TestCase):
    def test_converts_sampled_motion_into_physical_candidate_measurements(self) -> None:
        trace = RolloutTrace(
            minimum_clearance_m=0.032,
            reachable=True,
            alignment_error_degrees=12.0,
            object_start_height_m=0.77,
            object_retained_height_m=0.855,
            requested_lift_height_m=0.10,
            end_effector_positions=(
                (0.30, 0.20, 0.90),
                (0.30, 0.20, 0.80),
                (0.30, 0.20, 0.90),
                (0.50, -0.10, 0.90),
            ),
            perception_uncertainty=0.07,
        )

        measurement = measure_rollout(trace)

        self.assertAlmostEqual(measurement.retained_lift_height_m, 0.085)
        self.assertAlmostEqual(measurement.path_length_m, 0.5605551275)
        self.assertEqual(measurement.minimum_clearance_m, 0.032)
        self.assertTrue(measurement.reachable)

    def test_measures_clearance_between_collision_bounds(self) -> None:
        hand = ((0.00, 0.00, 0.80), (0.10, 0.10, 0.90))
        obstacle = ((0.13, 0.14, 0.80), (0.20, 0.20, 0.90))
        overlapping = ((0.05, 0.05, 0.85), (0.15, 0.15, 0.95))

        self.assertAlmostEqual(aabb_clearance(hand, obstacle), 0.05)
        self.assertEqual(aabb_clearance(hand, overlapping), 0.0)
        self.assertAlmostEqual(aabb_overlap_depth(hand, overlapping), 0.05)
        self.assertEqual(aabb_overlap_depth(hand, obstacle), 0.0)

    def test_touching_aabbs_are_not_classified_as_overlapping(self) -> None:
        hand = ((0.00, 0.00, 0.80), (0.10, 0.10, 0.90))
        touching = ((0.10, 0.00, 0.80), (0.20, 0.10, 0.90))

        self.assertEqual(aabb_clearance(hand, touching), 0.0)
        self.assertEqual(aabb_overlap_depth(hand, touching), 0.0)

    def test_maps_candidate_offset_into_the_gripper_lateral_axis(self) -> None:
        candidate = generate_grasp_candidates(
            (0.50, 0.10, 0.77),
            yaw_degrees=(90.0,),
            lateral_offsets_m=(0.02,),
        )[0]

        position, yaw_degrees = candidate_grasp_pose(candidate, object_yaw_degrees=0.0)

        self.assertAlmostEqual(position[0], 0.48)
        self.assertAlmostEqual(position[1], 0.10)
        self.assertAlmostEqual(position[2], 0.77)
        self.assertEqual(yaw_degrees, 90.0)


class BenchmarkTests(unittest.TestCase):
    def test_fixed_seed_snapshot_jitter_is_deterministic(self) -> None:
        snapshot = EpisodeSnapshot(
            seed=1,
            robot_qpos=(0.0, 1.0),
            object_poses={
                "011_banana": EntityPose(
                    position=(0.31, 0.22, 0.77),
                    quaternion=(1.0, 0.0, 0.0, 0.0),
                )
            },
        )

        first = perturb_snapshot(snapshot, seed=101, xy_jitter_m=0.015)
        repeated = perturb_snapshot(snapshot, seed=101, xy_jitter_m=0.015)
        changed = perturb_snapshot(snapshot, seed=102, xy_jitter_m=0.015)

        self.assertEqual(first, repeated)
        self.assertNotEqual(first.object_poses, changed.object_poses)
        self.assertEqual(first.robot_qpos, snapshot.robot_qpos)

    def test_real_execution_requires_lift_and_no_clutter_overlap(self) -> None:
        safe = CandidateMetrics(0.06, 1.0, 1.0, 0.75, 0.4, 0.05)
        dropped = CandidateMetrics(0.06, 1.0, 1.0, 0.0, 0.4, 0.05)
        collision = CandidateMetrics(
            0.0,
            1.0,
            1.0,
            0.90,
            0.4,
            0.05,
            clearance_diagnostic=ClearanceDiagnostic(
                sample_index=1,
                step_index=5,
                link_name="hand",
                obstacle_name="018_plum",
                clearance_m=0.0,
                overlaps=True,
                overlap_depth_m=0.002,
                support_surface=False,
            ),
        )

        self.assertTrue(execution_succeeded(safe))
        self.assertFalse(execution_succeeded(dropped))
        self.assertFalse(execution_succeeded(collision))

    def test_summarizes_independent_execution_results(self) -> None:
        candidate = {"candidate_id": "yaw_+00.0_offset_+0.000"}
        metrics = {"predicted_stability": 0.8, "collision_margin_m": 0.05}
        episodes = [
            {
                "baseline": {
                    "candidate": candidate,
                    "execution_metrics": metrics,
                    "succeeded": False,
                },
                "guardiansim": {
                    "candidate": candidate,
                    "execution_metrics": metrics,
                    "succeeded": True,
                },
            },
            {
                "baseline": {
                    "candidate": candidate,
                    "execution_metrics": metrics,
                    "succeeded": True,
                },
                "guardiansim": {
                    "candidate": candidate,
                    "execution_metrics": metrics,
                    "succeeded": True,
                },
            },
        ]

        summary = summarize_real_benchmark(episodes)

        self.assertEqual(summary["baseline"]["success_rate"], 0.5)
        self.assertEqual(summary["guardiansim"]["success_rate"], 1.0)
        self.assertEqual(summary["absolute_success_rate_lift"], 0.5)

    def test_resume_requires_compatible_contiguous_episode_prefix(self) -> None:
        configuration = {
            "schema_version": 2,
            "pick_object": "011_banana",
            "base_snapshot_fingerprint": "abc123",
        }
        payload = {
            **configuration,
            "episodes": [{"seed": 101}, {"seed": 102}],
        }

        resumed = validate_resume_payload(
            payload,
            expected_configuration=configuration,
            requested_episode_count=20,
            seed_start=101,
        )

        self.assertEqual(resumed, payload["episodes"])
        with self.assertRaisesRegex(ValueError, "contiguous seed prefix"):
            validate_resume_payload(
                {**configuration, "episodes": [{"seed": 102}]},
                expected_configuration=configuration,
                requested_episode_count=20,
                seed_start=101,
            )
        with self.assertRaisesRegex(ValueError, "configuration does not match"):
            validate_resume_payload(
                {**payload, "pick_object": "014_lemon"},
                expected_configuration=configuration,
                requested_episode_count=20,
                seed_start=101,
            )

    def test_guardian_recovers_when_baseline_candidate_fails(self) -> None:
        candidates = tuple(
            generate_grasp_candidates(
                (0.5, 0.0, 0.04),
                yaw_degrees=(0.0,),
                lateral_offsets_m=(-0.01, 0.01),
            )
        )
        first, second = candidates
        metrics = {
            first.candidate_id: CandidateMetrics(0.01, 0.8, 0.7, 0.4, 0.5, 0.2),
            second.candidate_id: CandidateMetrics(0.09, 0.95, 0.95, 0.95, 0.4, 0.05),
        }
        outcomes = {
            first.candidate_id: ExecutionOutcome(False, 0.0, 0.3, 2.0, 0.0, collision=True),
            second.candidate_id: ExecutionOutcome(True, 0.08, 0.02, 3.0, 0.005),
        }
        rows = run_benchmark([BenchmarkEpisode("episode-1", candidates, metrics, outcomes)])
        summary = summarize(rows)
        self.assertEqual(summary["baseline_first_candidate"]["success_rate"], 0.0)
        self.assertEqual(summary["guardiansim"]["success_rate"], 1.0)

        with TemporaryDirectory() as directory:
            csv_path, json_path = write_report(rows, directory, metadata={"data_source": "unit_test"})
            self.assertTrue(Path(csv_path).read_text(encoding="utf-8").startswith("episode_id,strategy"))
            self.assertIn('"data_source": "unit_test"', Path(json_path).read_text(encoding="utf-8"))


class RobustSelectionTests(unittest.TestCase):
    def test_lucky_high_clearance_candidate_cannot_beat_repeatable_stable_candidate(self) -> None:
        candidates = tuple(
            generate_grasp_candidates(
                (0.5, 0.0, 0.77),
                yaw_degrees=(-22.5, 0.0),
                lateral_offsets_m=(-0.02, 0.0),
            )
        )
        lucky = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == "yaw_-22.5_offset_-0.020"
        )
        nominal = next(
            candidate
            for candidate in candidates
            if candidate.candidate_id == "yaw_+00.0_offset_+0.000"
        )
        initial = {
            candidate.candidate_id: CandidateMetrics(
                0.09 if candidate is lucky else 0.045,
                1.0,
                0.95,
                0.95 if candidate is lucky else 0.90,
                0.4,
                0.05,
            )
            for candidate in candidates
        }

        class ConfirmationEvaluator:
            calls = 0

            def evaluate(self, candidate):
                self.calls += 1
                if candidate is lucky:
                    stability = 0.0 if self.calls % 2 else 0.95
                    return CandidateMetrics(0.09, 1.0, 0.95, stability, 0.4, 0.05)
                return CandidateMetrics(0.045, 1.0, 0.95, 0.90, 0.4, 0.05)

        result = select_robust_candidate(
            candidates,
            initial,
            ConfirmationEvaluator(),
            nominal_candidate_id=nominal.candidate_id,
            shortlist_size=4,
            confirmation_rollouts=2,
            minimum_stability=0.60,
        )

        self.assertNotEqual(result.selected.candidate, lucky)
        self.assertGreaterEqual(result.selected.metrics.predicted_stability, 0.60)

    def test_falls_back_to_nominal_without_a_repeatable_success_margin(self) -> None:
        candidates = tuple(
            generate_grasp_candidates(
                (0.5, 0.0, 0.77),
                yaw_degrees=(-22.5, 0.0),
                lateral_offsets_m=(0.0,),
            )
        )
        alternative, nominal = candidates
        nominal_metrics = CandidateMetrics(0.05, 1.0, 0.95, 0.90, 0.4, 0.05)
        alternative_metrics = CandidateMetrics(0.052, 1.0, 0.95, 0.90, 0.4, 0.05)
        initial = {
            alternative.candidate_id: alternative_metrics,
            nominal.candidate_id: nominal_metrics,
        }

        class StableEvaluator:
            def evaluate(self, candidate):
                return initial[candidate.candidate_id]

        result = select_robust_candidate(
            candidates,
            initial,
            StableEvaluator(),
            nominal_candidate_id=nominal.candidate_id,
            shortlist_size=2,
            confirmation_rollouts=2,
            minimum_success_margin=0.02,
        )

        self.assertEqual(result.selected.candidate, nominal)
        self.assertTrue(result.fallback_used)

    def test_selects_alternative_that_repeatedly_clears_the_success_margin(self) -> None:
        candidates = tuple(
            generate_grasp_candidates(
                (0.5, 0.0, 0.77),
                yaw_degrees=(-22.5, 0.0),
                lateral_offsets_m=(0.0,),
            )
        )
        alternative, nominal = candidates
        observations = {
            alternative.candidate_id: CandidateMetrics(
                0.08, 1.0, 0.95, 0.92, 0.4, 0.05
            ),
            nominal.candidate_id: CandidateMetrics(
                0.04, 1.0, 0.95, 0.90, 0.4, 0.05
            ),
        }

        class RepeatableEvaluator:
            def evaluate(self, candidate):
                return observations[candidate.candidate_id]

        result = select_robust_candidate(
            candidates,
            observations,
            RepeatableEvaluator(),
            nominal_candidate_id=nominal.candidate_id,
            shortlist_size=2,
            confirmation_rollouts=2,
            minimum_success_margin=0.02,
        )

        self.assertEqual(result.selected.candidate, alternative)
        self.assertFalse(result.fallback_used)
        self.assertEqual(len(result.observations_by_id[alternative.candidate_id]), 3)


if __name__ == "__main__":
    unittest.main()
