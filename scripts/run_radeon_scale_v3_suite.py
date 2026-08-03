#!/usr/bin/env python3
"""Run or resume the frozen no-overwrite Radeon Scale V3 endurance suite."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import sha256_file
from guardian_sim.radeon_scale_v3 import (
    RADEON_SCALE_V3_BATCH_SIZES,
    RADEON_SCALE_V3_REPEATS_PER_BATCH,
    assemble_scale_v3_report,
    build_scale_v3_protocol,
    validate_scale_v3_protocol,
    validate_scale_v3_report,
)
from guardian_sim.radeon_scale_v2 import validate_scale_v2_trial
from scripts.run_radeon_scale_v2_suite import (
    command_output,
    current_head,
    ensure_output_dir,
    require_tracked_source_clean,
    verify_checksums,
    write_checksums,
    write_json_exclusive,
    write_text_exclusive,
)

TRIAL_SCRIPT = ROOT / "scripts" / "run_radeon_scale_v2_trial.py"
SUITE_SCRIPT = Path(__file__).resolve()
SCENE_SOURCE = ROOT / "franka_fruit_pick" / "build_scene.py"
SCENE_CONFIG = ROOT / "franka_fruit_pick" / "scene_config.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser


def protocol_for_current_source() -> dict[str, object]:
    return build_scale_v3_protocol(
        scene_source_sha256=sha256_file(SCENE_SOURCE),
        scene_config_sha256=sha256_file(SCENE_CONFIG),
        trial_runner_sha256=sha256_file(TRIAL_SCRIPT),
        suite_runner_sha256=sha256_file(SUITE_SCRIPT),
    )


def next_attempt_log(output_dir: Path, n_envs: int, repeat_index: int) -> Path:
    attempt = 1
    while True:
        path = output_dir / (
            f"trial-{n_envs:05d}-repeat-{repeat_index:02d}-attempt-{attempt:02d}.log"
        )
        if not path.exists():
            return path
        attempt += 1


def write_source_receipt(output_dir: Path, command: list[str]) -> None:
    write_text_exclusive(output_dir / "source-head.txt", current_head() + "\n")
    write_text_exclusive(
        output_dir / "source-commit.txt",
        command_output(["git", "show", "--no-patch", "--format=fuller", "HEAD"]),
    )
    write_text_exclusive(
        output_dir / "git-status.txt",
        command_output(["git", "status", "--porcelain=v1", "--branch"]),
    )
    write_text_exclusive(output_dir / "launch-command.txt", shlex.join(command) + "\n")
    write_text_exclusive(output_dir / "rocm-smi-before.txt", command_output(["rocm-smi"]))


def finalize_run(
    output_dir: Path,
    report: dict[str, object],
    validation: dict[str, object],
) -> None:
    validation_path = output_dir / "validation.json"
    rocm_after_path = output_dir / "rocm-smi-after.txt"
    completed_state_path = output_dir / "run-state-completed.json"
    checksums_path = output_dir / "SHA256SUMS"

    if checksums_path.exists():
        verify_checksums(output_dir)
        for required_path in (
            validation_path,
            rocm_after_path,
            completed_state_path,
        ):
            if not required_path.exists():
                raise ValueError(
                    f"sealed evidence is missing required file: {required_path.name}"
                )
        existing_validation = json.loads(validation_path.read_text(encoding="utf-8"))
        if existing_validation != validation:
            raise ValueError("existing validation receipt does not match the report")
        return

    if validation_path.exists():
        existing_validation = json.loads(validation_path.read_text(encoding="utf-8"))
        if existing_validation != validation:
            raise ValueError("existing validation receipt does not match the report")
    else:
        write_json_exclusive(validation_path, validation)

    if not rocm_after_path.exists():
        write_text_exclusive(rocm_after_path, command_output(["rocm-smi"]))

    if not completed_state_path.exists():
        prior_state = json.loads(
            (output_dir / "run-state.json").read_text(encoding="utf-8")
        )
        write_json_exclusive(
            completed_state_path,
            {
                **prior_state,
                "status": "passed",
                "finished_at_utc": datetime.now(UTC).isoformat(),
                "completed_measurements": len(report["measurements"]),
                "report_sha256": report["report_sha256"],
            },
        )

    write_checksums(output_dir)
    verify_checksums(output_dir)


def main() -> None:
    args = build_parser().parse_args()
    output_dir = args.output_dir.resolve()
    require_tracked_source_clean()
    ensure_output_dir(output_dir, args.resume)
    expected_protocol = protocol_for_current_source()
    protocol_path = output_dir / "protocol.json"
    trial_protocol_path = output_dir / "trial-protocol.json"

    if args.resume:
        if (output_dir / "source-head.txt").read_text(encoding="utf-8").strip() != current_head():
            raise ValueError("current Git commit does not match the frozen V3 run")
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        validate_scale_v3_protocol(protocol, require_frozen_formal=True)
        if protocol != expected_protocol:
            raise ValueError("current source does not match the frozen V3 protocol")
    else:
        protocol = expected_protocol
        validate_scale_v3_protocol(protocol, require_frozen_formal=True)
        write_json_exclusive(protocol_path, protocol)
        write_json_exclusive(trial_protocol_path, protocol["trial_protocol"])
        write_source_receipt(output_dir, [sys.executable, *sys.argv])
        write_json_exclusive(
            output_dir / "run-state.json",
            {
                "status": "running",
                "started_at_utc": datetime.now(UTC).isoformat(),
                "protocol_sha256": protocol["protocol_sha256"],
                "expected_measurements": len(RADEON_SCALE_V3_BATCH_SIZES)
                * RADEON_SCALE_V3_REPEATS_PER_BATCH,
            },
        )

    report_path = output_dir / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        validation = validate_scale_v3_report(report)
        finalize_run(output_dir, report, validation)
        print(json.dumps({"report": str(report_path), **validation}, indent=2))
        return

    measurements: list[dict[str, object]] = []
    trial_protocol = protocol["trial_protocol"]
    for n_envs in RADEON_SCALE_V3_BATCH_SIZES:
        for repeat_index in range(1, RADEON_SCALE_V3_REPEATS_PER_BATCH + 1):
            trial_path = output_dir / f"trial-{n_envs:05d}-repeat-{repeat_index:02d}.json"
            if trial_path.exists():
                trial = json.loads(trial_path.read_text(encoding="utf-8"))
                validate_scale_v2_trial(trial, trial_protocol, require_telemetry=True)
            else:
                log_path = next_attempt_log(output_dir, n_envs, repeat_index)
                command = [
                    sys.executable,
                    str(TRIAL_SCRIPT),
                    "--protocol",
                    str(trial_protocol_path),
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
                    raise RuntimeError(
                        f"batch {n_envs} repeat {repeat_index} failed with exit code "
                        f"{result.returncode}; evidence preserved in {log_path}"
                    )
                trial = json.loads(trial_path.read_text(encoding="utf-8"))
                validate_scale_v2_trial(trial, trial_protocol, require_telemetry=True)
            measurements.append(
                {"n_envs": n_envs, "repeat_index": repeat_index, "trial": trial}
            )

    report = assemble_scale_v3_report(protocol, measurements)
    validation = validate_scale_v3_report(report)
    write_json_exclusive(report_path, report)
    finalize_run(output_dir, report, validation)
    print(json.dumps({"report": str(report_path), **validation}, indent=2))


if __name__ == "__main__":
    main()
