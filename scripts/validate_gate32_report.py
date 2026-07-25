#!/usr/bin/env python3
"""Validate a Gate 3.2 report and print its verified summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardian_sim.gate32_benchmark import validate_gate32_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        default="outputs/gate-3-2/report.json",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="validate a resumable prefix instead of requiring all 30 episodes",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    episodes = validate_gate32_payload(
        payload,
        require_complete=not args.allow_partial,
    )
    print(
        json.dumps(
            {
                "report": str(report_path),
                "validated_episode_count": len(episodes),
                "protocol_sha256": payload["protocol"]["protocol_sha256"],
                "summary": payload["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

