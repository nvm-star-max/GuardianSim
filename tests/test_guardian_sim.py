from __future__ import annotations

import unittest

from guardian_sim.candidates import generate_grasp_candidates
from guardian_sim.failure import diagnose_outcome
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


if __name__ == "__main__":
    unittest.main()
