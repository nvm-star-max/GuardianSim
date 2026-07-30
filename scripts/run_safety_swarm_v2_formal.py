#!/usr/bin/env python3
"""Run or resume the frozen 18-chunk Safety Swarm V2 Radeon formal gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm_v2 import (
    assemble_safety_swarm_v2_formal_report,
    validate_safety_swarm_v2_formal_chunk_report,
    validate_safety_swarm_v2_formal_report,
)


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return value


def _write_new_json(path: Path, payload: dict[str, object]) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _chunk_paths(
    output_dir: Path,
    chunk_index: int,
    attempt_index: int,
) -> dict[str, Path]:
    chunk_dir = (
        output_dir
        / "chunks"
        / f"chunk-{chunk_index:02d}"
        / f"attempt-{attempt_index:03d}"
    )
    return {
        "dir": chunk_dir,
        "report": chunk_dir / "report.json",
        "preflight": chunk_dir / "preflight.json",
        "validation": chunk_dir / "validation.json",
        "log": chunk_dir / "launch.log",
    }


def _load_or_run_chunk(
    *,
    output_dir: Path,
    chunk_index: int,
) -> dict[str, object]:
    chunk_root = output_dir / "chunks" / f"chunk-{chunk_index:02d}"
    existing_attempts = sorted(
        path
        for path in chunk_root.glob("attempt-*")
        if path.is_dir()
    )
    validated: list[dict[str, object]] = []
    for attempt_dir in existing_attempts:
        report_path = attempt_dir / "report.json"
        if not report_path.exists():
            continue
        report = _read_json(report_path)
        validation = validate_safety_swarm_v2_formal_chunk_report(
            report,
            require_radeon=True,
        )
        if int(validation["chunk_index"]) != chunk_index:
            raise ValueError("validated formal chunk index mismatch")
        validated.append(report)
    if len(validated) > 1:
        raise ValueError(
            f"chunk {chunk_index:02d} has multiple valid formal attempts"
        )
    if validated:
        print(
            f"VALIDATED_EXISTING chunk={chunk_index:02d} "
            f"sha256={validated[0]['report_sha256']}",
            flush=True,
        )
        return validated[0]

    attempt_index = len(existing_attempts) + 1
    paths = _chunk_paths(output_dir, chunk_index, attempt_index)
    paths["dir"].mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_safety_swarm_smoke.py"),
        "--v2-formal-chunk-index",
        str(chunk_index),
        "--output",
        str(paths["report"]),
        "--preflight-output",
        str(paths["preflight"]),
        "--validation-output",
        str(paths["validation"]),
    ]
    print(
        f"STARTING chunk={chunk_index:02d} attempt={attempt_index:03d}",
        flush=True,
    )
    with paths["log"].open("x", encoding="utf-8") as log:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
    if completed.returncode != 0:
        raise RuntimeError(
            f"formal chunk {chunk_index:02d} failed with exit "
            f"{completed.returncode}; preserve {paths['log']}"
        )
    report = _read_json(paths["report"])
    validation = validate_safety_swarm_v2_formal_chunk_report(
        report,
        require_radeon=True,
    )
    print(
        f"COMPLETED chunk={chunk_index:02d} "
        f"sha256={validation['report_sha256']}",
        flush=True,
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    final_report_path = args.output_dir / "formal-report.json"
    final_validation_path = args.output_dir / "formal-validation.json"
    if final_report_path.exists():
        report = _read_json(final_report_path)
        validation = validate_safety_swarm_v2_formal_report(
            report,
            require_radeon=True,
        )
        print(json.dumps(validation, indent=2))
        return
    if final_validation_path.exists():
        raise FileExistsError(
            "formal validation exists without a formal report; refusing overwrite"
        )

    chunks = [
        _load_or_run_chunk(output_dir=args.output_dir, chunk_index=index)
        for index in range(18)
    ]
    report = assemble_safety_swarm_v2_formal_report(chunks)
    validation = validate_safety_swarm_v2_formal_report(
        report,
        require_radeon=True,
    )
    _write_new_json(final_report_path, report)
    _write_new_json(final_validation_path, validation)
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
