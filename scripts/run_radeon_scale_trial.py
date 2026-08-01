#!/usr/bin/env python3
"""Run one isolated Genesis batch-size trial on an AMD Radeon GPU."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import (
    RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS,
    RADEON_SCALE_DEFAULT_WARMUP_STEPS,
    build_scale_protocol,
    derive_trial_metrics,
    sha256_file,
)
from guardian_sim.rocm_telemetry import RocmSmiSampler

SCENE_SOURCE = ROOT / "franka_fruit_pick" / "build_scene.py"
SCENE_CONFIG = ROOT / "franka_fruit_pick" / "scene_config.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-envs", type=int, required=True)
    parser.add_argument(
        "--batch-sizes",
        type=int,
        nargs="+",
        required=True,
        help="Full suite batch-size declaration used to lock the protocol hash.",
    )
    parser.add_argument(
        "--warmup-steps",
        type=int,
        default=RADEON_SCALE_DEFAULT_WARMUP_STEPS,
    )
    parser.add_argument(
        "--measurement-steps",
        type=int,
        default=RADEON_SCALE_DEFAULT_MEASUREMENT_STEPS,
    )
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    protocol = build_scale_protocol(
        batch_sizes=args.batch_sizes,
        warmup_steps=args.warmup_steps,
        measurement_steps=args.measurement_steps,
        scene_source_sha256=sha256_file(SCENE_SOURCE),
        scene_config_sha256=sha256_file(SCENE_CONFIG),
    )
    if args.n_envs not in protocol["batch_sizes"]:
        raise ValueError("n-envs is not part of the declared suite")

    import genesis as gs
    import numpy as np
    import torch

    from franka_fruit_pick.build_scene import build_scene
    from franka_fruit_pick.scene_config import FRANKA_QPOS

    if not torch.cuda.is_available() or not torch.version.hip:
        raise RuntimeError("Radeon scaling trials require ROCm/HIP PyTorch")

    gs.init(backend=gs.gpu)
    build_started = time.perf_counter()
    bundle = build_scene(
        n_envs=args.n_envs,
        add_world_cam=False,
        add_wrist_cam=False,
        add_video_cam=False,
    )
    torch.cuda.synchronize()
    build_seconds = time.perf_counter() - build_started

    hold_qpos = np.asarray(FRANKA_QPOS)
    if args.n_envs > 1:
        hold_qpos = np.tile(hold_qpos, (args.n_envs, 1))

    warmup_started = time.perf_counter()
    for _ in range(args.warmup_steps):
        bundle.franka.control_dofs_position(hold_qpos)
        bundle.scene.step()
    torch.cuda.synchronize()
    warmup_seconds = time.perf_counter() - warmup_started

    sampler = RocmSmiSampler()
    sampler.start()
    torch.cuda.synchronize()
    measurement_started = time.perf_counter()
    for _ in range(args.measurement_steps):
        bundle.franka.control_dofs_position(hold_qpos)
        bundle.scene.step()
    torch.cuda.synchronize()
    measurement_seconds = time.perf_counter() - measurement_started
    telemetry = sampler.stop()

    metrics = derive_trial_metrics(
        n_envs=args.n_envs,
        measurement_steps=args.measurement_steps,
        measurement_seconds=measurement_seconds,
    )
    payload = {
        "status": "passed",
        "protocol_sha256": protocol["protocol_sha256"],
        "backend": "genesis_gpu",
        "n_envs": args.n_envs,
        "build_seconds": build_seconds,
        "warmup_seconds": warmup_seconds,
        "measurement_seconds": measurement_seconds,
        **metrics,
        "device": {
            "name": torch.cuda.get_device_name(0),
            "torch_version": torch.__version__,
            "hip_version": torch.version.hip,
            "genesis_version": getattr(gs, "__version__", "unknown"),
        },
        "gpu_telemetry": telemetry,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
