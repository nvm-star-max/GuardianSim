#!/usr/bin/env python3
"""Run one immutable full-scene Radeon Scale V2 trial."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import derive_trial_metrics
from guardian_sim.radeon_scale_v2 import (
    validate_scale_v2_protocol,
    validate_scale_v2_trial,
)
from guardian_sim.rocm_telemetry import RocmSmiSampler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--n-envs", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def write_json_exclusive(path: Path, payload: object) -> None:
    """Write JSON atomically without replacing any existing evidence."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {path}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary evidence path already exists: {temporary}")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        if path.exists():
            raise FileExistsError(f"refusing to overwrite evidence: {path}")
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    args = build_parser().parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    validate_scale_v2_protocol(protocol, require_frozen_formal=False)
    if args.n_envs not in [int(value) for value in protocol["batch_sizes"]]:
        raise ValueError("n-envs is not part of the declared protocol")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite evidence: {args.output}")

    import genesis as gs
    import numpy as np
    import torch

    from franka_fruit_pick.build_scene import build_scene
    from franka_fruit_pick.scene_config import FRANKA_QPOS

    if not torch.cuda.is_available() or not torch.version.hip:
        raise RuntimeError("Radeon Scale V2 requires ROCm/HIP PyTorch")

    started_at = datetime.now(UTC).isoformat()
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
    for _ in range(int(protocol["warmup_steps"])):
        bundle.franka.control_dofs_position(hold_qpos)
        bundle.scene.step()
    torch.cuda.synchronize()
    warmup_seconds = time.perf_counter() - warmup_started

    sampler = RocmSmiSampler()
    sampler.start()
    torch.cuda.synchronize()
    measurement_started = time.perf_counter()
    for _ in range(int(protocol["measurement_steps"])):
        bundle.franka.control_dofs_position(hold_qpos)
        bundle.scene.step()
    torch.cuda.synchronize()
    measurement_seconds = time.perf_counter() - measurement_started
    telemetry = sampler.stop()

    metrics = derive_trial_metrics(
        n_envs=args.n_envs,
        measurement_steps=int(protocol["measurement_steps"]),
        measurement_seconds=measurement_seconds,
        simulation_dt_s=float(protocol["simulation_dt_s"]),
    )
    payload: dict[str, object] = {
        "status": "passed",
        "protocol_sha256": protocol["protocol_sha256"],
        "backend": "genesis_gpu",
        "n_envs": args.n_envs,
        "process_id": os.getpid(),
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(UTC).isoformat(),
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
    validate_scale_v2_trial(payload, protocol, require_telemetry=True)
    write_json_exclusive(args.output, payload)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
