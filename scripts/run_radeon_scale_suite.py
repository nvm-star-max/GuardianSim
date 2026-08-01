#!/usr/bin/env python3
"""Run isolated Radeon scaling trials and assemble one strict evidence report."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import (
    RADEON_SCALE_DEFAULT_BATCH_SIZES,
    RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS,
    RADEON_SCALE_DEFAULT_WARMUP_STEPS,
    assemble_scale_report,
    build_scale_protocol,
    sha256_file,
    validate_scale_report,
)

TRIAL_SCRIPT = ROOT / "scripts" / "run_radeon_scale_trial.py"
SCENE_SOURCE = ROOT / "franka_fruit_pick" / "build_scene.py"
SCENE_CONFIG = ROOT / "franka_fruit_pick" / "scene_config.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        default=list(RADEON_SCALE_DEFAULT_BATCH_SIZES),
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=RADEON_SCALE_DEFAULT_WARMUP_STEPS,
    )
    parser.add_argument(
        "--measurement-steps",
        type=int,
        default=RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS,
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/radeon-scale"),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    protocol = build_scale_protocol(
        batch_sizes=args.batch_sizes,
        warmup_steps=args.warmup_steps,
        measurement_steps=args.measurement_steps,
        scene_source_sha256=sha256_file(SCENE_SOURCE),
        scene_config_sha256=sha256_file(SCENE_CONFIG),
    )
    protocol_path = output_dir / "protocol.json"
    protocol_path.write_text(json.dumps(protocol, indent=2) + "\n", encoding="utf-8")

    trials: list[dict[str, object]] = []
    for n_envs in args.batch_sizes:
        trial_path = output_dir / f"trial-{n_envs:04d}.json"
        log_path = output_dir / f"trial-{n_envs:04d}.log"
        command = [
            sys.executable,
            str(TRIAL_SCRIPT),
            "--n-envs",
            str(n_envs),
            "--batch-sizes",
            *(str(value) for value in args.batch_sizes),
            "--warmup-steps",
            str(args.warmup_steps),
            "--measurement-steps",
            str(args.measurement_steps),
            "--output",
            str(trial_path),
        ]
        with log_path.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
        if result.returncode != 0:
            raise RuntimeError(
                f"batch {n_envs} failed with exit code {result.returncode}; "
                f"inspect {log_path}"
            )
        trials.append(json.loads(trial_path.read_text(encoding="utf-8")))

    report = assemble_scale_report(protocol, trials)
    validation = validate_scale_report(report, require_telemetry=True)
    report_path = output_dir / "report.json"
    validation_path = output_dir / "validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    validation_path.write_text(
        json.dumps(validation, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"report": str(report_path), **validation}, indent=2))


if __name__ == "__main__":
    main()
