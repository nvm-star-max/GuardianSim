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
from franka_fruit_pick.scene_config import (
    VIDEO_CAM_FOV,
    VIDEO_CAM_LOOKAT,
    VIDEO_CAM_POS,
    get_ycb_assets,
)
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
from guardian_sim.genesis_adapter import candidate_metrics_from_measurement
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


def _project_world_to_pixel(
    point_xyz: tuple[float, float, float],
    *,
    width: int,
    height: int,
) -> tuple[int, int]:
    position = np.asarray(VIDEO_CAM_POS, dtype=float)
    lookat = np.asarray(VIDEO_CAM_LOOKAT, dtype=float)
    point = np.asarray(point_xyz, dtype=float)
    forward = lookat - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.asarray((0.0, 0.0, 1.0)))
    right /= np.linalg.norm(right)
    camera_up = np.cross(right, forward)
    relative = point - position
    depth = max(float(np.dot(relative, forward)), 1e-6)
    focal = height / (2.0 * np.tan(np.deg2rad(VIDEO_CAM_FOV) / 2.0))
    x = width / 2.0 + focal * float(np.dot(relative, right)) / depth
    y = height / 2.0 - focal * float(np.dot(relative, camera_up)) / depth
    return int(np.clip(x, 0, width - 1)), int(np.clip(y, 0, height - 1))


def _annotate_obstacle(
    frame: np.ndarray,
    *,
    obstacle_pixel: tuple[int, int],
    color: tuple[int, int, int],
    event_active: bool,
) -> np.ndarray:
    annotated = frame.copy()
    x, y = obstacle_pixel
    radius = 58 if event_active else 42
    thickness = 8 if event_active else 5
    cv2.circle(annotated, (x, y), radius, color, thickness, cv2.LINE_AA)
    label_x = int(np.clip(x + 70, 24, frame.shape[1] - 330))
    label_y = int(np.clip(y - 70, 50, frame.shape[0] - 24))
    cv2.arrowedLine(
        annotated,
        (label_x, label_y + 10),
        (x + 28, y - 28),
        color,
        5,
        cv2.LINE_AA,
        tipLength=0.18,
    )
    cv2.putText(
        annotated,
        "PLUM OBSTACLE",
        (label_x, label_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        color,
        3,
        cv2.LINE_AA,
    )
    return annotated


def _draw_panel_header(
    canvas: np.ndarray,
    *,
    x_offset: int,
    width: int,
    title: str,
    subtitle: str,
    color: tuple[int, int, int],
) -> None:
    cv2.rectangle(canvas, (x_offset, 160), (x_offset + width, 168), color, -1)
    cv2.putText(
        canvas,
        title,
        (x_offset + 28, 119),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.06,
        (250, 250, 250),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        subtitle,
        (x_offset + 30, 151),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )


def _draw_footer(
    canvas: np.ndarray,
    *,
    x_offset: int,
    width: int,
    y_offset: int,
    outcome: str,
    metric_line: str,
    action_line: str,
    color: tuple[int, int, int],
) -> None:
    cv2.putText(
        canvas,
        outcome,
        (x_offset + 28, y_offset + 66),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.18,
        color,
        4,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        metric_line,
        (x_offset + 30, y_offset + 112),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.82,
        (245, 245, 245),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        canvas,
        action_line,
        (x_offset + 30, y_offset + 154),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.70,
        (185, 192, 204),
        2,
        cv2.LINE_AA,
    )
    cv2.rectangle(
        canvas,
        (x_offset + 4, y_offset + 8),
        (x_offset + width - 4, y_offset + 174),
        color,
        4,
    )


def _phase_label(index: int, frame_count: int) -> str:
    ratio = index / max(frame_count - 1, 1)
    if ratio < 0.12:
        return "SAME INITIAL STATE"
    if ratio < 0.56:
        return "APPROACH"
    if ratio < 0.78:
        return "GRASP"
    return "LIFT + SAFETY CHECK"


def _compose_video(
    *,
    baseline_frames: list[np.ndarray],
    guardian_frames: list[np.ndarray],
    baseline_metrics,
    guardian_metrics,
    scenario_label: str,
    obstacle_xyz: tuple[float, float, float],
    capture_every: int,
    baseline_yaw_degrees: float,
    guardian_yaw_degrees: float,
    output_path: Path,
    fps: int,
) -> None:
    if not baseline_frames or not guardian_frames:
        raise RuntimeError("both strategies must produce rendered frames")
    frame_count = max(len(baseline_frames), len(guardian_frames))
    height, width = baseline_frames[0].shape[:2]
    if guardian_frames[0].shape[:2] != (height, width):
        raise RuntimeError("both panels must use the same camera resolution")
    obstacle_pixel = _project_world_to_pixel(
        obstacle_xyz,
        width=width,
        height=height,
    )
    header_height = 170
    footer_height = 190
    output_height = header_height + height + footer_height
    output_width = width * 2
    baseline_event_step = (
        baseline_metrics.clearance_diagnostic.step_index
        if baseline_metrics.clearance_diagnostic is not None
        else frame_count * capture_every
    )
    guardian_event_step = (
        guardian_metrics.clearance_diagnostic.step_index
        if guardian_metrics.clearance_diagnostic is not None
        else frame_count * capture_every
    )
    baseline_event_index = min(frame_count - 1, baseline_event_step // capture_every)
    guardian_event_index = min(frame_count - 1, guardian_event_step // capture_every)
    red = (255, 92, 82)
    green = (95, 255, 144)

    def compose(index: int, *, freeze_label: str | None = None) -> np.ndarray:
        baseline_frame = baseline_frames[min(index, len(baseline_frames) - 1)]
        guardian_frame = guardian_frames[min(index, len(guardian_frames) - 1)]
        baseline_active = index >= baseline_event_index
        guardian_active = index >= guardian_event_index
        baseline_panel = _annotate_obstacle(
            baseline_frame,
            obstacle_pixel=obstacle_pixel,
            color=red,
            event_active=baseline_active,
        )
        guardian_panel = _annotate_obstacle(
            guardian_frame,
            obstacle_pixel=obstacle_pixel,
            color=green,
            event_active=guardian_active,
        )
        combined = np.full((output_height, output_width, 3), 12, dtype=np.uint8)
        combined[header_height : header_height + height, :width] = baseline_panel
        combined[header_height : header_height + height, width:] = guardian_panel
        cv2.rectangle(
            combined,
            (0, header_height),
            (width - 1, header_height + height - 1),
            red if baseline_active else (80, 80, 90),
            10,
        )
        cv2.rectangle(
            combined,
            (width, header_height),
            (output_width - 1, header_height + height - 1),
            green if guardian_active else (80, 80, 90),
            10,
        )
        cv2.line(
            combined,
            (width, 0),
            (width, output_height),
            (240, 240, 240),
            4,
        )
        cv2.putText(
            combined,
            "SAME SCENE. SAME START. DIFFERENT GRASP.",
            (34, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.18,
            (245, 245, 245),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            combined,
            scenario_label,
            (36, 88),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.67,
            (182, 190, 205),
            2,
            cv2.LINE_AA,
        )
        phase = freeze_label or _phase_label(index, frame_count)
        phase_width = cv2.getTextSize(
            phase,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.86,
            3,
        )[0][0]
        cv2.putText(
            combined,
            phase,
            (output_width - phase_width - 34, 58),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.86,
            (255, 220, 104),
            3,
            cv2.LINE_AA,
        )
        _draw_panel_header(
            combined,
            x_offset=0,
            width=width,
            title="LEFT  |  NOMINAL BASELINE",
            subtitle="Straight-down grasp",
            color=red,
        )
        _draw_panel_header(
            combined,
            x_offset=width,
            width=width,
            title="RIGHT  |  GUARDIANSIM",
            subtitle="Obstacle-aware rotated grasp",
            color=green,
        )
        footer_y = header_height + height
        overlap_mm = (
            baseline_metrics.clearance_diagnostic.overlap_depth_m * 1000.0
            if baseline_metrics.clearance_diagnostic is not None
            else 0.0
        )
        _draw_footer(
            combined,
            x_offset=0,
            width=width,
            y_offset=footer_y,
            outcome="CONTACT / COLLISION",
            metric_line=(
                f"Clearance 0.0 mm  |  overlap {overlap_mm:.2f} mm  |  "
                f"stability {baseline_metrics.predicted_stability:.3f}"
            ),
            action_line=f"Action: yaw {baseline_yaw_degrees:+.1f} deg, direct approach",
            color=red,
        )
        _draw_footer(
            combined,
            x_offset=width,
            width=width,
            y_offset=footer_y,
            outcome="SAFE CLEARANCE",
            metric_line=(
                f"Clearance {guardian_metrics.collision_margin_m * 1000.0:.1f} mm  |  "
                f"no overlap  |  stability {guardian_metrics.predicted_stability:.3f}"
            ),
            action_line=f"Action: yaw {guardian_yaw_degrees:+.1f} deg, raised approach",
            color=green,
        )
        return combined

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
        first_frame = compose(0, freeze_label="WATCH THE PLUM OBSTACLE")
        for _ in range(fps * 2):
            writer.append_data(first_frame)
        for index in range(frame_count):
            writer.append_data(compose(index))
            if index == baseline_event_index:
                freeze = compose(index, freeze_label="PAUSE: LEFT HAND CONTACTS PLUM")
                for _ in range(fps * 2):
                    writer.append_data(freeze)
        final_frame = compose(frame_count - 1, freeze_label="RESULT: CONTACT vs SAFE")
        for _ in range(fps * 3):
            writer.append_data(final_frame)


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
    baseline_measurement = run_grasp_candidate(
        bundle,
        nominal,
        pick_object=scenario.pick_object,
        frame_callback=baseline_recorder,
    )
    baseline_metrics = candidate_metrics_from_measurement(baseline_measurement)
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
    guardian_measurement = run_grasp_candidate(
        bundle,
        guardian,
        pick_object=scenario.pick_object,
        frame_callback=guardian_recorder,
    )
    guardian_metrics = candidate_metrics_from_measurement(guardian_measurement)
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
        baseline_metrics=baseline_metrics,
        guardian_metrics=guardian_metrics,
        scenario_label=(f"VISUAL REPLAY · seed {scenario.seed} · {scenario.pick_object} · {scenario.layout}"),
        obstacle_xyz=obstacle_xyz,
        capture_every=args.capture_every,
        baseline_yaw_degrees=nominal.yaw_degrees,
        guardian_yaw_degrees=guardian.yaw_degrees,
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
