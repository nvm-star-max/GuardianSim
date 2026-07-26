#!/usr/bin/env python3
"""Record a side-by-side visual replay of one verified Gate 3.2 scenario.

The generated video is a fresh visual replay using the frozen scenario
configuration and the action selected in the formal report. It is not appended
to, and must not be presented as part of, the formal benchmark evidence.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import cv2
import genesis as gs
import imageio.v2 as imageio
import numpy as np
from run_gate31_adversarial_benchmark import RuntimeDynamicsController

from franka_fruit_pick.build_scene import build_scene
from franka_fruit_pick.grasp_demo import _settle, _to_numpy
from franka_fruit_pick.guardian_rollout import run_grasp_candidate
from franka_fruit_pick.scene_config import get_ycb_assets
from guardian_sim.adversarial_benchmark import (
    PRIMARY_OBSTACLE_BY_PICK,
    apply_gate31_scenario,
    classify_gate31_execution,
)
from guardian_sim.candidates import generate_obstacle_aware_candidates
from guardian_sim.gate32_benchmark import (
    GATE32_MINIMUM_SAFE_CLEARANCE_M,
    GATE32_MINIMUM_STABILITY,
    generate_gate32_scenarios,
    validate_gate32_payload,
)
from guardian_sim.reference_backend import EpisodeSnapshot, GenesisSceneDriver
from guardian_sim.serialization import json_default

NOMINAL_CANDIDATE_ID = "yaw_+00.0_offset_+0.000"
SETTLE_STEPS = 40


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--seed", type=int, default=411)
    parser.add_argument(
        "--report",
        default="docs/evidence/gate-3-2/formal-report.json",
    )
    parser.add_argument(
        "--output",
        default="outputs/demo/gate-3-2-seed-411.mp4",
    )
    parser.add_argument("--fps", type=int, default=20)
    parser.add_argument(
        "--capture-every",
        type=int,
        default=4,
        help="capture one rendered frame every N simulator control steps",
    )
    return parser


def _as_rgb_uint8(frame) -> np.ndarray:
    if hasattr(frame, "detach"):
        frame = frame.detach().cpu().numpy()
    array = np.asarray(frame)
    if array.ndim == 4:
        array = array[0]
    if np.issubdtype(array.dtype, np.floating):
        array = np.clip(array, 0.0, 1.0) * 255.0
    return np.ascontiguousarray(array[..., :3].astype(np.uint8))


class CameraFrameRecorder:
    def __init__(self, bundle, *, capture_every: int) -> None:
        if bundle.video_cam is None:
            raise ValueError("the demo scene requires a video camera")
        self.bundle = bundle
        self.capture_every = max(1, capture_every)
        self.frames: list[np.ndarray] = []

    def __call__(self, step_index: int) -> None:
        if step_index % self.capture_every == 0:
            self.capture()

    def capture(self) -> None:
        rendered = self.bundle.video_cam.render(rgb=True)[0]
        self.frames.append(_as_rgb_uint8(rendered))


def _status_text(classification) -> tuple[str, tuple[int, int, int]]:
    if classification.safe_completion:
        return "SAFE", (216, 255, 95)
    return classification.failure_type.replace("_", " ").upper(), (255, 118, 92)


def _panel(
    frame: np.ndarray,
    *,
    title: str,
    candidate_id: str,
    classification,
    metrics,
) -> np.ndarray:
    height, width = frame.shape[:2]
    canvas = np.full((height + 108, width, 3), 13, dtype=np.uint8)
    canvas[76 : 76 + height] = frame
    status, status_color = _status_text(classification)
    cv2.putText(
        canvas,
        title,
        (20, 31),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.78,
        (245, 245, 245),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        status,
        (20, 61),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        status_color,
        2,
        cv2.LINE_AA,
    )
    detail = f"{candidate_id}  clearance={metrics.collision_margin_m:.3f}m  stability={metrics.predicted_stability:.3f}"
    cv2.putText(
        canvas,
        detail,
        (20, height + 99),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (205, 210, 218),
        1,
        cv2.LINE_AA,
    )
    return canvas


def _compose_video(
    *,
    baseline_frames: list[np.ndarray],
    guardian_frames: list[np.ndarray],
    baseline_candidate_id: str,
    guardian_candidate_id: str,
    baseline_classification,
    guardian_classification,
    baseline_metrics,
    guardian_metrics,
    scenario_label: str,
    output_path: Path,
    fps: int,
) -> None:
    if not baseline_frames or not guardian_frames:
        raise RuntimeError("both strategies must produce rendered frames")
    frame_count = max(len(baseline_frames), len(guardian_frames))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with imageio.get_writer(
        output_path,
        format="ffmpeg",
        mode="I",
        fps=fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=2,
    ) as writer:
        for index in range(frame_count):
            baseline_frame = baseline_frames[min(index, len(baseline_frames) - 1)]
            guardian_frame = guardian_frames[min(index, len(guardian_frames) - 1)]
            baseline_panel = _panel(
                baseline_frame,
                title="NOMINAL BASELINE",
                candidate_id=baseline_candidate_id,
                classification=baseline_classification,
                metrics=baseline_metrics,
            )
            guardian_panel = _panel(
                guardian_frame,
                title="GUARDIANSIM",
                candidate_id=guardian_candidate_id,
                classification=guardian_classification,
                metrics=guardian_metrics,
            )
            combined = np.concatenate([baseline_panel, guardian_panel], axis=1)
            cv2.putText(
                combined,
                scenario_label,
                (combined.shape[1] // 2 - 210, 31),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (216, 255, 95),
                1,
                cv2.LINE_AA,
            )
            writer.append_data(combined)


def main() -> None:
    args = build_parser().parse_args()
    if args.capture_every < 1 or args.fps < 1:
        raise ValueError("--capture-every and --fps must be positive")

    report_path = Path(args.report)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_gate32_payload(report, require_complete=True)
    formal_episode = next(
        (episode for episode in report["episodes"] if episode["seed"] == args.seed),
        None,
    )
    if formal_episode is None:
        raise ValueError(f"seed {args.seed} is not present in the formal report")
    if formal_episode["guardiansim"]["candidate"] is None:
        raise ValueError(f"seed {args.seed} used a formal safe-stop")

    scenario = next(item for item in generate_gate32_scenarios() if item.seed == args.seed)
    guardian_candidate_id = formal_episode["guardiansim"]["candidate"]["candidate_id"]

    gs.init(backend=gs.cpu if args.cpu else gs.gpu)
    bundle = build_scene(
        n_envs=1,
        add_world_cam=False,
        add_wrist_cam=False,
        add_video_cam=True,
    )
    _settle(bundle, 60)
    driver = GenesisSceneDriver(bundle, seed=scenario.seed)
    base_snapshot = driver.capture_snapshot()
    footprint_radii = {name: asset.radius_xy for name, asset in get_ycb_assets().items()}
    challenge_snapshot = apply_gate31_scenario(
        base_snapshot,
        scenario,
        footprint_radii_m=footprint_radii,
    )
    driver.restore_snapshot(challenge_snapshot)
    RuntimeDynamicsController(bundle).apply(
        pick_object=scenario.pick_object,
        friction_ratio=scenario.friction_ratio,
        target_mass_ratio=scenario.target_mass_ratio,
    )
    _settle(bundle, SETTLE_STEPS)
    settled_snapshot = driver.capture_snapshot()
    episode_snapshot = EpisodeSnapshot(
        seed=scenario.seed,
        robot_qpos=settled_snapshot.robot_qpos,
        object_poses=settled_snapshot.object_poses,
    )

    obstacle_name = PRIMARY_OBSTACLE_BY_PICK[scenario.pick_object]
    target_xyz = tuple(_to_numpy(bundle.ycb[scenario.pick_object].get_pos())[:3])
    obstacle_xyz = tuple(_to_numpy(bundle.ycb[obstacle_name].get_pos())[:3])
    candidates = tuple(generate_obstacle_aware_candidates(target_xyz, obstacle_xyz))
    candidates_by_id = {candidate.candidate_id: candidate for candidate in candidates}
    nominal = candidates_by_id[NOMINAL_CANDIDATE_ID]
    guardian = candidates_by_id[guardian_candidate_id]

    driver.restore_snapshot(episode_snapshot)
    baseline_recorder = CameraFrameRecorder(
        bundle,
        capture_every=args.capture_every,
    )
    baseline_recorder.capture()
    baseline_metrics = run_grasp_candidate(
        bundle,
        nominal,
        pick_object=scenario.pick_object,
        frame_callback=baseline_recorder,
    )
    baseline_recorder.capture()
    baseline_classification = classify_gate31_execution(
        baseline_metrics,
        minimum_stability=GATE32_MINIMUM_STABILITY,
        minimum_safe_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
    )

    driver.restore_snapshot(episode_snapshot)
    guardian_recorder = CameraFrameRecorder(
        bundle,
        capture_every=args.capture_every,
    )
    guardian_recorder.capture()
    guardian_metrics = run_grasp_candidate(
        bundle,
        guardian,
        pick_object=scenario.pick_object,
        frame_callback=guardian_recorder,
    )
    guardian_recorder.capture()
    guardian_classification = classify_gate31_execution(
        guardian_metrics,
        minimum_stability=GATE32_MINIMUM_STABILITY,
        minimum_safe_clearance_m=GATE32_MINIMUM_SAFE_CLEARANCE_M,
    )

    output_path = Path(args.output)
    _compose_video(
        baseline_frames=baseline_recorder.frames,
        guardian_frames=guardian_recorder.frames,
        baseline_candidate_id=nominal.candidate_id,
        guardian_candidate_id=guardian.candidate_id,
        baseline_classification=baseline_classification,
        guardian_classification=guardian_classification,
        baseline_metrics=baseline_metrics,
        guardian_metrics=guardian_metrics,
        scenario_label=(f"VISUAL REPLAY · seed {scenario.seed} · {scenario.pick_object} · {scenario.layout}"),
        output_path=output_path,
        fps=args.fps,
    )

    sidecar = {
        "kind": "gate32_visual_replay_not_formal_evidence",
        "formal_report": str(report_path),
        "formal_protocol_sha256": report["protocol"]["protocol_sha256"],
        "seed": scenario.seed,
        "scenario_id": scenario.scenario_id,
        "pick_object": scenario.pick_object,
        "layout": scenario.layout,
        "primary_obstacle": obstacle_name,
        "formal_baseline_repeatable_safe": formal_episode["baseline"]["aggregate"]["repeatable_safe_completion"],
        "formal_guardian_repeatable_safe": formal_episode["guardiansim"]["aggregate"]["repeatable_safe_completion"],
        "visual_replay": {
            "baseline": {
                "candidate": asdict(nominal),
                "metrics": asdict(baseline_metrics),
                "classification": asdict(baseline_classification),
                "frame_count": len(baseline_recorder.frames),
            },
            "guardiansim": {
                "candidate": asdict(guardian),
                "metrics": asdict(guardian_metrics),
                "classification": asdict(guardian_classification),
                "frame_count": len(guardian_recorder.frames),
            },
        },
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(
        json.dumps(sidecar, default=json_default, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "video": str(output_path),
                "sidecar": str(sidecar_path),
                "baseline_safe": baseline_classification.safe_completion,
                "guardian_safe": guardian_classification.safe_completion,
                "baseline_frames": len(baseline_recorder.frames),
                "guardian_frames": len(guardian_recorder.frames),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
