"""Repeatability-aware selection for counterfactual action candidates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from guardian_sim.evaluator import CandidateEvaluator
from guardian_sim.models import ActionCandidate, CandidateMetrics, CandidateScore
from guardian_sim.scoring import rank_candidates, score_candidate


@dataclass(frozen=True, slots=True)
class RobustSelectionResult:
    """Selected action plus the evidence used for the conservative decision."""

    selected: CandidateScore
    nominal: CandidateScore
    observations_by_id: Mapping[str, tuple[CandidateMetrics, ...]]
    fallback_used: bool


def aggregate_conservatively(
    observations: Sequence[CandidateMetrics],
) -> CandidateMetrics:
    """Collapse repeated rollouts into a pessimistic physical measurement."""

    if not observations:
        raise ValueError("at least one observation is required")
    clearance_observation = min(
        observations,
        key=lambda metrics: metrics.collision_margin_m,
    )
    support_observation = max(
        observations,
        key=lambda metrics: (
            metrics.support_contact_diagnostic.overlap_depth_m
            if metrics.support_contact_diagnostic is not None
            else 0.0
        ),
    )
    return CandidateMetrics(
        collision_margin_m=min(item.collision_margin_m for item in observations),
        reachability=min(item.reachability for item in observations),
        grasp_alignment=min(item.grasp_alignment for item in observations),
        predicted_stability=min(item.predicted_stability for item in observations),
        path_length_m=max(item.path_length_m for item in observations),
        perception_uncertainty=max(
            item.perception_uncertainty for item in observations
        ),
        clearance_diagnostic=clearance_observation.clearance_diagnostic,
        support_contact_diagnostic=support_observation.support_contact_diagnostic,
    )


def select_robust_candidate(
    candidates: Sequence[ActionCandidate],
    initial_metrics_by_id: Mapping[str, CandidateMetrics],
    evaluator: CandidateEvaluator,
    *,
    nominal_candidate_id: str,
    shortlist_size: int = 3,
    confirmation_rollouts: int = 2,
    minimum_stability: float = 0.60,
    minimum_success_margin: float = 0.02,
) -> RobustSelectionResult:
    """Confirm top candidates and select using worst observed physical metrics."""

    if shortlist_size < 1:
        raise ValueError("shortlist_size must be positive")
    if confirmation_rollouts < 1:
        raise ValueError("confirmation_rollouts must be positive")
    if not 0.0 <= minimum_stability <= 1.0:
        raise ValueError("minimum_stability must be in [0, 1]")
    if not 0.0 <= minimum_success_margin <= 1.0:
        raise ValueError("minimum_success_margin must be in [0, 1]")

    candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    if len(candidates_by_id) != len(candidates):
        raise ValueError("candidate identifiers must be unique")
    try:
        nominal_candidate = candidates_by_id[nominal_candidate_id]
        nominal_initial = initial_metrics_by_id[nominal_candidate_id]
    except KeyError as exc:
        raise KeyError("nominal candidate and metrics are required") from exc

    initially_ranked = rank_candidates(candidates, initial_metrics_by_id)
    shortlist = [
        item.candidate for item in initially_ranked[: min(shortlist_size, len(candidates))]
    ]
    if nominal_candidate not in shortlist:
        shortlist.append(nominal_candidate)

    observations_by_id: dict[str, tuple[CandidateMetrics, ...]] = {}
    robust_scores: list[CandidateScore] = []
    for candidate in shortlist:
        observations = (
            initial_metrics_by_id[candidate.candidate_id],
            *(evaluator.evaluate(candidate) for _ in range(confirmation_rollouts)),
        )
        observations_by_id[candidate.candidate_id] = observations
        robust_scores.append(
            score_candidate(candidate, aggregate_conservatively(observations))
        )

    nominal_score = next(
        score
        for score in robust_scores
        if score.candidate.candidate_id == nominal_candidate_id
    )
    eligible = [
        score
        for score in robust_scores
        if score.metrics.reachability >= 1.0
        and score.metrics.predicted_stability >= minimum_stability
        and not (
            score.metrics.clearance_diagnostic is not None
            and score.metrics.clearance_diagnostic.overlaps
        )
    ]
    eligible.sort(
        key=lambda item: (
            -item.success_probability,
            item.risk,
            item.metrics.path_length_m,
            item.candidate.candidate_id,
        )
    )
    eligible_alternatives = [
        score
        for score in eligible
        if score.candidate.candidate_id != nominal_candidate_id
    ]
    best_alternative = eligible_alternatives[0] if eligible_alternatives else None
    if (
        best_alternative is not None
        and best_alternative.success_probability
        >= nominal_score.success_probability + minimum_success_margin
    ):
        selected = best_alternative
        fallback_used = False
    else:
        selected = nominal_score
        fallback_used = True
    return RobustSelectionResult(
        selected=selected,
        nominal=nominal_score,
        observations_by_id=observations_by_id,
        fallback_used=fallback_used,
    )
