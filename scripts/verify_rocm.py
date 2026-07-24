"""Fail-fast validation for the official Radeon Cloud execution environment."""

from __future__ import annotations

import json
import platform
import sys


def main() -> int:
    try:
        import torch
    except ImportError:
        print(json.dumps({"ok": False, "error": "PyTorch is not installed"}, indent=2))
        return 1

    hip_version = getattr(torch.version, "hip", None)
    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    payload = {
        "ok": bool(hip_version and gpu_count == 1),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "torch": torch.__version__,
        "hip": hip_version,
        "gpu_count": gpu_count,
        "gpu_name": torch.cuda.get_device_name(0) if gpu_count else None,
    }
    print(json.dumps(payload, indent=2))
    if not hip_version:
        print("ERROR: PyTorch is not a ROCm build.", file=sys.stderr)
        return 2
    if gpu_count != 1:
        print(f"ERROR: expected exactly one visible Radeon GPU, found {gpu_count}.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
