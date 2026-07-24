"""Counterfactual planning loop independent of a specific simulator."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from guardian_sim.failure import diagnose_outcome
from guardian_sim.models import (
    ActionCandidate,
    CandidateMetrics,
    CandidateScore,
    ExecutionOutcome,
    FailureDiagnosis,
    RecoveryAction,
)
from guardian_sim.recovery import choose_recovery
from guardian_sim.scoring import rank_candidates


@dataclass(frozen=True, slots=True)
class AttemptTrace:
    attempt_number: int
    score: CandidateScore
    outcome: ExecutionOutcome
    diagnosis: FailureDiagnosis
    recovery: RecoveryAction


@dataclass(frozen=True, slots=True)
class PlanResult:
    succeeded: bool
    attempts: tuple[AttemptTrace, ...]


def execute_ranked_plan(
    candidates: Sequence[ActionCandidate],
    metrics_by_id: Mapping[str, CandidateMetrics],
    executor: Callable[[ActionCandidate], ExecutionOutcome],
    *,
    max_attempts: int = 3,
) -> PlanResult:
    """Execute the safest unused candidates until success or a bounded stop."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")

    ranked = rank_candidates(candidates, metrics_by_id)
    traces: list[AttemptTrace] = []
    for attempt_number, score in enumerate(ranked[:max_attempts], start=1):
        outcome = executor(score.candidate)
        diagnosis = diagnose_outcome(outcome)
        recovery = choose_recovery(diagnosis, attempt_number, max_attempts=max_attempts)
        traces.append(AttemptTrace(attempt_number, score, outcome, diagnosis, recovery))
        if diagnosis.succeeded:
            return PlanResult(True, tuple(traces))
    return PlanResult(False, tuple(traces))
