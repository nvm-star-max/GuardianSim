#!/usr/bin/env python3
"""Strictly validate a preserved Radeon scaling report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import validate_scale_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument(
        "--allow-missing-telemetry",
        action="store_true",
        help="Development-only relaxation; official Radeon evidence must not use it.",
    )
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    result = validate_scale_report(
        payload,
        require_telemetry=not args.allow_missing_telemetry,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
