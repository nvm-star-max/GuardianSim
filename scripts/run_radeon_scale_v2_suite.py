#!/usr/bin/env python3
"""Run or resume the frozen, no-overwrite Radeon Scale V2 evidence suite."""

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
from guardian_sim.radeon_scale_v2 import (
    RADEON_SCALE_V2_BATCH_SIZES,
    assemble_scale_v2_report,
    build_scale_v2_protocol,
    validate_scale_v2_protocol,
    validate_scale_v2_report,
    validate_scale_v2_trial,
)

TRIAL_SCRIPT = ROOT / "scripts" / "run_radeon_scale_v2_trial.py"
SCENE_SOURCE = ROOT / "franka_fruit_pick" / "build_scene.py"
SCENE_CONFIG = ROOT / "franka_fruit_pick" / "scene_config.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume only from raw trials that strictly match this exact protocol.",
    )
    return parser


def write_text_exclusive(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as target:
        target.write(content)


def write_json_exclusive(path: Path, payload: object) -> None:
    write_text_exclusive(path, json.dumps(payload, indent=2) + "\n")


def command_output(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.stdout


def current_head() -> str:
    return command_output(["git", "rev-parse", "HEAD"]).strip()


def require_tracked_source_clean() -> None:
    for command in (
        ["git", "diff", "--quiet"],
        ["git", "diff", "--cached", "--quiet"],
    ):
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            raise RuntimeError("tracked source must be clean before a formal run")


def next_attempt_log(output_dir: Path, n_envs: int) -> Path:
    attempt = 1
    while True:
        path = output_dir / f"trial-{n_envs:04d}-attempt-{attempt:02d}.log"
        if not path.exists():
            return path
        attempt += 1


def protocol_for_current_source() -> dict[str, object]:
    return build_scale_v2_protocol(
        scene_source_sha256=sha256_file(SCENE_SOURCE),
        scene_config_sha256=sha256_file(SCENE_CONFIG),
        trial_runner_sha256=sha256_file(TRIAL_SCRIPT),
    )


def ensure_output_dir(output_dir: Path, resume: bool) -> None:
    if resume:
        if not output_dir.is_dir():
            raise FileNotFoundError("--resume requires an existing output directory")
        return
    output_dir.mkdir(parents=True, exist_ok=False)


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
    write_text_exclusive(
        output_dir / "launch-command.txt",
        shlex.join(command) + "\n",
    )
    write_text_exclusive(
        output_dir / "rocm-smi-before.txt",
        command_output(["rocm-smi"]),
    )


def write_checksums(output_dir: Path) -> None:
    paths = sorted(
        path for path in output_dir.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    )
    lines = [f"{sha256_file(path)}  {path.name}" for path in paths]
    write_text_exclusive(output_dir / "SHA256SUMS", "\n".join(lines) + "\n")


def verify_checksums(output_dir: Path) -> None:
    manifest_path = output_dir / "SHA256SUMS"
    declared: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        digest, separator, name = line.partition("  ")
        if not separator or name in declared:
            raise ValueError("invalid or duplicate SHA256SUMS entry")
        declared[name] = digest
    expected_names = {
        path.name
        for path in output_dir.iterdir()
        if path.is_file() and path.name != "SHA256SUMS"
    }
    if set(declared) != expected_names:
        raise ValueError("SHA256SUMS does not cover the exact evidence file set")
    for name, digest in declared.items():
        if sha256_file(output_dir / name) != digest:
            raise ValueError(f"checksum mismatch: {name}")


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
                "completed_batch_sizes": list(RADEON_SCALE_V2_BATCH_SIZES),
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

    if args.resume:
        recorded_head = (output_dir / "source-head.txt").read_text(
            encoding="utf-8"
        ).strip()
        if recorded_head != current_head():
            raise ValueError("current Git commit does not match the frozen run")
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        validate_scale_v2_protocol(protocol, require_frozen_formal=True)
        if protocol != expected_protocol:
            raise ValueError(
                "current source does not match the frozen protocol; refusing resume"
            )
    else:
        protocol = expected_protocol
        validate_scale_v2_protocol(protocol, require_frozen_formal=True)
        write_json_exclusive(protocol_path, protocol)
        write_source_receipt(output_dir, [sys.executable, *sys.argv])
        write_json_exclusive(
            output_dir / "run-state.json",
            {
                "status": "running",
                "started_at_utc": datetime.now(UTC).isoformat(),
                "protocol_sha256": protocol["protocol_sha256"],
                "completed_batch_sizes": [],
            },
        )

    report_path = output_dir / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        validation = validate_scale_v2_report(report)
        finalize_run(output_dir, report, validation)
        print(json.dumps({"report": str(report_path), **validation}, indent=2))
        return

    trials: list[dict[str, object]] = []
    for n_envs in RADEON_SCALE_V2_BATCH_SIZES:
        trial_path = output_dir / f"trial-{n_envs:04d}.json"
        if trial_path.exists():
            trial = json.loads(trial_path.read_text(encoding="utf-8"))
            validate_scale_v2_trial(trial, protocol, require_telemetry=True)
            trials.append(trial)
            continue

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
            raise RuntimeError(
                f"batch {n_envs} failed with exit code {result.returncode}; "
                f"evidence preserved in {log_path}"
            )
        trial = json.loads(trial_path.read_text(encoding="utf-8"))
        validate_scale_v2_trial(trial, protocol, require_telemetry=True)
        trials.append(trial)

    report = assemble_scale_v2_report(protocol, trials)
    validation = validate_scale_v2_report(report)
    write_json_exclusive(report_path, report)
    finalize_run(output_dir, report, validation)
    print(json.dumps({"report": str(report_path), **validation}, indent=2))


if __name__ == "__main__":
    main()
