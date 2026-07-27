#!/usr/bin/env python3
"""Write a deterministic recursive SHA-256 manifest for an evidence directory."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def build_manifest(root: Path, output: Path) -> str:
    root = root.resolve()
    output = output.resolve()
    lines: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.resolve() == output:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    output = args.output or args.root / "SHA256SUMS"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_manifest(args.root, output), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
