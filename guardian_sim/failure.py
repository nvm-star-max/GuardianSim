"""Post-condition based failure detection."""

from __future__ import annotations

from guardian_sim.models import ExecutionOutcome, FailureDiagnosis, FailureType


def diagnose_outcome(
    outcome: ExecutionOutcome,
    *,
    minimum_lift_m: float = 0.04,
    placement_tolerance_m: float = 0.07,
    slip_tolerance_m: float = 0.025,
) -> FailureDiagnosis:
    """Diagnose the dominant execution failure using ordered safety checks."""

    if outcome.collision:
        return FailureDiagnosis(FailureType.COLLISION, "unexpected robot or object collision", 0.99)
    if outcome.timed_out:
        return FailureDiagnosis(FailureType.TIMEOUT, "execution exceeded the task time limit", 0.98)
    if not outcome.gripper_closed or outcome.object_lift_height_m < minimum_lift_m:
        return FailureDiagnosis(FailureType.MISSED_GRASP, "object was not securely lifted", 0.94)
    if outcome.object_slip_m > slip_tolerance_m:
        confidence = min(0.99, 0.75 + outcome.object_slip_m)
        return FailureDiagnosis(FailureType.SLIP, "object moved inside the gripper after lift", confidence)
    if outcome.target_distance_m > placement_tolerance_m:
        confidence = min(0.99, 0.75 + outcome.target_distance_m)
        return FailureDiagnosis(FailureType.WRONG_PLACEMENT, "object finished outside the target region", confidence)
    return FailureDiagnosis(FailureType.SUCCESS, "task post-conditions satisfied", 0.99)
