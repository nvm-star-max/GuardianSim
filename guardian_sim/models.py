"""Domain models shared by planning, scoring, and recovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class ActionCandidate:
    """A grasp proposal that can be evaluated in a cloned simulation."""

    candidate_id: str
    target_xyz: tuple[float, float, float]
    yaw_degrees: float
    lateral_offset_m: float
    approach_height_m: float
    gripper_width_m: float


@dataclass(frozen=True, slots=True)
class CandidateMetrics:
    """Normalized rollout metrics; all probabilities must be in [0, 1]."""

    collision_margin_m: float
    reachability: float
    grasp_alignment: float
    predicted_stability: float
    path_length_m: float
    perception_uncertainty: float


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate: ActionCandidate
    utility: float
    risk: float
    success_probability: float
    metrics: CandidateMetrics


@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    """Signals collected after a real or simulated execution attempt."""

    gripper_closed: bool
    object_lift_height_m: float
    target_distance_m: float
    max_contact_force_n: float
    object_slip_m: float
    collision: bool = False
    timed_out: bool = False


class FailureType(StrEnum):
    SUCCESS = "success"
    COLLISION = "collision"
    MISSED_GRASP = "missed_grasp"
    SLIP = "slip"
    WRONG_PLACEMENT = "wrong_placement"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class FailureDiagnosis:
    failure_type: FailureType
    reason: str
    confidence: float

    @property
    def succeeded(self) -> bool:
        return self.failure_type is FailureType.SUCCESS


class RecoveryAction(StrEnum):
    FINISH = "finish"
    SAFE_STOP = "safe_stop"
    REOBSERVE = "reobserve"
    WIDEN_GRIP = "widen_grip"
    CHANGE_GRASP_POSE = "change_grasp_pose"
    REPLAN_PATH = "replan_path"
