#!/usr/bin/env python3
"""Strictly validate a frozen Radeon Scale V2 report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale_v2 import validate_scale_v2_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(validate_scale_v2_report(payload), indent=2))


if __name__ == "__main__":
    main()
