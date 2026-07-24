"""Map failure diagnoses to bounded, explainable recovery actions."""

from __future__ import annotations

from guardian_sim.models import FailureDiagnosis, FailureType, RecoveryAction


def choose_recovery(diagnosis: FailureDiagnosis, attempt_number: int, *, max_attempts: int = 3) -> RecoveryAction:
    if attempt_number < 1:
        raise ValueError("attempt_number starts at 1")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if diagnosis.succeeded:
        return RecoveryAction.FINISH
    if attempt_number >= max_attempts:
        return RecoveryAction.SAFE_STOP

    mapping = {
        FailureType.COLLISION: RecoveryAction.REPLAN_PATH,
        FailureType.MISSED_GRASP: RecoveryAction.CHANGE_GRASP_POSE,
        FailureType.SLIP: RecoveryAction.WIDEN_GRIP,
        FailureType.WRONG_PLACEMENT: RecoveryAction.REOBSERVE,
        FailureType.TIMEOUT: RecoveryAction.REPLAN_PATH,
    }
    return mapping[diagnosis.failure_type]
