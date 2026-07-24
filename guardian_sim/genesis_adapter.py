"""Thin adapter between GuardianSim and a Genesis rollout implementation.

The adapter deliberately has no import-time Genesis dependency. Radeon Cloud can
provide a concrete backend while the decision core and tests remain runnable on
macOS.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from guardian_sim.models import ActionCandidate, CandidateMetrics, ClearanceDiagnostic


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True, slots=True)
class GenesisRolloutMeasurement:
    """Raw measurements returned by one cloned Genesis rollout."""

    minimum_clearance_m: float
    reachable: bool
    alignment_error_degrees: float
    retained_lift_height_m: float
    requested_lift_height_m: float
    path_length_m: float
    perception_uncertainty: float
    clearance_diagnostic: ClearanceDiagnostic | None = None


class GenesisRolloutBackend(Protocol):
    """The small surface the cloud-specific Genesis runner must implement."""

    def restore_reference_state(self) -> None:
        """Restore the exact same scene state before each candidate."""

    def rollout(self, candidate: ActionCandidate) -> GenesisRolloutMeasurement:
        """Run a candidate in simulation and return measured safety signals."""


class GenesisCandidateEvaluator:
    """Convert raw Genesis rollout measurements to normalized planner metrics."""

    def __init__(self, backend: GenesisRolloutBackend) -> None:
        self._backend = backend

    def evaluate(self, candidate: ActionCandidate) -> CandidateMetrics:
        self._backend.restore_reference_state()
        measurement = self._backend.rollout(candidate)
        lift_denominator = max(measurement.requested_lift_height_m, 1e-6)
        return CandidateMetrics(
            collision_margin_m=measurement.minimum_clearance_m,
            reachability=1.0 if measurement.reachable else 0.0,
            grasp_alignment=_clamp(1.0 - abs(measurement.alignment_error_degrees) / 90.0),
            predicted_stability=_clamp(measurement.retained_lift_height_m / lift_denominator),
            path_length_m=max(0.0, measurement.path_length_m),
            perception_uncertainty=_clamp(measurement.perception_uncertainty),
            clearance_diagnostic=measurement.clearance_diagnostic,
        )


def build_reference_scene(*, n_envs: int = 1):
    """Lazily build the competition reference scene on a Genesis-capable host."""

    if n_envs < 1:
        raise ValueError("n_envs must be positive")
    try:
        from franka_fruit_pick.build_scene import build_scene
    except ImportError as exc:
        raise RuntimeError(
            "Genesis reference scene is unavailable. Run scripts/install_system_deps.sh "
            "and scripts/install_rocm_stack.sh inside Radeon Cloud first."
        ) from exc
    return build_scene(n_envs=n_envs)
