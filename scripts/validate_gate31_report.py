#!/usr/bin/env python3
"""Validate a Gate 3.1 report against the frozen protocol and print its summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from guardian_sim.adversarial_benchmark import (
    summarize_gate31,
    validate_gate31_payload,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        default="outputs/gate-3-1/report.json",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="validate a resumable smoke-run prefix instead of requiring all 30 episodes",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    episodes = validate_gate31_payload(
        payload,
        require_complete=not args.allow_partial,
    )
    expected_summary = summarize_gate31(episodes)
    if payload.get("summary") != expected_summary:
        raise ValueError("stored Gate 3.1 summary does not match raw episodes")
    print(
        json.dumps(
            {
                "report": str(report_path),
                "validated_episode_count": len(episodes),
                "protocol_sha256": payload["protocol"]["protocol_sha256"],
                "summary": expected_summary,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
