#!/usr/bin/env python3
"""Back up GuardianSim into the active Radeon Cloud persistence mount."""

from __future__ import annotations

import argparse
from pathlib import Path

from guardian_sim.backup import create_backup, result_as_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--persistence-root",
        type=Path,
        help="Override mount detection (normally /workspace/persistence or /workspace/persistent).",
    )
    parser.add_argument(
        "--include-file",
        action="append",
        default=[],
        type=Path,
        help="Copy an additional raw artifact into the backup (repeatable).",
    )
    args = parser.parse_args()

    result = create_backup(
        args.repo,
        persistence_root=args.persistence_root,
        include_files=tuple(args.include_file),
    )
    print(result_as_json(result))


if __name__ == "__main__":
    main()
