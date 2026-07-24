from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from guardian_sim.benchmark import BenchmarkEpisode, run_benchmark, summarize, write_report
from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.evaluator import evaluate_candidates
from guardian_sim.failure import diagnose_outcome
from guardian_sim.genesis_adapter import GenesisCandidateEvaluator, GenesisRolloutMeasurement
from guardian_sim.models import CandidateMetrics, ExecutionOutcome, FailureType, RecoveryAction
from guardian_sim.planner import execute_ranked_plan
from guardian_sim.recovery import choose_recovery
from guardian_sim.scoring import rank_candidates


class CandidateTests(unittest.TestCase):
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
        class FakeBackend:
            restores = 0

            def restore_reference_state(self) -> None:
                self.restores += 1

            def rollout(self, candidate):
                return GenesisRolloutMeasurement(0.08, True, 9.0, 0.09, 0.10, 0.4, 0.05)

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


class BenchmarkTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
