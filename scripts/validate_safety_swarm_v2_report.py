#!/usr/bin/env python3
"""Strictly validate a GuardianSim Radeon Safety Swarm V2 smoke report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm_v2 import validate_safety_swarm_v2_smoke_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-radeon", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    validation = validate_safety_swarm_v2_smoke_report(
        payload,
        require_radeon=args.require_radeon,
    )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
