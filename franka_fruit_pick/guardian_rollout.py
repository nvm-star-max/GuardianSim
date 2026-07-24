"""Genesis execution of one GuardianSim counterfactual grasp candidate."""

from __future__ import annotations

import logging
from math import inf

import numpy as np

from guardian_sim.genesis_adapter import GenesisRolloutMeasurement
from guardian_sim.models import ActionCandidate, ClearanceDiagnostic
from guardian_sim.reference_motion import candidate_grasp_pose
from guardian_sim.rollout_metrics import (
    RolloutTrace,
    aabb_clearance,
    aabb_overlap_depth,
    measure_rollout,
)

from .grasp_demo import (
    DEFAULT_PROFILE,
    GRASP_PROFILES,
    GRIPPER_OPEN,
    _descend_vertical,
    _goto_direct,
    _goto_interp,
    _goto_plan,
    _grasp_hand_z,
    _obj_xy_yaw,
    _to_numpy,
    _topdown_quat,
)

COUNTERFACTUAL_LIFT_HEIGHT_M = 0.10
_CLEARANCE_LINK_NAMES = ("link5", "link6", "link7", "hand", "left_finger", "right_finger")
_LOGGER = logging.getLogger(__name__)


def _aabb_tuple(entity) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    bounds = entity.get_AABB()
    if hasattr(bounds, "detach"):
        bounds = bounds.detach().cpu().numpy()
    bounds = np.asarray(bounds, dtype=float)
    if bounds.ndim == 3:
        bounds = bounds[0]
    return tuple(bounds[0]), tuple(bounds[1])


class _RolloutRecorder:
    def __init__(self, bundle, *, pick_object: str, sample_every: int = 5) -> None:
        self._bundle = bundle
        self._sample_every = max(1, sample_every)
        self._step = 0
        self._sample_index = 0
        self._hand = bundle.franka.get_link("hand")
        self._links = [
            (name, bundle.franka.get_link(name)) for name in _CLEARANCE_LINK_NAMES
        ]
        self._obstacles = [
            (name, entity, False)
            for name, entity in sorted(bundle.ycb.items())
            if name != pick_object
        ]
        if bundle.table:
            self._obstacles.append(("table_top", bundle.table[0], True))
        self.end_effector_positions: list[tuple[float, float, float]] = []
        self.minimum_clearance_m = inf
        self.clearance_diagnostic: ClearanceDiagnostic | None = None

    def on_step(self, _action) -> None:
        self._step += 1
        if self._step % self._sample_every == 0:
            self.sample()

    def sample(self) -> None:
        self.end_effector_positions.append(tuple(_to_numpy(self._hand.get_pos())[:3]))
        for link_name, link in self._links:
            link_bounds = _aabb_tuple(link)
            for obstacle_name, obstacle, support_surface in self._obstacles:
                obstacle_bounds = _aabb_tuple(obstacle)
                clearance = aabb_clearance(link_bounds, obstacle_bounds)
                overlap_depth = aabb_overlap_depth(link_bounds, obstacle_bounds)
                diagnostic = ClearanceDiagnostic(
                    sample_index=self._sample_index,
                    step_index=self._step,
                    link_name=link_name,
                    obstacle_name=obstacle_name,
                    clearance_m=clearance,
                    overlaps=overlap_depth > 0.0,
                    overlap_depth_m=overlap_depth,
                    support_surface=support_surface,
                )
                if self._is_more_critical(diagnostic):
                    self.minimum_clearance_m = clearance
                    self.clearance_diagnostic = diagnostic
        self._sample_index += 1

    def _is_more_critical(self, diagnostic: ClearanceDiagnostic) -> bool:
        if self.clearance_diagnostic is None:
            return True
        current = self.clearance_diagnostic
        return (
            diagnostic.clearance_m,
            -diagnostic.overlap_depth_m,
        ) < (
            current.clearance_m,
            -current.overlap_depth_m,
        )

    def clearance_or_zero(self) -> float:
        return 0.0 if self.minimum_clearance_m == inf else self.minimum_clearance_m


def run_grasp_candidate(
    bundle,
    candidate: ActionCandidate,
    *,
    pick_object: str = "011_banana",
    perception_uncertainty: float = 0.05,
) -> GenesisRolloutMeasurement:
    """Execute approach, grasp, and retained lift for one candidate."""

    pick_entity = bundle.ycb[pick_object]
    grasp_profile = GRASP_PROFILES.get(pick_object, DEFAULT_PROFILE)
    object_position, object_yaw = _obj_xy_yaw(pick_entity)
    object_start_height = float(object_position[2])
    grasp_target, grasp_yaw = candidate_grasp_pose(
        candidate,
        object_yaw_degrees=object_yaw + grasp_profile.yaw_offset,
    )
    grasp_z = _grasp_hand_z(pick_entity, grasp_profile)
    grasp_position = np.array((grasp_target[0], grasp_target[1], grasp_z), dtype=float)
    pregrasp_position = grasp_position.copy()
    pregrasp_position[2] = max(
        grasp_z + 0.04,
        object_start_height + candidate.approach_height_m,
    )
    grasp_quat = _topdown_quat(grasp_yaw)
    finger_open = min(GRIPPER_OPEN, candidate.gripper_width_m / 2.0)
    recorder = _RolloutRecorder(bundle, pick_object=pick_object)
    reachable = True

    try:
        recorder.sample()
        _goto_plan(
            bundle,
            pregrasp_position,
            grasp_quat,
            finger=finger_open,
            recorder=recorder,
        )
        _descend_vertical(
            bundle,
            grasp_position[:2],
            pregrasp_position[2],
            grasp_position[2],
            grasp_quat,
            finger=finger_open,
            recorder=recorder,
        )
        _goto_direct(
            bundle,
            grasp_position,
            grasp_quat,
            finger_cmd=0.0,
            steps=100,
            close_force=grasp_profile.close_force,
            recorder=recorder,
        )
        lift_position = grasp_position.copy()
        lift_position[2] += COUNTERFACTUAL_LIFT_HEIGHT_M
        _goto_interp(
            bundle,
            lift_position,
            grasp_quat,
            finger_cmd=0.0,
            close_force=grasp_profile.close_force,
            recorder=recorder,
        )
        recorder.sample()
    except Exception:
        _LOGGER.warning(
            "candidate %s could not complete its rollout",
            candidate.candidate_id,
            exc_info=True,
        )
        reachable = False

    retained_height = float(_to_numpy(pick_entity.get_pos())[2])
    trace = RolloutTrace(
        minimum_clearance_m=recorder.clearance_or_zero(),
        reachable=reachable,
        alignment_error_degrees=abs(candidate.yaw_degrees),
        object_start_height_m=object_start_height,
        object_retained_height_m=retained_height,
        requested_lift_height_m=COUNTERFACTUAL_LIFT_HEIGHT_M,
        end_effector_positions=tuple(recorder.end_effector_positions),
        perception_uncertainty=perception_uncertainty,
        clearance_diagnostic=recorder.clearance_diagnostic,
    )
    return measure_rollout(trace)
