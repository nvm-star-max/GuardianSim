"""Simulator boundary for evaluating counterfactual action candidates."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from guardian_sim.models import ActionCandidate, CandidateMetrics


class CandidateEvaluator(Protocol):
    """Backend implemented by geometry, Genesis, or a learned risk model."""

    def evaluate(self, candidate: ActionCandidate) -> CandidateMetrics:
        """Evaluate one candidate without changing the real execution state."""


def evaluate_candidates(
    evaluator: CandidateEvaluator,
    candidates: Iterable[ActionCandidate],
) -> dict[str, CandidateMetrics]:
    """Evaluate candidates and reject duplicate identifiers."""

    metrics_by_id: dict[str, CandidateMetrics] = {}
    for candidate in candidates:
        if candidate.candidate_id in metrics_by_id:
            raise ValueError(f"duplicate candidate id: {candidate.candidate_id}")
        metrics_by_id[candidate.candidate_id] = evaluator.evaluate(candidate)
    return metrics_by_id
