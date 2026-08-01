#!/usr/bin/env python3
"""Render a validated Safety Swarm report as HTML and a PNG review frame."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm import validate_safety_swarm_report

COLORS = {
    "safe": "#67f5b4",
    "clutter_contact": "#ff5f57",
    "unreachable": "#9aa8b2",
    "clearance_below_minimum": "#ff9f43",
    "stability_below_minimum": "#b784ff",
    "task_failure": "#4bd6ff",
}


def _tooltip(result: dict[str, object]) -> str:
    world = result["perturbation"]
    measurement = result["measurement"]
    return (
        f"WORLD {int(result['world_id']):03d}\n"
        f"{str(result['primary_stop_reason']).replace('_', ' ').upper()}\n"
        f"Target bias: {float(world['target_dx_m']) * 1000:+.1f}, "
        f"{float(world['target_dy_m']) * 1000:+.1f} mm · "
        f"yaw {float(world['target_yaw_bias_deg']):+.1f}°\n"
        f"Clutter gap: {float(world['clutter_gap_delta_m']) * 1000:+.1f} mm · "
        f"bearing {float(world['clutter_bearing_bias_deg']):+.1f}°\n"
        f"EE bias: {float(world['end_effector_dx_m']) * 1000:+.1f}, "
        f"{float(world['end_effector_dy_m']) * 1000:+.1f} mm · "
        f"delay {int(world['action_start_delay_steps'])} steps\n"
        f"Clearance {float(measurement['minimum_clearance_m']) * 1000:.2f} mm · "
        f"stability {float(measurement['stability']):.3f}"
    )


def _render_html(payload: dict[str, object], output: Path) -> None:
    summary = payload["summary"]
    protocol = payload["protocol"]
    is_fixture = payload["mode"] == "offline_fixture"
    cells = []
    for result in payload["results"]:
        reason = str(result["primary_stop_reason"])
        tooltip = html.escape(_tooltip(result), quote=True)
        cells.append(
            '<button class="world {reason}" aria-label="{tooltip}" '
            'data-tip="{tooltip}"><span>{world_id:03d}</span></button>'.format(
                reason=reason,
                tooltip=tooltip,
                world_id=int(result["world_id"]),
            )
        )
    histogram = summary["failure_histogram"]
    legend = "".join(
        (
            f'<li><i style="--tone:{COLORS[reason]}"></i>'
            f"<span>{reason.replace('_', ' ')}</span>"
            f"<b>{int(histogram[reason])}</b></li>"
        )
        for reason in COLORS
        if int(histogram[reason]) > 0 or reason == "safe"
    )
    banner = (
        "OFFLINE UI FIXTURE · NOT A RADEON RESULT"
        if is_fixture
        else "PRESERVED RADEON RUN · STRICT VALIDATION PASSED"
    )
    device = payload.get("device") or {}
    hardware = (
        "Cloud execution pending"
        if is_fixture
        else f"{device.get('name')} · HIP {device.get('hip_version')}"
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GuardianSim · Radeon Safety Swarm</title>
  <style>
    :root {{
      color-scheme: dark;
      --ink: #edf8ff;
      --muted: #8296a3;
      --cyan: #4bd6ff;
      --green: #67f5b4;
      --orange: #ff9f43;
      --panel: #06151d;
      --line: rgba(75,214,255,.20);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 10%, rgba(75,214,255,.10), transparent 28rem),
        radial-gradient(circle at 86% 80%, rgba(103,245,180,.07), transparent 30rem),
        #02080c;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    }}
    main {{ width: min(1480px, calc(100% - 48px)); margin: 0 auto; padding: 34px 0 50px; }}
    .topline {{
      display: flex; justify-content: space-between; gap: 24px; align-items: center;
      padding-bottom: 22px; border-bottom: 1px solid var(--line);
      font: 700 12px/1 ui-monospace, monospace; letter-spacing: .12em;
    }}
    .brand {{ color: var(--cyan); }}
    .status {{ color: {("#ffcf67" if is_fixture else "#67f5b4")}; }}
    header {{ display: grid; grid-template-columns: 1fr auto; gap: 32px; padding: 42px 0 30px; }}
    h1 {{ margin: 0; max-width: 920px; font-size: clamp(44px, 5vw, 78px); line-height: .98; letter-spacing: -.055em; }}
    h1 span {{ color: var(--green); }}
    .hashes {{ min-width: 310px; align-self: end; color: var(--muted); font: 11px/1.75 ui-monospace, monospace; }}
    .hashes b {{ display: block; color: #b8cad4; font-weight: 500; overflow-wrap: anywhere; }}
    .workspace {{ display: grid; grid-template-columns: minmax(620px, 1.5fr) minmax(310px, .7fr); gap: 22px; }}
    .wall-shell, .decision, .metric, .legend {{
      border: 1px solid var(--line); background: rgba(6,21,29,.86);
      box-shadow: inset 0 1px rgba(255,255,255,.03);
    }}
    .wall-shell {{ padding: 22px; }}
    .wall-head {{ display: flex; justify-content: space-between; gap: 20px; margin-bottom: 18px; }}
    .wall-head b {{ font: 700 12px/1 ui-monospace, monospace; color: var(--cyan); letter-spacing: .1em; }}
    .wall-head span {{ color: var(--muted); font-size: 12px; }}
    .wall {{ display: grid; grid-template-columns: repeat(16, 1fr); gap: 7px; }}
    .world {{
      position: relative; aspect-ratio: 1; min-width: 0; border: 1px solid color-mix(in srgb, var(--tone) 52%, transparent);
      border-radius: 4px; cursor: help; background: color-mix(in srgb, var(--tone) 14%, #07151d);
      box-shadow: inset 0 0 14px color-mix(in srgb, var(--tone) 8%, transparent);
    }}
    .world:hover {{ z-index: 4; transform: scale(1.18); border-color: var(--tone); box-shadow: 0 0 18px color-mix(in srgb, var(--tone) 38%, transparent); }}
    .world::after {{
      content: attr(data-tip); display: none; position: absolute; z-index: 10; left: 50%; bottom: calc(100% + 12px);
      width: 290px; padding: 12px 14px; white-space: pre-line; text-align: left; color: #eaf8ff;
      border: 1px solid var(--tone); background: #020a0f; font: 11px/1.55 ui-monospace, monospace;
      transform: translateX(-50%); pointer-events: none;
    }}
    .world:hover::after {{ display: block; }}
    .world span {{ opacity: 0; font: 8px/1 ui-monospace, monospace; }}
    {''.join(f'.world.{key} {{ --tone: {value}; }}' for key, value in COLORS.items())}
    aside {{ display: grid; gap: 14px; align-content: start; }}
    .decision {{ padding: 26px; border-top: 3px solid {("#ff9f43" if summary["decision"] == "safe_stop" else "#67f5b4")}; }}
    .decision span, .metric span {{ color: var(--muted); font: 700 10px/1.2 ui-monospace, monospace; letter-spacing: .1em; }}
    .decision strong {{ display: block; margin: 14px 0 8px; color: {("#ff9f43" if summary["decision"] == "safe_stop" else "#67f5b4")}; font-size: 42px; }}
    .decision p {{ margin: 0; color: #b8cad4; line-height: 1.55; }}
    .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
    .metric {{ padding: 18px; min-height: 126px; }}
    .metric strong {{ display: block; margin-top: 15px; font: 700 27px/1 ui-monospace, monospace; }}
    .metric small {{ display: block; margin-top: 10px; color: var(--muted); }}
    .legend {{ padding: 20px; }}
    .legend ul {{ list-style: none; margin: 14px 0 0; padding: 0; display: grid; gap: 10px; }}
    .legend li {{ display: grid; grid-template-columns: 12px 1fr auto; gap: 10px; align-items: center; color: #b8cad4; font-size: 12px; text-transform: capitalize; }}
    .legend i {{ width: 10px; height: 10px; background: var(--tone); box-shadow: 0 0 10px color-mix(in srgb, var(--tone) 40%, transparent); }}
    .legend b {{ color: var(--ink); font-family: ui-monospace, monospace; }}
    footer {{ display: flex; justify-content: space-between; gap: 20px; margin-top: 18px; color: var(--muted); font: 11px/1.5 ui-monospace, monospace; }}
    footer b {{ color: #b8cad4; font-weight: 500; }}
    @media (max-width: 980px) {{
      main {{ width: min(100% - 24px, 760px); }}
      header, .workspace {{ grid-template-columns: 1fr; }}
      .hashes {{ min-width: 0; }}
      .wall {{ gap: 3px; }}
      .wall-shell {{ padding: 10px; }}
      .world::after {{ display: none !important; }}
      footer {{ flex-direction: column; }}
    }}
  </style>
</head>
<body>
<main>
  <div class="topline"><span class="brand">AEGIS MOTION / GUARDIANSIM</span><span class="status">{banner}</span></div>
  <header>
    <h1>One move. <span>256 uncertain worlds.</span><br>Move only if all agree.</h1>
    <div class="hashes">MATRIX SHA-256<b>{protocol["matrix_sha256"]}</b>REPORT SHA-256<b>{payload["report_sha256"]}</b></div>
  </header>
  <div class="workspace">
    <section class="wall-shell">
      <div class="wall-head"><b>16 × 16 FROZEN UNCERTAINTY MATRIX</b><span>Hover any cell for the exact perturbation</span></div>
      <div class="wall">{''.join(cells)}</div>
    </section>
    <aside>
      <section class="decision">
        <span>SWARM DECISION</span>
        <strong>{str(summary["decision"]).replace("_", " ").upper()}</strong>
        <p>{int(summary["safe_world_count"])}/256 worlds passed every hard gate. One failed world is enough to stop.</p>
      </section>
      <div class="metrics">
        <section class="metric"><span>SAFE WORLDS</span><strong>{int(summary["safe_world_count"])} / 256</strong><small>Wilson lower bound {float(summary["safe_world_rate_wilson_lower_bound"]) * 100:.1f}%</small></section>
        <section class="metric"><span>WORST CLEARANCE</span><strong>{float(summary["worst_case_clearance_m"]) * 1000:.2f} mm</strong><small>Frozen hard gate {float(protocol["minimum_safe_clearance_m"]) * 1000:.1f} mm</small></section>
        <section class="metric"><span>5TH PERCENTILE</span><strong>{float(summary["fifth_percentile_clearance_m"]) * 1000:.2f} mm</strong><small>Across all 256 worlds</small></section>
        <section class="metric"><span>MIN STABILITY</span><strong>{float(summary["minimum_stability"]):.3f}</strong><small>Frozen hard gate {float(protocol["minimum_stability"]):.2f}</small></section>
      </div>
      <section class="legend"><span>WORLD OUTCOMES</span><ul>{legend}</ul></section>
    </aside>
  </div>
  <footer><span>{hardware}</span><b>{protocol["evidence_scope"]}</b></footer>
</main>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


def _render_png(payload: dict[str, object], output: Path) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from matplotlib.patches import Rectangle

    summary = payload["summary"]
    protocol = payload["protocol"]
    reasons = list(COLORS)
    reason_index = {reason: index for index, reason in enumerate(reasons)}
    values = [
        [
            reason_index[str(payload["results"][row * 16 + column]["primary_stop_reason"])]
            for column in range(16)
        ]
        for row in range(16)
    ]

    figure = plt.figure(figsize=(16, 9), dpi=140, facecolor="#02080c")
    grid = figure.add_gridspec(
        12,
        20,
        left=0.045,
        right=0.97,
        top=0.90,
        bottom=0.10,
        wspace=0.6,
        hspace=0.8,
    )
    wall_axis = figure.add_subplot(grid[2:11, :13])
    panel_axis = figure.add_subplot(grid[2:11, 14:])
    for axis in (wall_axis, panel_axis):
        axis.set_facecolor("#06151d")

    wall_axis.imshow(values, cmap=ListedColormap([COLORS[key] for key in reasons]))
    wall_axis.set_xticks([])
    wall_axis.set_yticks([])
    for index in range(17):
        wall_axis.axhline(index - 0.5, color="#02080c", linewidth=2.4)
        wall_axis.axvline(index - 0.5, color="#02080c", linewidth=2.4)
    for spine in wall_axis.spines.values():
        spine.set_color("#23404d")
    wall_axis.set_title(
        "16 × 16 FROZEN UNCERTAINTY MATRIX",
        loc="left",
        pad=14,
        color="#4bd6ff",
        fontsize=11,
        fontfamily="monospace",
        weight="bold",
    )

    panel_axis.set_xlim(0, 1)
    panel_axis.set_ylim(0, 1)
    panel_axis.axis("off")
    decision_color = (
        "#ff9f43" if summary["decision"] == "safe_stop" else "#67f5b4"
    )
    panel_axis.add_patch(
        Rectangle(
            (0, 0.73),
            1,
            0.27,
            facecolor="#071923",
            edgecolor=decision_color,
            linewidth=1.5,
        )
    )
    panel_axis.text(
        0.06,
        0.94,
        "SWARM DECISION",
        color="#8296a3",
        fontsize=9,
        fontfamily="monospace",
        va="top",
    )
    panel_axis.text(
        0.06,
        0.84,
        str(summary["decision"]).replace("_", " ").upper(),
        color=decision_color,
        fontsize=28,
        weight="bold",
        va="top",
    )
    panel_axis.text(
        0.06,
        0.75,
        f"{summary['safe_world_count']} / 256 worlds passed every hard gate",
        color="#b8cad4",
        fontsize=9,
        va="bottom",
    )
    metric_rows = (
        (
            "SAFE WORLDS",
            f"{summary['safe_world_count']} / 256",
            f"Wilson lower bound {summary['safe_world_rate_wilson_lower_bound'] * 100:.1f}%",
        ),
        (
            "WORST CLEARANCE",
            f"{summary['worst_case_clearance_m'] * 1000:.2f} mm",
            f"hard gate {protocol['minimum_safe_clearance_m'] * 1000:.1f} mm",
        ),
        (
            "5TH PERCENTILE",
            f"{summary['fifth_percentile_clearance_m'] * 1000:.2f} mm",
            "across all 256 worlds",
        ),
        (
            "MIN STABILITY",
            f"{summary['minimum_stability']:.3f}",
            f"hard gate {protocol['minimum_stability']:.2f}",
        ),
    )
    for index, (label, value, detail) in enumerate(metric_rows):
        y = 0.63 - index * 0.135
        panel_axis.text(
            0.02,
            y,
            label,
            color="#8296a3",
            fontsize=8,
            fontfamily="monospace",
            va="top",
        )
        panel_axis.text(
            0.98,
            y,
            value,
            color="#edf8ff",
            fontsize=15,
            fontfamily="monospace",
            weight="bold",
            ha="right",
            va="top",
        )
        panel_axis.text(
            0.98,
            y - 0.047,
            detail,
            color="#8296a3",
            fontsize=7.5,
            ha="right",
            va="top",
        )

    histogram = summary["failure_histogram"]
    legend_y = 0.08
    for reason in reasons:
        count = int(histogram[reason])
        if count == 0 and reason != "safe":
            continue
        panel_axis.scatter(
            [0.03],
            [legend_y],
            color=COLORS[reason],
            marker="s",
            s=50,
        )
        panel_axis.text(
            0.08,
            legend_y,
            reason.replace("_", " ").upper(),
            color="#b8cad4",
            fontsize=7.5,
            va="center",
        )
        panel_axis.text(
            0.98,
            legend_y,
            str(count),
            color="#edf8ff",
            fontsize=8,
            fontfamily="monospace",
            ha="right",
            va="center",
        )
        legend_y -= 0.05

    figure.text(
        0.045,
        0.965,
        "AEGIS MOTION / GUARDIANSIM",
        color="#4bd6ff",
        fontsize=10,
        fontfamily="monospace",
        weight="bold",
    )
    figure.text(
        0.97,
        0.965,
        (
            "OFFLINE UI FIXTURE · NOT A RADEON RESULT"
            if payload["mode"] == "offline_fixture"
            else "PRESERVED RADEON RUN · VALIDATED"
        ),
        color="#ffcf67" if payload["mode"] == "offline_fixture" else "#67f5b4",
        fontsize=9,
        fontfamily="monospace",
        weight="bold",
        ha="right",
    )
    figure.text(
        0.045,
        0.915,
        "ONE MOVE. 256 UNCERTAIN WORLDS. MOVE ONLY IF ALL AGREE.",
        color="#edf8ff",
        fontsize=25,
        weight="bold",
    )
    figure.text(
        0.045,
        0.045,
        "Engineering uncertainty stress test · separate from Gate 3.2 formal scenarios · not a physical-robot guarantee",
        color="#8296a3",
        fontsize=8,
        fontfamily="monospace",
    )
    figure.text(
        0.97,
        0.045,
        f"MATRIX {protocol['matrix_sha256'][:12]} · REPORT {payload['report_sha256'][:12]}",
        color="#8296a3",
        fontsize=8,
        fontfamily="monospace",
        ha="right",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output, facecolor=figure.get_facecolor())
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--html", type=Path)
    parser.add_argument("--png", type=Path)
    args = parser.parse_args()
    if args.html is None and args.png is None:
        parser.error("at least one of --html or --png is required")

    payload = json.loads(args.report.read_text(encoding="utf-8"))
    validate_safety_swarm_report(payload)
    if args.html is not None:
        _render_html(payload, args.html)
        print(args.html)
    if args.png is not None:
        _render_png(payload, args.png)
        print(args.png)


if __name__ == "__main__":
    main()
