#!/usr/bin/env python3
"""Strictly validate the GuardianSim narrated submission-video review cut."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def resolve_recorded_path(record: dict, key: str = "path") -> Path:
    path = ROOT / record[key]
    require(path.is_file(), f"Missing recorded source: {path}")
    return path


def validate(sidecar_path: Path) -> dict:
    payload = json.loads(sidecar_path.read_text())
    require(
        payload.get("kind") == "guardiansim_submission_video_review_v1",
        "Unexpected presentation kind",
    )
    require(payload.get("team") == "Aegis Motion", "Unexpected team identity")
    require(payload.get("project") == "GuardianSim", "Unexpected project identity")
    require("no Genesis physics re-execution" in payload["claim_boundary"], "Missing no-rerun boundary")
    require("Simulation only" in payload["claim_boundary"], "Missing simulation-only boundary")

    output_record = payload["output"]
    output_path = resolve_recorded_path(output_record)
    require(sha256(output_path) == output_record["sha256"], "Output SHA-256 mismatch")

    capture = cv2.VideoCapture(str(output_path))
    require(capture.isOpened(), "Could not open output video")
    frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    decoded_samples = 0
    for fraction in (0.0, 0.15, 0.33, 0.5, 0.67, 0.84, 0.99):
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frames * fraction) - 1))
        ok, frame = capture.read()
        require(ok and frame is not None and frame.size > 0, f"Decode failed at {fraction}")
        decoded_samples += 1
    capture.release()
    duration = frames / fps
    require(width == 1920 and height == 1080, "Output must be 1920x1080")
    require(fps >= 20.0, "Output must be at least 20 FPS")
    require(180.0 <= duration <= 300.0, "Output must be between 3 and 5 minutes")
    require(abs(duration - output_record["duration_seconds"]) < 0.1, "Recorded duration drift")

    sources = payload["sources"]
    for key in ("hero_video", "gate32_formal_report", "gate33_engineering_report", "smoke_candidates"):
        record = sources[key]
        require(sha256(resolve_recorded_path(record)) == record["sha256"], f"{key} SHA-256 mismatch")
    require(sources["hero_video"]["validated"] is True, "Hero replay must be validated")
    require(sources["gate32_formal_report"]["schema_version"] == 5, "Gate 3.2 schema drift")
    require(sources["gate32_formal_report"]["completed_episode_count"] == 30, "Gate 3.2 count drift")
    require(sources["gate33_engineering_report"]["schema_version"] == 6, "Gate 3.3 schema drift")
    require(sources["gate33_engineering_report"]["completed_episode_count"] == 12, "Gate 3.3 count drift")
    require(sources["smoke_candidates"]["candidate_count"] == 3, "Smoke candidate count drift")

    metrics = payload["verified_metrics"]
    require(
        metrics["gate32_repeatable_safe_completion"]
        == {"baseline": 18, "guardiansim": 30, "total": 30},
        "Repeatable completion claim drift",
    )
    require(
        metrics["gate32_independent_safe_executions"]
        == {"baseline": 58, "guardiansim": 90, "total": 90},
        "Independent execution claim drift",
    )
    require(
        metrics["gate32_clutter_contact_executions"] == {"baseline": 30, "guardiansim": 0},
        "Contact claim drift",
    )
    require(metrics["gate33_gap_bearing"]["label"] == "engineering breadth evidence", "Gate 3.3 label drift")
    require(metrics["gate33_gap_bearing"]["unsafe_executions"] == 0, "Safe-stop claim drift")
    require(len(payload["narration"]["segments"]) == 8, "Expected eight narrated sections")
    require(payload["narration"]["human_narration_recommended_for_final"] is True, "Review status drift")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    decode = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(output_path),
            "-map",
            "0:v:0",
            "-map",
            "0:a:0",
            "-f",
            "null",
            "-",
        ],
        text=True,
        capture_output=True,
    )
    require(decode.returncode == 0, f"Full A/V decode failed: {decode.stderr}")

    return {
        "validated": True,
        "kind": payload["kind"],
        "video": str(output_path.relative_to(ROOT)),
        "sha256": output_record["sha256"],
        "duration_seconds": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "decoded_sample_count": decoded_samples,
        "full_audio_video_decode": True,
        "source_hashes_verified": True,
        "formal_claims_verified": True,
        "claim_boundary_verified": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sidecar",
        nargs="?",
        type=Path,
        default=ROOT / "docs/submission/GuardianSim-Aegis-Motion-demo-review-v1.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.sidecar.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
