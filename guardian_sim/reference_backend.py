"""Snapshot-safe rollout backend for the retained Franka reference scene."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Mapping, Protocol

from guardian_sim.genesis_adapter import GenesisRolloutMeasurement
from guardian_sim.models import ActionCandidate


@dataclass(frozen=True, slots=True)
class EntityPose:
    """World-frame pose of one simulated entity."""

    position: tuple[float, float, float]
    quaternion: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class EpisodeSnapshot:
    """State required to replay every candidate from an identical episode."""

    seed: int
    robot_qpos: tuple[float, ...]
    object_poses: Mapping[str, EntityPose]

    def canonical_json(self) -> str:
        payload = {
            "seed": self.seed,
            "robot_qpos": list(self.robot_qpos),
            "object_poses": {
                name: {
                    "position": list(pose.position),
                    "quaternion": list(pose.quaternion),
                }
                for name, pose in sorted(self.object_poses.items())
            },
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)

    def fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


class ReferenceSceneDriver(Protocol):
    """Genesis-specific scene operations used by the portable backend."""

    def capture_snapshot(self) -> EpisodeSnapshot:
        """Capture the current robot and task-object state."""

    def restore_snapshot(self, snapshot: EpisodeSnapshot) -> None:
        """Restore a previously captured state and clear dynamic velocity."""

    def rollout_candidate(self, candidate: ActionCandidate) -> GenesisRolloutMeasurement:
        """Execute one candidate and return simulator measurements."""


def _as_float_tuple(value: object) -> tuple[float, ...]:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "reshape"):
        value = value.reshape(-1)
    if hasattr(value, "tolist"):
        value = value.tolist()
    return tuple(float(item) for item in value)


class GenesisSceneDriver:
    """Capture and restore a built ``SceneBundle`` without importing Genesis."""

    def __init__(
        self,
        bundle: object,
        *,
        seed: int,
        rollout: Callable[[object, ActionCandidate], GenesisRolloutMeasurement] | None = None,
    ) -> None:
        self._bundle = bundle
        self._seed = seed
        self._rollout = rollout

    def capture_snapshot(self) -> EpisodeSnapshot:
        return EpisodeSnapshot(
            seed=self._seed,
            robot_qpos=_as_float_tuple(self._bundle.franka.get_qpos()),
            object_poses={
                name: EntityPose(
                    position=_as_float_tuple(entity.get_pos()),
                    quaternion=_as_float_tuple(entity.get_quat()),
                )
                for name, entity in sorted(self._bundle.ycb.items())
            },
        )

    def restore_snapshot(self, snapshot: EpisodeSnapshot) -> None:
        self._bundle.franka.set_qpos(snapshot.robot_qpos, zero_velocity=True)
        for name, pose in snapshot.object_poses.items():
            try:
                entity = self._bundle.ycb[name]
            except KeyError as exc:
                raise KeyError(f"snapshot object is missing from scene: {name}") from exc
            entity.set_pos(pose.position, zero_velocity=True)
            entity.set_quat(pose.quaternion, zero_velocity=True)

    def rollout_candidate(self, candidate: ActionCandidate) -> GenesisRolloutMeasurement:
        if self._rollout is None:
            raise RuntimeError("no Genesis candidate rollout function was configured")
        return self._rollout(self._bundle, candidate)


class ReferenceSceneRolloutBackend:
    """Apply identical-state restoration around reference-scene rollouts."""

    def __init__(self, driver: ReferenceSceneDriver, snapshot: EpisodeSnapshot) -> None:
        self._driver = driver
        self._snapshot = snapshot

    @classmethod
    def from_current_state(cls, driver: ReferenceSceneDriver) -> ReferenceSceneRolloutBackend:
        return cls(driver, driver.capture_snapshot())

    @property
    def snapshot(self) -> EpisodeSnapshot:
        return self._snapshot

    def restore_reference_state(self) -> None:
        self._driver.restore_snapshot(self._snapshot)

    def rollout(self, candidate: ActionCandidate) -> GenesisRolloutMeasurement:
        return self._driver.rollout_candidate(candidate)
