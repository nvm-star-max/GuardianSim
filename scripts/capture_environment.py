#!/usr/bin/env python3
"""Capture GuardianSim host, dependency, ROCm, and source metadata as JSON."""

from __future__ import annotations

import argparse
from pathlib import Path

from guardian_sim.environment_manifest import capture_environment, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="return a non-zero exit code unless the supported Radeon runtime is ready",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    payload = capture_environment(repo_root)
    print(write_manifest(payload, args.output), end="")
    return 2 if args.require_gpu and not payload["gpu_ready"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
