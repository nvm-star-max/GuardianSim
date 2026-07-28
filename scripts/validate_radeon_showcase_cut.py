#!/usr/bin/env python3
"""Strictly validate the GuardianSim scale-first visual review cut."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import cv2
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SIDECAR = (
    ROOT
    / "docs/submission/GuardianSim-Radeon-Parallel-Futures-review-v3.json"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(sidecar: Path = DEFAULT_SIDECAR) -> dict:
    payload = json.loads(sidecar.read_text())
    require(
        payload["kind"] == "guardiansim_radeon_parallel_futures_visual_review_v3",
        "Unexpected review kind",
    )
    require(payload["team"] == "Aegis Motion", "Unexpected team")
    require(payload["project"] == "GuardianSim", "Unexpected project")
    require("not independent safety scenes" in payload["claim_boundary"], "Missing scale boundary")
    require("no physical-robot claim" in payload["claim_boundary"], "Missing simulation boundary")
    layout = payload["layout_policy"]
    require(
        layout["metric_rows"]
        == "measured as one group and centered inside each card",
        "Metric-row centering policy drift",
    )
    require(layout["overflow_asserted_during_render"] is True, "Missing overflow assertion")

    output = payload["output"]
    output_path = ROOT / output["path"]
    require(output_path.is_file(), "Missing output video")
    require(sha256(output_path) == output["sha256"], "Output SHA-256 mismatch")
    require(output["audio"] is False, "Review cut must remain explicitly silent")

    capture = cv2.VideoCapture(str(output_path))
    require(capture.isOpened(), "Could not open output video")
    frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    decoded = 0
    for fraction in (0.0, 0.08, 0.2, 0.4, 0.55, 0.72, 0.9, 0.99):
        capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(frames * fraction) - 1))
        ok, frame = capture.read()
        require(ok and frame is not None and frame.size > 0, f"Decode failed at {fraction}")
        decoded += 1
    capture.release()

    duration = frames / fps
    require(width == 1920 and height == 1080, "Output must be 1920x1080")
    require(abs(fps - 20.0) < 0.01, "Output must be 20 FPS")
    require(79.9 <= duration <= 80.1, "Output duration drift")
    require(abs(duration - output["duration_seconds"]) < 0.1, "Sidecar duration drift")

    for source in payload["sources"].values():
        source_path = ROOT / source["path"]
        require(source_path.is_file(), f"Missing source {source_path}")
        require(sha256(source_path) == source["sha256"], f"Source hash mismatch: {source_path}")

    metrics = payload["verified_metrics"]
    require(metrics["largest_parallel_batch"] == 256, "Batch claim drift")
    require(metrics["environment_steps_per_second"] == 35166, "Throughput claim drift")
    require(metrics["speedup_vs_single_world"] == 228.16, "Speedup claim drift")
    require(metrics["total_measured_environment_steps"] == 337000, "Workload claim drift")
    require(metrics["parallel_future_worlds"] == 54, "Future count drift")
    require(metrics["parallel_future_hard_safe"] == 32, "Safe future count drift")
    require(metrics["parallel_future_rejected"] == 22, "Rejected future count drift")
    require(
        metrics["formal_repeatable_safe_scenarios"]
        == {"baseline": 18, "guardiansim": 30, "total": 30},
        "Formal safety claim drift",
    )
    require(len(payload["chapters"]) == 6, "Chapter count drift")
    require(payload["chapters"][0]["start"] == 0, "Chapter start drift")
    require(payload["chapters"][-1]["end"] == 80, "Chapter end drift")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    full_decode = subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-i",
            str(output_path),
            "-map",
            "0:v:0",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    require(full_decode.returncode == 0, f"Full video decode failed: {full_decode.stderr}")

    return {
        "validated": True,
        "video": output["path"],
        "sha256": output["sha256"],
        "duration_seconds": duration,
        "fps": fps,
        "width": width,
        "height": height,
        "decoded_sample_count": decoded,
        "full_video_decode": True,
        "source_hashes_verified": True,
        "claim_boundaries_verified": True,
        "verified_metrics_locked": True,
        "audio": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sidecar", nargs="?", type=Path, default=DEFAULT_SIDECAR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.sidecar.resolve())
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
