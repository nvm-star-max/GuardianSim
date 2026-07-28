#!/usr/bin/env python3
"""Render a validated Radeon scaling report as a judge-facing evidence card."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.radeon_scale import validate_scale_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.report.read_text(encoding="utf-8"))
    validate_scale_report(payload, require_telemetry=True)

    import matplotlib.pyplot as plt

    trials = payload["trials"]
    batch_sizes = [trial["n_envs"] for trial in trials]
    throughput = [trial["environment_steps_per_second"] for trial in trials]
    speedup = [trial["speedup_vs_single_env"] for trial in trials]
    gpu_name = trials[0]["device"]["name"]
    largest = trials[-1]
    telemetry = largest["gpu_telemetry"]

    plt.style.use("dark_background")
    figure, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=160)
    figure.patch.set_facecolor("#03090d")
    for axis in axes:
        axis.set_facecolor("#071219")
        axis.grid(axis="y", color="#24404c", alpha=0.5, linewidth=0.8)
        axis.spines[["top", "right"]].set_visible(False)

    axes[0].bar(
        [str(value) for value in batch_sizes],
        throughput,
        color=[
            "#46dcff" if index < len(batch_sizes) / 2 else "#77ffb2"
            for index in range(len(batch_sizes))
        ],
    )
    axes[0].set_title("Steady-state physics throughput", loc="left", weight="bold")
    axes[0].set_xlabel("Parallel Franka worlds")
    axes[0].set_ylabel("Environment steps / second")
    for index, value in enumerate(throughput):
        axes[0].text(index, value, f" {value:,.0f}", va="bottom", color="#eaf8ff")

    axes[1].plot(
        batch_sizes,
        speedup,
        marker="o",
        linewidth=3,
        color="#77ffb2",
    )
    axes[1].set_xscale("log", base=2)
    axes[1].set_xticks(batch_sizes, [str(value) for value in batch_sizes])
    axes[1].set_title("Measured speedup vs 1 world", loc="left", weight="bold")
    axes[1].set_xlabel("Parallel Franka worlds")
    axes[1].set_ylabel("Speedup")
    for x_value, y_value in zip(batch_sizes, speedup, strict=True):
        axes[1].text(x_value, y_value, f" {y_value:.2f}×", va="bottom", color="#eaf8ff")

    title = "GUARDIANSIM · RADEON PARALLEL PHYSICS LAB"
    subtitle = (
        f"{gpu_name} · HIP {trials[0]['device']['hip_version']} · "
        f"{largest['n_envs']} worlds · {largest['environment_steps_per_second']:,.0f} env-steps/s · "
        f"GPU peak {telemetry['max_gpu_utilization_pct']:.0f}%"
    )
    figure.suptitle(title, x=0.06, y=0.98, ha="left", fontsize=21, weight="bold", color="#46dcff")
    figure.text(0.06, 0.91, subtitle, color="#b7cbd4", fontsize=11)
    figure.text(
        0.06,
        0.03,
        "Physics-throughput evidence only · not an independent safety-trial count",
        color="#7f929e",
        fontsize=9,
    )
    figure.subplots_adjust(left=0.07, right=0.97, top=0.82, bottom=0.13, wspace=0.22)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(args.output, facecolor=figure.get_facecolor())
    plt.close(figure)
    print(args.output)


if __name__ == "__main__":
    main()
