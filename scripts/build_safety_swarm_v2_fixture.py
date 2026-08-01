#!/usr/bin/env python3
"""Build a deterministic, non-Radeon Safety Swarm V2 selection fixture."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm_v2 import (
    assemble_safety_swarm_v2_smoke_report,
    build_safety_swarm_v2_offline_fixture_measurements,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--tier",
        choices=("triad-4", "full-4", "full-16"),
        default="triad-4",
    )
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    report = assemble_safety_swarm_v2_smoke_report(
        build_safety_swarm_v2_offline_fixture_measurements(args.tier),
        tier=args.tier,
        wall_seconds=1.0,
        mode="offline_fixture",
        backend="deterministic_fixture",
        source_commit="fixture",
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
