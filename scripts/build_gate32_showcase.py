#!/usr/bin/env python3
"""Build the Aegis Motion judge-facing hero clip from a verified replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import imageio.v2 as imageio
import numpy as np

WIDTH = 1920
HEIGHT = 1080
SOURCE_FRAME_TOP = 76
SOURCE_FRAME_HEIGHT = 720
SOURCE_CAPTURE_EVERY = 4
RED = (82, 92, 255)
GREEN = (144, 255, 95)
AMBER = (104, 220, 255)
WHITE = (245, 245, 245)
MUTED = (180, 187, 200)
INK = (13, 15, 20)
PANEL = (24, 27, 34)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(
    frame: np.ndarray,
    value: str,
    point: tuple[int, int],
    *,
    scale: float,
    color: tuple[int, int, int] = WHITE,
    thickness: int = 2,
) -> None:
    cv2.putText(
        frame,
        value,
        point,
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        thickness,
        cv2.LINE_AA,
    )


def _read_source_frames(path: Path) -> tuple[list[np.ndarray], list[np.ndarray]]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise RuntimeError(f"cannot open source video: {path}")
    left: list[np.ndarray] = []
    right: list[np.ndarray] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            height, width = frame.shape[:2]
            if height < SOURCE_FRAME_TOP + SOURCE_FRAME_HEIGHT or width % 2:
                raise RuntimeError(f"unexpected source dimensions: {width}x{height}")
            split = width // 2
            bottom = SOURCE_FRAME_TOP + SOURCE_FRAME_HEIGHT
            left.append(frame[SOURCE_FRAME_TOP:bottom, :split].copy())
            right.append(frame[SOURCE_FRAME_TOP:bottom, split:].copy())
    finally:
        capture.release()
    if not left:
        raise RuntimeError("source video contains no frames")
    return left, right


def _base() -> np.ndarray:
    frame = np.full((HEIGHT, WIDTH, 3), INK, dtype=np.uint8)
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        frame[y, :, :] = (
            int(13 + 9 * ratio),
            int(15 + 7 * ratio),
            int(20 + 9 * ratio),
        )
    return frame


def _accent(frame: np.ndarray) -> None:
    cv2.rectangle(frame, (0, 0), (18, HEIGHT), RED, -1)
    cv2.rectangle(frame, (18, 0), (25, HEIGHT), GREEN, -1)


def _title_card() -> np.ndarray:
    frame = _base()
    _accent(frame)
    _text(frame, "AEGIS MOTION", (110, 135), scale=1.15, color=RED, thickness=3)
    _text(frame, "GUARDIANSIM", (110, 275), scale=2.55, thickness=6)
    _text(
        frame,
        "Counterfactual safety certification before robot execution",
        (116, 345),
        scale=0.92,
        color=MUTED,
        thickness=2,
    )
    cv2.line(frame, (110, 405), (1810, 405), (65, 69, 80), 2)
    _text(frame, "SAME SCENE", (155, 515), scale=1.35, thickness=4)
    _text(frame, "SAME START", (690, 515), scale=1.35, thickness=4)
    _text(frame, "DIFFERENT DECISION", (1160, 515), scale=1.35, color=AMBER, thickness=4)
    cv2.rectangle(frame, (145, 610), (875, 825), PANEL, -1)
    cv2.rectangle(frame, (145, 610), (875, 825), RED, 4)
    _text(frame, "NOMINAL", (195, 670), scale=0.82, color=RED, thickness=3)
    _text(frame, "CONTACT", (195, 760), scale=1.75, color=RED, thickness=5)
    _text(frame, "Measured overlap: 1.42 mm", (195, 805), scale=0.67, color=MUTED)
    cv2.rectangle(frame, (945, 610), (1675, 825), PANEL, -1)
    cv2.rectangle(frame, (945, 610), (1675, 825), GREEN, 4)
    _text(frame, "GUARDIANSIM", (995, 670), scale=0.82, color=GREEN, thickness=3)
    _text(frame, "SAFE", (995, 760), scale=1.75, color=GREEN, thickness=5)
    _text(frame, "Measured clearance: 17.1 mm", (995, 805), scale=0.67, color=MUTED)
    _text(
        frame,
        "AMD Radeon Cloud  |  ROCm/HIP  |  Genesis simulation",
        (110, 1000),
        scale=0.72,
        color=MUTED,
        thickness=2,
    )
    return frame


def _rotated_box(
    frame: np.ndarray,
    *,
    center: tuple[int, int],
    angle: float,
    color: tuple[int, int, int],
) -> None:
    box = cv2.boxPoints((center, (180, 54), angle)).astype(np.int32)
    cv2.polylines(frame, [box], True, color, 6, cv2.LINE_AA)
    theta = np.deg2rad(angle)
    direction = np.asarray((np.cos(theta), np.sin(theta)))
    normal = np.asarray((-direction[1], direction[0]))
    center_array = np.asarray(center, dtype=float)
    for sign in (-1.0, 1.0):
        start = center_array + normal * sign * 50 - direction * 80
        end = center_array + normal * sign * 50 + direction * 80
        cv2.line(
            frame,
            tuple(start.astype(int)),
            tuple(end.astype(int)),
            color,
            8,
            cv2.LINE_AA,
        )


def _geometry_panel(
    frame: np.ndarray,
    *,
    bounds: tuple[int, int, int, int],
    title: str,
    angle: float,
    color: tuple[int, int, int],
    result: str,
    safe: bool,
) -> None:
    x1, y1, x2, y2 = bounds
    cv2.rectangle(frame, (x1, y1), (x2, y2), PANEL, -1)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 4)
    _text(frame, title, (x1 + 35, y1 + 60), scale=0.84, color=color, thickness=3)
    _text(frame, "TOP-DOWN ACTION GEOMETRY", (x1 + 35, y1 + 99), scale=0.54, color=MUTED)
    target = (x1 + 350, y1 + 330)
    obstacle = (target[0], target[1] - 118)
    cv2.circle(frame, target, 30, (45, 220, 240), -1, cv2.LINE_AA)
    cv2.circle(frame, obstacle, 36, (110, 45, 95), -1, cv2.LINE_AA)
    _text(frame, "LEMON", (target[0] + 44, target[1] + 9), scale=0.48, color=WHITE)
    _text(frame, "PLUM", (obstacle[0] + 50, obstacle[1] + 8), scale=0.48, color=WHITE)
    _rotated_box(frame, center=target, angle=angle, color=color)
    if safe:
        cv2.line(
            frame,
            (obstacle[0] + 25, obstacle[1] + 25),
            (target[0] + 85, target[1] - 15),
            GREEN,
            4,
            cv2.LINE_AA,
        )
        _text(frame, "17.1 mm", (target[0] + 90, target[1] - 45), scale=0.56, color=GREEN, thickness=2)
    else:
        cv2.circle(frame, obstacle, 52, RED, 5, cv2.LINE_AA)
        _text(frame, "OVERLAP", (obstacle[0] - 95, obstacle[1] - 60), scale=0.58, color=RED, thickness=3)
    _text(frame, result, (x1 + 35, y2 - 48), scale=0.76, color=color, thickness=3)


def _geometry_card() -> np.ndarray:
    frame = _base()
    _accent(frame)
    _text(frame, "WHY THE DECISION CHANGES", (90, 105), scale=1.35, thickness=4)
    _text(
        frame,
        "Measured action geometry, illustrated in plan view",
        (92, 150),
        scale=0.67,
        color=MUTED,
    )
    _geometry_panel(
        frame,
        bounds=(90, 215, 910, 900),
        title="LEFT  |  NOMINAL YAW 0 deg",
        angle=90.0,
        color=RED,
        result="0.0 mm clearance  |  1.42 mm overlap",
        safe=False,
    )
    _geometry_panel(
        frame,
        bounds=(1010, 215, 1830, 900),
        title="RIGHT  |  GUARDIAN YAW +67.5 deg",
        angle=22.5,
        color=GREEN,
        result="17.1 mm clearance  |  no overlap",
        safe=True,
    )
    _text(
        frame,
        "Illustration explains the measured geometry; the next shot is the real Genesis replay.",
        (170, 1000),
        scale=0.65,
        color=MUTED,
    )
    return frame


def _phase(index: int, count: int) -> str:
    ratio = index / max(count - 1, 1)
    if ratio < 0.12:
        return "SAME INITIAL STATE"
    if ratio < 0.56:
        return "APPROACH"
    if ratio < 0.78:
        return "GRASP"
    return "LIFT + VERIFY"


def _project_obstacle(
    obstacle_xyz: list[float],
    *,
    panel_width: int,
    panel_height: int,
) -> tuple[int, int]:
    position = np.asarray((0.35, -1.0, 1.20), dtype=float)
    lookat = np.asarray((0.35, 0.0, 0.80), dtype=float)
    point = np.asarray(obstacle_xyz, dtype=float)
    forward = lookat - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, np.asarray((0.0, 0.0, 1.0)))
    right /= np.linalg.norm(right)
    camera_up = np.cross(right, forward)
    relative = point - position
    depth = max(float(np.dot(relative, forward)), 1e-6)
    focal = panel_height / (2.0 * np.tan(np.deg2rad(42.0) / 2.0))
    x = panel_width / 2.0 + focal * float(np.dot(relative, right)) / depth
    y = panel_height / 2.0 - focal * float(np.dot(relative, camera_up)) / depth
    return int(x), int(y)


def _replay_frame(
    left: np.ndarray,
    right: np.ndarray,
    *,
    index: int,
    count: int,
    obstacle_xyz: list[float],
    contact_index: int,
    baseline_overlap_mm: float,
    guardian_clearance_mm: float,
    freeze: bool = False,
) -> np.ndarray:
    frame = _base()
    panel_size = (950, 534)
    left_scaled = cv2.resize(left, panel_size, interpolation=cv2.INTER_AREA)
    right_scaled = cv2.resize(right, panel_size, interpolation=cv2.INTER_AREA)
    frame[170:704, 0:950] = left_scaled
    frame[170:704, 970:1920] = right_scaled
    active = index >= contact_index
    border_left = RED if active else (92, 96, 108)
    cv2.rectangle(frame, (0, 170), (950, 704), border_left, 8)
    cv2.rectangle(frame, (970, 170), (1919, 704), GREEN, 8)

    _text(frame, "AEGIS MOTION  /  GUARDIANSIM", (35, 48), scale=0.73, color=RED, thickness=3)
    _text(frame, "VERIFIED GATE 3.2 VISUAL REPLAY", (35, 92), scale=0.94, thickness=3)
    _text(frame, "seed 411  |  lemon + plum clutter", (36, 128), scale=0.60, color=MUTED)
    phase = "CONTACT FRAME: PAUSED" if freeze else _phase(index, count)
    phase_width = cv2.getTextSize(phase, cv2.FONT_HERSHEY_SIMPLEX, 0.76, 3)[0][0]
    _text(frame, phase, (WIDTH - phase_width - 35, 72), scale=0.76, color=AMBER, thickness=3)

    cv2.rectangle(frame, (0, 704), (950, 1020), PANEL, -1)
    cv2.rectangle(frame, (970, 704), (1920, 1020), PANEL, -1)
    cv2.rectangle(frame, (0, 704), (950, 1020), RED, 4)
    cv2.rectangle(frame, (970, 704), (1919, 1020), GREEN, 4)
    _text(frame, "LEFT  |  NOMINAL BASELINE", (35, 758), scale=0.82, color=RED, thickness=3)
    _text(frame, "CONTACT / COLLISION", (35, 840), scale=1.18, color=RED, thickness=4)
    _text(
        frame,
        f"clearance 0.0 mm  |  measured overlap {baseline_overlap_mm:.2f} mm",
        (35, 894),
        scale=0.66,
    )
    _text(frame, "yaw 0 deg  |  direct approach", (35, 943), scale=0.60, color=MUTED)
    _text(frame, "RIGHT  |  GUARDIANSIM", (1005, 758), scale=0.82, color=GREEN, thickness=3)
    _text(frame, "SAFE CLEARANCE", (1005, 840), scale=1.18, color=GREEN, thickness=4)
    _text(
        frame,
        f"clearance {guardian_clearance_mm:.1f} mm  |  no overlap",
        (1005, 894),
        scale=0.66,
    )
    _text(frame, "yaw +67.5 deg  |  raised approach", (1005, 943), scale=0.60, color=MUTED)

    obstacle = _project_obstacle(
        obstacle_xyz,
        panel_width=1280,
        panel_height=720,
    )
    obstacle_scaled = (
        int(obstacle[0] * panel_size[0] / 1280),
        170 + int(obstacle[1] * panel_size[1] / 720),
    )
    for x_offset, color in ((0, RED), (970, GREEN)):
        center = (x_offset + obstacle_scaled[0], obstacle_scaled[1])
        cv2.circle(frame, center, 44 if active else 32, color, 6, cv2.LINE_AA)
        if active:
            label = "MEASURED CONTACT" if x_offset == 0 else "MEASURED CLEARANCE"
            label_x = max(x_offset + 30, min(center[0] + 55, x_offset + 650))
            _text(frame, label, (label_x, center[1] - 50), scale=0.55, color=color, thickness=3)
            cv2.arrowedLine(
                frame,
                (label_x, center[1] - 35),
                (center[0] + 20, center[1] - 15),
                color,
                4,
                cv2.LINE_AA,
                tipLength=0.18,
            )
    progress = int((index + 1) / count * (WIDTH - 70))
    cv2.rectangle(frame, (35, 1044), (WIDTH - 35, 1058), (52, 56, 66), -1)
    cv2.rectangle(frame, (35, 1044), (35 + progress, 1058), AMBER, -1)
    return frame


def _result_card() -> np.ndarray:
    frame = _base()
    _accent(frame)
    _text(frame, "VERIFIED RESULT", (100, 115), scale=1.45, thickness=4)
    _text(frame, "One replay for clarity. Thirty scenarios for the claim.", (102, 164), scale=0.72, color=MUTED)
    cv2.rectangle(frame, (95, 235), (900, 865), PANEL, -1)
    cv2.rectangle(frame, (95, 235), (900, 865), AMBER, 4)
    _text(frame, "THIS REPLAY  |  SEED 411", (140, 300), scale=0.82, color=AMBER, thickness=3)
    _text(frame, "NOMINAL", (145, 395), scale=0.68, color=RED, thickness=3)
    _text(frame, "1.42 mm OVERLAP", (145, 455), scale=1.15, color=RED, thickness=4)
    _text(frame, "GUARDIANSIM", (145, 570), scale=0.68, color=GREEN, thickness=3)
    _text(frame, "17.1 mm CLEARANCE", (145, 630), scale=1.15, color=GREEN, thickness=4)
    _text(frame, "Decision: unsafe nominal replaced", (145, 750), scale=0.68, color=WHITE)
    _text(frame, "Formal episode: baseline 0/3 safe, Guardian 3/3 safe", (145, 804), scale=0.57, color=MUTED)

    cv2.rectangle(frame, (1000, 235), (1825, 865), PANEL, -1)
    cv2.rectangle(frame, (1000, 235), (1825, 865), GREEN, 4)
    _text(frame, "FORMAL GATE 3.2  |  30 SCENARIOS", (1045, 300), scale=0.82, color=GREEN, thickness=3)
    rows = [
        ("Repeatable safe completion", "18/30", "30/30"),
        ("Independent safe executions", "58/90", "90/90"),
        ("Clutter contacts", "30", "0"),
        ("Mean clearance", "23.191 mm", "46.003 mm"),
    ]
    y = 405
    for label, before, after in rows:
        _text(frame, label, (1045, y), scale=0.57, color=MUTED)
        _text(frame, before, (1455, y), scale=0.64, color=RED, thickness=3)
        _text(frame, "->", (1580, y), scale=0.64, color=WHITE, thickness=2)
        _text(frame, after, (1640, y), scale=0.64, color=GREEN, thickness=3)
        y += 105
    _text(
        frame,
        "Genesis simulation on AMD Radeon Cloud  |  not a physical-robot claim",
        (235, 985),
        scale=0.67,
        color=MUTED,
    )
    return frame


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-video",
        default="docs/demo/gate-3-2-seed-411.mp4",
    )
    parser.add_argument(
        "--source-sidecar",
        default="docs/demo/gate-3-2-seed-411.json",
    )
    parser.add_argument(
        "--formal-report",
        default="docs/evidence/gate-3-2/formal-report.json",
    )
    parser.add_argument(
        "--output",
        default="docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4",
    )
    parser.add_argument("--fps", type=int, default=20)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.fps < 1:
        raise ValueError("--fps must be positive")
    source_path = Path(args.source_video)
    sidecar_path = Path(args.source_sidecar)
    formal_path = Path(args.formal_report)
    output_path = Path(args.output)
    replay = json.loads(sidecar_path.read_text(encoding="utf-8"))
    formal = json.loads(formal_path.read_text(encoding="utf-8"))
    episode = next(item for item in formal["episodes"] if item["seed"] == replay["seed"])
    left, right = _read_source_frames(source_path)
    baseline = replay["visual_replay"]["baseline"]
    guardian = replay["visual_replay"]["guardiansim"]
    baseline_overlap_mm = (
        baseline["metrics"]["clearance_diagnostic"]["overlap_depth_m"] * 1000.0
    )
    guardian_clearance_mm = guardian["metrics"]["collision_margin_m"] * 1000.0
    contact_index = min(
        len(left) - 1,
        baseline["metrics"]["clearance_diagnostic"]["step_index"]
        // SOURCE_CAPTURE_EVERY,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_card = _result_card()
    output_frame_count = 0
    with imageio.get_writer(
        output_path,
        format="ffmpeg",
        mode="I",
        fps=args.fps,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=2,
    ) as writer:
        def emit(frame: np.ndarray, count: int = 1) -> None:
            nonlocal output_frame_count
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            for _ in range(count):
                writer.append_data(rgb)
                output_frame_count += 1

        emit(_title_card(), args.fps * 2)
        emit(_geometry_card(), args.fps * 3)
        emit(
            _replay_frame(
                left[0],
                right[0],
                index=0,
                count=len(left),
                obstacle_xyz=episode["obstacle_xyz"],
                contact_index=contact_index,
                baseline_overlap_mm=baseline_overlap_mm,
                guardian_clearance_mm=guardian_clearance_mm,
            ),
            args.fps,
        )
        for index, (left_frame, right_frame) in enumerate(zip(left, right)):
            rendered = _replay_frame(
                left_frame,
                right_frame,
                index=index,
                count=len(left),
                obstacle_xyz=episode["obstacle_xyz"],
                contact_index=contact_index,
                baseline_overlap_mm=baseline_overlap_mm,
                guardian_clearance_mm=guardian_clearance_mm,
            )
            emit(rendered)
            if index == contact_index:
                emit(
                    _replay_frame(
                        left_frame,
                        right_frame,
                        index=index,
                        count=len(left),
                        obstacle_xyz=episode["obstacle_xyz"],
                        contact_index=contact_index,
                        baseline_overlap_mm=baseline_overlap_mm,
                        guardian_clearance_mm=guardian_clearance_mm,
                        freeze=True,
                    ),
                    args.fps * 2,
                )
        emit(final_card, args.fps * 4)

    preview_path = output_path.with_name(output_path.stem + "-preview.png")
    cv2.imwrite(str(preview_path), final_card)
    presentation = {
        "kind": "gate32_aegis_motion_showcase_from_verified_replay",
        "physics_reexecuted": False,
        "statistical_trial_added": False,
        "seed": replay["seed"],
        "scenario_id": replay["scenario_id"],
        "source_video": str(source_path),
        "source_video_sha256": _sha256(source_path),
        "source_sidecar": str(sidecar_path),
        "source_sidecar_sha256": _sha256(sidecar_path),
        "formal_report": str(formal_path),
        "formal_report_sha256": _sha256(formal_path),
        "output_video": str(output_path),
        "output_video_sha256": _sha256(output_path),
        "preview": str(preview_path),
        "preview_sha256": _sha256(preview_path),
        "output_width": WIDTH,
        "output_height": HEIGHT,
        "output_fps": args.fps,
        "output_frame_count": output_frame_count,
        "duration_seconds": output_frame_count / args.fps,
        "contact_frame_index": contact_index,
        "baseline_overlap_mm": baseline_overlap_mm,
        "guardian_clearance_mm": guardian_clearance_mm,
        "formal_baseline_contacts": episode["baseline"]["aggregate"][
            "clutter_contact_count"
        ],
        "formal_guardian_safe_executions": episode["guardiansim"]["aggregate"][
            "safe_completion_count"
        ],
    }
    presentation_path = output_path.with_suffix(".json")
    presentation_path.write_text(
        json.dumps(presentation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(presentation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
