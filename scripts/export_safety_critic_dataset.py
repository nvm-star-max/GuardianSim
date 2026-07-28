#!/usr/bin/env python3
"""Export the preserved GuardianSim rollouts as a scene-grouped JSONL dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_critic_data import (
    CRITIC_FEATURE_NAMES,
    CRITIC_TARGET_NAMES,
    extract_safety_critic_rows,
    split_rows_by_scene,
)

DEFAULT_GATE32 = ROOT / "docs" / "evidence" / "gate-3-2" / "formal-report.json"
DEFAULT_GATE33 = (
    ROOT
    / "docs"
    / "evidence"
    / "gate-3-3-two-strata"
    / "raw"
    / "two-strata-report.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate32", type=Path, default=DEFAULT_GATE32)
    parser.add_argument("--gate33", type=Path, default=DEFAULT_GATE33)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/safety-critic"),
    )
    args = parser.parse_args()

    gate32 = json.loads(args.gate32.read_text(encoding="utf-8"))
    gate33 = json.loads(args.gate33.read_text(encoding="utf-8"))
    rows = extract_safety_critic_rows(gate32, gate33)
    train, test = split_rows_by_scene(rows)
    split_by_identity = {
        (
            row.source_gate,
            row.seed,
            row.candidate_id,
            row.observation_index,
        ): "train"
        for row in train
    }
    split_by_identity.update(
        {
            (
                row.source_gate,
                row.seed,
                row.candidate_id,
                row.observation_index,
            ): "test"
            for row in test
        }
    )

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = output_dir / "rollouts.jsonl"
    with dataset_path.open("w", encoding="utf-8") as output:
        for row in rows:
            identity = (
                row.source_gate,
                row.seed,
                row.candidate_id,
                row.observation_index,
            )
            payload = row.as_dict()
            payload["split"] = split_by_identity[identity]
            output.write(json.dumps(payload, separators=(",", ":")) + "\n")

    manifest = {
        "schema_version": 1,
        "dataset_name": "GuardianSim Counterfactual Safety Critic",
        "claim_boundary": (
            "Rows are nested candidate rollouts from 42 scene units, not 1,185 "
            "independent robot scenes."
        ),
        "feature_names": list(CRITIC_FEATURE_NAMES),
        "target_names": list(CRITIC_TARGET_NAMES),
        "row_count": len(rows),
        "train_row_count": len(train),
        "test_row_count": len(test),
        "train_scene_count": len(
            {(row.source_gate, row.seed) for row in train}
        ),
        "test_scene_count": len(
            {(row.source_gate, row.seed) for row in test}
        ),
        "positive_hard_safe_count": sum(row.hard_safe for row in rows),
        "source_reports": {
            "gate32": {
                "path": str(args.gate32),
                "sha256": _sha256(args.gate32),
                "schema_version": gate32["schema_version"],
            },
            "gate33": {
                "path": str(args.gate33),
                "sha256": _sha256(args.gate33),
                "schema_version": gate33["schema_version"],
            },
        },
    }
    manifest["dataset_sha256"] = _sha256(dataset_path)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
