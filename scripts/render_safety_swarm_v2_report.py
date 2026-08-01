#!/usr/bin/env python3
"""Render a validated Safety Swarm V2 candidate-by-world report as HTML."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from guardian_sim.safety_swarm_v2 import validate_safety_swarm_v2_smoke_report

COLORS = {
    "safe": "#63e6a7",
    "clutter_contact": "#ff655c",
    "unreachable": "#8d9aa4",
    "clearance_below_minimum": "#ffad4d",
    "stability_below_minimum": "#ba8cff",
    "task_failure": "#54c7ec",
}


def _short_candidate(candidate_id: str) -> str:
    return (
        candidate_id.replace("yaw_", "Y ")
        .replace("_retreat_", " · R ")
        .replace("_approach_", " · A ")
        .replace("_offset_", " · O ")
    )


def render(payload: dict[str, object], output: Path) -> None:
    validation = validate_safety_swarm_v2_smoke_report(payload)
    protocol = payload["protocol"]
    summary = payload["summary"]
    candidate_summaries = payload["candidate_summaries"]
    world_ids = protocol["world_ids"]
    results_by_pair = {
        (result["candidate_id"], result["world_id"]): result
        for result in payload["results"]
    }
    row_markup = []
    for candidate in candidate_summaries:
        candidate_id = str(candidate["candidate_id"])
        cells = []
        for world_id in world_ids:
            result = results_by_pair[(candidate_id, world_id)]
            measurement = result["measurement"]
            reason = str(result["primary_stop_reason"])
            tooltip = html.escape(
                (
                    f"{candidate_id}\n"
                    f"World {int(world_id):03d} · {reason.replace('_', ' ')}\n"
                    f"Clearance {float(measurement['minimum_clearance_m']) * 1000:.2f} mm\n"
                    f"Stability {float(measurement['stability']):.3f}"
                ),
                quote=True,
            )
            cells.append(
                f'<button class="cell {reason}" title="{tooltip}" '
                f'aria-label="{tooltip}">{int(world_id):03d}</button>'
            )
        state = "QUALIFIED" if candidate["qualifies"] else "REJECTED"
        row_markup.append(
            f"""
            <div class="candidate">
              <div class="candidate-label">
                <span>{int(candidate["candidate_index"]) + 1:02d}</span>
                <b>{html.escape(_short_candidate(candidate_id))}</b>
                <i class="{"qualified" if candidate["qualifies"] else "rejected"}">{state}</i>
              </div>
              <div class="cells" style="--columns:{len(world_ids)}">{''.join(cells)}</div>
              <div class="envelope">
                <b>{int(candidate["safe_world_count"])}/{len(world_ids)}</b>
                <span>worst {float(candidate["worst_case_clearance_m"]) * 1000:.1f} mm</span>
              </div>
            </div>
            """
        )

    selected = summary["selected_candidate_id"] or "NONE — SAFE STOP"
    is_fixture = payload["mode"] == "offline_fixture"
    banner = (
        "OFFLINE SELECTION FIXTURE · NOT A RADEON RESULT"
        if is_fixture
        else "PRESERVED RADEON V2 SMOKE · PARTIAL EVIDENCE"
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>GuardianSim · Safety Swarm V2</title>
  <style>
    :root {{ color-scheme: dark; --bg:#03090d; --panel:#07141b; --line:#18313d; --ink:#eaf6fb; --muted:#8497a1; --cyan:#51cef3; --green:#63e6a7; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:radial-gradient(circle at 85% 5%,#102b37 0,transparent 34rem),var(--bg); color:var(--ink); font-family:Inter,ui-sans-serif,system-ui,sans-serif; }}
    main {{ width:min(1600px,calc(100% - 44px)); margin:auto; padding:28px 0 52px; }}
    .top {{ display:flex; justify-content:space-between; gap:18px; padding-bottom:18px; border-bottom:1px solid var(--line); font:700 11px/1.3 ui-monospace,monospace; letter-spacing:.1em; color:var(--cyan); }}
    header {{ display:grid; grid-template-columns:1fr minmax(320px,.6fr); gap:28px; padding:34px 0; align-items:end; }}
    h1 {{ margin:0; font-size:clamp(38px,5vw,72px); line-height:.96; letter-spacing:-.05em; }}
    h1 em {{ color:var(--green); font-style:normal; }}
    .decision {{ border:1px solid var(--line); border-top:3px solid var(--green); background:rgba(7,20,27,.88); padding:20px; }}
    .decision span,.metric span {{ color:var(--muted); font:700 10px/1.3 ui-monospace,monospace; letter-spacing:.1em; }}
    .decision strong {{ display:block; color:var(--green); margin:10px 0 5px; overflow-wrap:anywhere; font-size:20px; }}
    .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:20px; }}
    .metric {{ background:var(--panel); border:1px solid var(--line); padding:16px; min-height:95px; }}
    .metric b {{ display:block; margin-top:14px; font:700 25px/1 ui-monospace,monospace; }}
    .matrix {{ border:1px solid var(--line); background:rgba(7,20,27,.82); padding:12px; overflow:auto; }}
    .matrix-head {{ display:flex; justify-content:space-between; gap:16px; padding:8px 8px 16px; color:var(--muted); font:11px/1.4 ui-monospace,monospace; }}
    .candidate {{ display:grid; grid-template-columns:330px minmax(360px,1fr) 145px; gap:12px; align-items:center; padding:7px; border-top:1px solid rgba(24,49,61,.7); }}
    .candidate-label {{ display:grid; grid-template-columns:28px 1fr auto; gap:10px; align-items:center; min-width:0; }}
    .candidate-label span {{ color:var(--muted); font:11px/1 ui-monospace,monospace; }}
    .candidate-label b {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font:12px/1.2 ui-monospace,monospace; }}
    .candidate-label i {{ font:700 9px/1 ui-monospace,monospace; font-style:normal; }}
    .qualified {{ color:var(--green); }} .rejected {{ color:#ffad4d; }}
    .cells {{ display:grid; grid-template-columns:repeat(var(--columns),minmax(25px,1fr)); gap:5px; }}
    .cell {{ min-width:0; aspect-ratio:1.2; border:1px solid color-mix(in srgb,var(--tone) 50%,transparent); border-radius:3px; color:transparent; background:color-mix(in srgb,var(--tone) 18%,#07141b); }}
    {''.join(f'.cell.{key}{{--tone:{color};}}' for key,color in COLORS.items())}
    .envelope {{ display:flex; justify-content:space-between; gap:8px; font:10px/1 ui-monospace,monospace; color:var(--muted); }}
    .envelope b {{ color:var(--ink); }}
    footer {{ margin-top:16px; display:flex; justify-content:space-between; gap:18px; color:var(--muted); font:10px/1.5 ui-monospace,monospace; }}
    @media(max-width:900px) {{ header{{grid-template-columns:1fr}} .metrics{{grid-template-columns:1fr 1fr}} .candidate{{grid-template-columns:240px minmax(320px,1fr) 120px}} }}
  </style>
</head>
<body>
<main>
  <div class="top"><span>AEGIS MOTION / GUARDIANSIM / SAFETY SWARM V2</span><span>{banner}</span></div>
  <header>
    <h1><em>{int(protocol["candidate_count"])}</em> actions × <em>{int(protocol["world_count_per_candidate"])}</em> worlds.<br>Execute one survivor.</h1>
    <section class="decision"><span>SELECTION DECISION</span><strong>{html.escape(str(selected))}</strong><small>{len(summary["qualifying_candidate_ids"])} candidate(s) passed every selected world.</small></section>
  </header>
  <section class="metrics">
    <div class="metric"><span>CANDIDATE-WORLD PAIRS</span><b>{int(summary["candidate_world_count"])}</b></div>
    <div class="metric"><span>QUALIFIED ACTIONS</span><b>{len(summary["qualifying_candidate_ids"])}</b></div>
    <div class="metric"><span>FORMAL TARGET</span><b>4,608</b></div>
    <div class="metric"><span>REPORT STATUS</span><b>{str(validation["smoke_status"]).upper()}</b></div>
  </section>
  <section class="matrix">
    <div class="matrix-head"><b>CANDIDATE × UNCERTAINTY WALL</b><span>Every row must be fully green to qualify</span></div>
    {''.join(row_markup)}
  </section>
  <footer><span>Protocol {protocol["protocol_sha256"]}</span><span>{html.escape(str(payload["claim_boundary"]))}</span></footer>
</main>
</body>
</html>
"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--html", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.report.read_text(encoding="utf-8"))
    render(payload, args.html)
    print(args.html)


if __name__ == "__main__":
    main()
