#!/usr/bin/env python3
"""Probe V2 scene capacity without producing performance evidence."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import sha256_file
from guardian_sim.radeon_scale_v2 import (
    build_scale_v2_protocol,
    validate_scale_v2_trial,
)

TRIAL_SCRIPT = ROOT / "scripts" / "run_radeon_scale_v2_trial.py"
SCENE_SOURCE = ROOT / "franka_fruit_pick" / "build_scene.py"
SCENE_CONFIG = ROOT / "franka_fruit_pick" / "scene_config.py"
PREFLIGHT_BATCH_SIZES = (1, 512, 1024, 2048, 4096)
PREFLIGHT_TARGETS = PREFLIGHT_BATCH_SIZES[1:]
PREFLIGHT_WARMUP_STEPS = 5
PREFLIGHT_MEASUREMENT_STEPS = 10


def write_json_exclusive(path: Path, payload: object) -> None:
    with path.open("x", encoding="utf-8") as target:
        target.write(json.dumps(payload, indent=2) + "\n")


def next_attempt_log(output_dir: Path, n_envs: int) -> Path:
    attempt = 1
    while True:
        path = output_dir / f"capacity-{n_envs:04d}-attempt-{attempt:02d}.log"
        if not path.exists():
            return path
        attempt += 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    protocol = build_scale_v2_protocol(
        batch_sizes=PREFLIGHT_BATCH_SIZES,
        warmup_steps=PREFLIGHT_WARMUP_STEPS,
        measurement_steps=PREFLIGHT_MEASUREMENT_STEPS,
        scene_source_sha256=sha256_file(SCENE_SOURCE),
        scene_config_sha256=sha256_file(SCENE_CONFIG),
        trial_runner_sha256=sha256_file(TRIAL_SCRIPT),
    )
    protocol_path = output_dir / "preflight-protocol.json"
    write_json_exclusive(protocol_path, protocol)

    passed: list[int] = []
    failed: int | None = None
    for n_envs in PREFLIGHT_TARGETS:
        trial_path = output_dir / f"capacity-{n_envs:04d}.json"
        log_path = next_attempt_log(output_dir, n_envs)
        command = [
            sys.executable,
            str(TRIAL_SCRIPT),
            "--protocol",
            str(protocol_path),
            "--n-envs",
            str(n_envs),
            "--output",
            str(trial_path),
        ]
        with log_path.open("x", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode != 0:
            failed = n_envs
            break
        trial = json.loads(trial_path.read_text(encoding="utf-8"))
        validate_scale_v2_trial(trial, protocol, require_telemetry=False)
        passed.append(n_envs)

    summary = {
        "status": "passed" if failed is None else "capacity_limit_detected",
        "evidence_scope": (
            "Capacity preflight only. Short runs are not performance evidence "
            "and must not be merged into the formal report."
        ),
        "finished_at_utc": datetime.now(UTC).isoformat(),
        "protocol_sha256": protocol["protocol_sha256"],
        "passed_batch_sizes": passed,
        "failed_batch_size": failed,
        "formal_target_supported": failed is None and passed[-1:] == [4096],
    }
    write_json_exclusive(output_dir / "preflight-summary.json", summary)
    print(json.dumps(summary, indent=2))
    if failed is not None:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
