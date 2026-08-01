#!/usr/bin/env python3
"""Strictly validate a GuardianSim Radeon Safety Swarm V2 report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm_v2 import (
    SAFETY_SWARM_V2_FORMAL_CHUNK_REPORT_NAME,
    SAFETY_SWARM_V2_FORMAL_REPORT_NAME,
    validate_safety_swarm_v2_formal_chunk_report,
    validate_safety_swarm_v2_formal_report,
    validate_safety_swarm_v2_smoke_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-radeon", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    if payload.get("report_name") == SAFETY_SWARM_V2_FORMAL_REPORT_NAME:
        validation = validate_safety_swarm_v2_formal_report(
            payload,
            require_radeon=args.require_radeon,
        )
    elif payload.get("report_name") == SAFETY_SWARM_V2_FORMAL_CHUNK_REPORT_NAME:
        validation = validate_safety_swarm_v2_formal_chunk_report(
            payload,
            require_radeon=args.require_radeon,
        )
    else:
        validation = validate_safety_swarm_v2_smoke_report(
            payload,
            require_radeon=args.require_radeon,
        )
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
