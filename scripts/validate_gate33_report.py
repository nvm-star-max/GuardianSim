#!/usr/bin/env python3
"""Validate a Gate 3.3 report and print its engineering-only summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardian_sim.gate33_benchmark import validate_gate33_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        default="outputs/gate-3-3/smoke-report.json",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="validate a resumable prefix instead of requiring all 24 episodes",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    episodes = validate_gate33_payload(
        payload,
        require_complete=not args.allow_partial,
    )
    print(
        json.dumps(
            {
                "report": str(report_path),
                "validated_episode_count": len(episodes),
                "evidence_status": payload["protocol"]["status"],
                "protocol_sha256": payload["protocol"]["protocol_sha256"],
                "matrix_sha256": payload["protocol"][
                    "scenario_matrix_sha256"
                ],
                "stop_reasons": payload["stop_reasons"],
                "summary": payload["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
