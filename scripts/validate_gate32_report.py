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
    parser.add_argument(
        "--compact",
        action="store_true",
        help="print only evaluator-facing headline metrics",
    )
    args = parser.parse_args()

    report_path = Path(args.report)
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    episodes = validate_gate32_payload(
        payload,
        require_complete=not args.allow_partial,
    )
    result = {
        "report": str(report_path),
        "validated_episode_count": len(episodes),
        "protocol_sha256": payload["protocol"]["protocol_sha256"],
    }
    if args.compact:
        summary = payload["summary"]
        result["verified_metrics"] = {
            "baseline_repeatable_safe_completion": (
                f"{summary['baseline']['repeatable_safe_completion_count']}"
                f"/{summary['baseline']['episode_count']}"
            ),
            "guardiansim_repeatable_safe_completion": (
                f"{summary['guardiansim']['repeatable_safe_completion_count']}"
                f"/{summary['guardiansim']['episode_count']}"
            ),
            "baseline_independent_safe_executions": (
                f"{summary['baseline']['execution_safe_completion_count']}"
                f"/{summary['baseline']['execution_count']}"
            ),
            "guardiansim_independent_safe_executions": (
                f"{summary['guardiansim']['execution_safe_completion_count']}"
                f"/{summary['guardiansim']['execution_count']}"
            ),
            "baseline_clutter_contacts": summary["baseline"]["clutter_contact_count"],
            "guardiansim_clutter_contacts": summary["guardiansim"]["clutter_contact_count"],
        }
    else:
        result["summary"] = payload["summary"]
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
