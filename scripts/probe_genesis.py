#!/usr/bin/env python3
"""Build and step the retained Franka scene, then save machine-readable evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _to_list(value):
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _to_numpy(value):
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        return value.numpy()
    import numpy as np

    return np.asarray(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Probe the Genesis Franka scene on Radeon Cloud.")
    parser.add_argument("--n-envs", type=int, default=1)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--save-frames", action="store_true")
    parser.add_argument("--output-dir", default="outputs/evidence/genesis-probe")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.n_envs < 1 or args.steps < 0:
        raise ValueError("n-envs must be positive and steps cannot be negative")

    import genesis as gs
    import numpy as np

    from franka_fruit_pick.build_scene import build_scene
    from franka_fruit_pick.scene_config import FRANKA_QPOS

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gs.init(backend=gs.gpu)
    bundle = build_scene(
        n_envs=args.n_envs,
        add_world_cam=args.save_frames,
        add_wrist_cam=args.save_frames,
    )
    hold_qpos = np.asarray(FRANKA_QPOS)
    if args.n_envs > 1:
        hold_qpos = np.tile(hold_qpos, (args.n_envs, 1))
    for _ in range(args.steps):
        bundle.franka.control_dofs_position(hold_qpos)
        bundle.scene.step()
        bundle.update_wrist_cam()

    frames: dict[str, str] = {}
    if args.save_frames:
        import imageio.v2 as imageio

        for camera_name, rendered in bundle.render(rgb=True).items():
            frame = rendered[0] if isinstance(rendered, tuple) else rendered
            frame_path = output_dir / f"{camera_name}.png"
            imageio.imwrite(frame_path, _to_numpy(frame))
            frames[camera_name] = str(frame_path)

    payload = {
        "backend": "genesis_gpu",
        "n_envs": args.n_envs,
        "steps": args.steps,
        "franka_qpos": _to_list(bundle.franka.get_qpos()),
        "objects": {name: _to_list(entity.get_pos()) for name, entity in sorted(bundle.ycb.items())},
        "frames": frames,
        "status": "passed",
    }
    evidence_path = output_dir / "scene-probe.json"
    evidence_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
