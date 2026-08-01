#!/usr/bin/env python3
"""Build a deterministic, explicitly non-Radeon Safety Swarm UI fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm import (
    assemble_safety_swarm_report,
    build_offline_fixture_measurements,
    validate_safety_swarm_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    args = parser.parse_args()

    report = assemble_safety_swarm_report(
        build_offline_fixture_measurements(),
        candidate_id="ui-fixture-candidate",
        wall_seconds=1.0,
        mode="offline_fixture",
        backend="deterministic_fixture",
        source_commit="fixture",
    )
    validation = validate_safety_swarm_report(report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        f"{json.dumps(report, indent=2)}\n",
        encoding="utf-8",
    )
    args.validation.write_text(
        f"{json.dumps(validation, indent=2)}\n",
        encoding="utf-8",
    )
    print(args.report)
    print(args.validation)


if __name__ == "__main__":
    main()
