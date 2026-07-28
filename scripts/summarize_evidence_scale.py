#!/usr/bin/env python3
"""Print the preserved GuardianSim evidence at each statistical grain."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardian_sim.evidence_scale import summarize_preserved_evidence


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate32-report",
        default="docs/evidence/gate-3-2/formal-report.json",
    )
    parser.add_argument(
        "--gate33-report",
        default=(
            "docs/evidence/gate-3-3-two-strata/raw/"
            "two-strata-report.json"
        ),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    gate32 = json.loads(
        Path(args.gate32_report).read_text(encoding="utf-8")
    )
    gate33 = json.loads(
        Path(args.gate33_report).read_text(encoding="utf-8")
    )
    scale = summarize_preserved_evidence(gate32, gate33)
    print(json.dumps(scale.as_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
