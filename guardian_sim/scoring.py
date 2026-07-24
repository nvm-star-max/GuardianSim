"""Risk-aware scoring for counterfactual grasp rollouts."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from math import exp

from guardian_sim.models import ActionCandidate, CandidateMetrics, CandidateScore


DEFAULT_WEIGHTS: dict[str, float] = {
    "reachability": 0.20,
    "alignment": 0.22,
    "stability": 0.28,
    "clearance": 0.18,
    "path_efficiency": 0.07,
    "certainty": 0.05,
}


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def score_candidate(
    candidate: ActionCandidate,
    metrics: CandidateMetrics,
    *,
    weights: Mapping[str, float] = DEFAULT_WEIGHTS,
) -> CandidateScore:
    """Convert rollout metrics into an interpretable utility and risk score."""

    required = set(DEFAULT_WEIGHTS)
    if set(weights) != required:
        missing = sorted(required - set(weights))
        extra = sorted(set(weights) - required)
        raise ValueError(f"weights must contain exactly {sorted(required)}; missing={missing}, extra={extra}")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("weights cannot be negative")
    weight_total = sum(weights.values())
    if weight_total <= 0:
        raise ValueError("at least one weight must be positive")

    features = {
        "reachability": _clamp(metrics.reachability),
        "alignment": _clamp(metrics.grasp_alignment),
        "stability": _clamp(metrics.predicted_stability),
        "clearance": _clamp(metrics.collision_margin_m / 0.10),
        "path_efficiency": exp(-max(0.0, metrics.path_length_m) / 0.8),
        "certainty": 1.0 - _clamp(metrics.perception_uncertainty),
    }
    utility = sum(weights[name] * value for name, value in features.items()) / weight_total

    collision_risk = 1.0 - features["clearance"]
    instability_risk = 1.0 - features["stability"]
    uncertainty_risk = 1.0 - features["certainty"]
    risk = _clamp(0.55 * collision_risk + 0.30 * instability_risk + 0.15 * uncertainty_risk)

    # Keep the probability conservative when a high-utility action is still risky.
    success_probability = _clamp(utility * (1.0 - 0.65 * risk))
    return CandidateScore(
        candidate=candidate,
        utility=utility,
        risk=risk,
        success_probability=success_probability,
        metrics=metrics,
    )


def rank_candidates(
    candidates: Iterable[ActionCandidate],
    metrics_by_id: Mapping[str, CandidateMetrics],
) -> list[CandidateScore]:
    """Rank candidates by predicted success, then lower risk and shorter path."""

    scores: list[CandidateScore] = []
    for candidate in candidates:
        try:
            metrics = metrics_by_id[candidate.candidate_id]
        except KeyError as exc:
            raise KeyError(f"missing rollout metrics for {candidate.candidate_id}") from exc
        scores.append(score_candidate(candidate, metrics))

    return sorted(
        scores,
        key=lambda item: (
            -item.success_probability,
            item.risk,
            item.metrics.path_length_m,
            item.candidate.candidate_id,
        ),
    )
