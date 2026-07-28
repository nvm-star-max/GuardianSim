#!/usr/bin/env python3
"""Validate the ROCm Safety Critic report and its showcase quality gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_critic_report import validate_safety_critic_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--allow-quality-gate-failure",
        action="store_true",
        help="Inspect a valid engineering report that is not showcase-ready.",
    )
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    result = validate_safety_critic_report(
        payload,
        require_ready=not args.allow_quality_gate_failure,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
