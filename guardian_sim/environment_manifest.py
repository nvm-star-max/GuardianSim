"""Capture a portable, machine-readable GuardianSim runtime manifest."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

TRACKED_PACKAGES = (
    "genesis-world",
    "numpy",
    "scikit-image",
    "trimesh",
    "opencv-python",
    "imageio",
    "imageio-ffmpeg",
    "torch",
    "torchvision",
    "torchaudio",
    "triton",
    "lerobot",
)


def _run(command: Sequence[str], *, cwd: Path | None = None) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return {
            "available": False,
            "command": list(command),
            "error": type(error).__name__,
        }
    return {
        "available": True,
        "command": list(command),
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _os_release(path: Path = Path("/etc/os-release")) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value.strip().strip('"')
    return values


def _package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in TRACKED_PACKAGES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _torch_runtime() -> dict[str, object]:
    try:
        import torch
    except (ImportError, OSError) as error:
        return {
            "available": False,
            "error": f"{type(error).__name__}: {error}",
            "hip": None,
            "gpu_count": 0,
            "gpu_names": [],
        }

    gpu_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    return {
        "available": True,
        "version": torch.__version__,
        "hip": getattr(torch.version, "hip", None),
        "cuda_api_available": bool(torch.cuda.is_available()),
        "gpu_count": gpu_count,
        "gpu_names": [torch.cuda.get_device_name(index) for index in range(gpu_count)],
    }


def capture_environment(repo_root: Path) -> dict[str, object]:
    """Return environment facts without requiring a GPU or optional package."""

    repo_root = repo_root.resolve()
    git_commit = _run(("git", "rev-parse", "HEAD"), cwd=repo_root)
    git_status = _run(("git", "status", "--short"), cwd=repo_root)
    torch_runtime = _torch_runtime()
    os_release = _os_release()
    packages = _package_versions()
    python_312 = sys.version_info[:2] == (3, 12)
    linux = sys.platform.startswith("linux")
    rocm_torch = bool(torch_runtime.get("hip"))
    one_gpu = torch_runtime.get("gpu_count") == 1

    return {
        "schema_version": 1,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": "GuardianSim",
        "source": {
            "repository": "https://github.com/nvm-star-max/GuardianSim",
            "git_commit": git_commit.get("stdout") if git_commit.get("returncode") == 0 else None,
            "git_dirty": bool(git_status.get("stdout")) if git_status.get("returncode") == 0 else None,
        },
        "cloud": {
            "provider": "AMD Radeon Cloud",
            "template": os.environ.get("RADEON_CLOUD_TEMPLATE"),
            "instance_id": os.environ.get("RADEON_CLOUD_INSTANCE_ID"),
        },
        "host": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "os_release": os_release,
        },
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable": sys.executable,
        },
        "packages": packages,
        "torch_runtime": torch_runtime,
        "rocm_smi": _run(("rocm-smi", "--showproductname")),
        "checks": {
            "linux": linux,
            "python_3_12": python_312,
            "rocm_pytorch": rocm_torch,
            "exactly_one_visible_gpu": one_gpu,
            "genesis_installed": packages["genesis-world"] is not None,
        },
        "gpu_ready": bool(linux and python_312 and rocm_torch and one_gpu),
    }


def write_manifest(payload: dict[str, object], output: Path | None) -> str:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return rendered
