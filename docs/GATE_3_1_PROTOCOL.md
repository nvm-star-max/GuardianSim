# Gate 3.1 — Multi-object Adversarial Safety Benchmark

Status: **predeclared; no Radeon Cloud outcome has been inspected**

Protocol SHA-256:
`472bb6ea13984dff02124c091ac8d94c67154bbe68858bb782aed8014d2afbba`

Exact scenario-matrix SHA-256:
`b3ba08b367a0c634f66ddbba8670311c9b449aaa4ad7ee55d418bca7c2147936`

The canonical declaration is implemented in
[`guardian_sim/adversarial_benchmark.py`](../guardian_sim/adversarial_benchmark.py).
The commit containing this document and implementation must precede every
formal Gate 3.1 cloud result.

## Question

Does repeatability-aware counterfactual selection improve safe completion over
the nominal scripted grasp when object identity, close-clutter geometry,
friction, mass, target position, and target yaw vary?

Gate 2.8 could only show equal 20/20 task success and higher mean clearance on
one banana-centered distribution. Gate 3.1 is designed to test actual
generalization and to make near-miss behavior an explicit outcome rather than
using mean clearance alone.

## Frozen matrix

- Pick objects: `011_banana`, `014_lemon`, `018_plum`.
- Controlled layouts: `lateral_clutter`, `radial_clutter`.
- Repeats per object/layout cell: 5.
- Total paired episodes: 30.
- Seeds: contiguous `301–330`.
- The exact 30 sampled XY/yaw/friction/mass tuples are covered by the
  scenario-matrix hash above.
- Both strategies receive the same settled episode snapshot.
- Baseline: nominal `yaw_+00.0_offset_+0.000`.
- GuardianSim: the unchanged Gate 2.8 robust selector.

| Cell | Seeds |
| --- | --- |
| banana / lateral | 301–305 |
| banana / radial | 306–310 |
| lemon / lateral | 311–315 |
| lemon / radial | 316–320 |
| plum / lateral | 321–325 |
| plum / radial | 326–330 |

## Controlled challenge construction

Each scenario:

1. jitters target XY by at most `±0.010 m`;
2. jitters target yaw by at most `±15°`;
3. samples a shared friction ratio in `[0.75, 0.95]`;
4. samples target mass ratio in `[0.90, 1.25]`;
5. places one declared small obstacle beside the target with a conservative
   footprint-to-footprint gap of `0.012 m`;
6. parks non-participating objects at declared far-table positions.

The target/obstacle center distance is calculated from both conservative YCB
footprint radii plus the declared gap. This prevents initial object penetration
from becoming fake robot-failure evidence.

Primary obstacles:

- banana → plum;
- lemon → plum;
- plum → lemon.

## Frozen policy thresholds

The Gate 2.8 selector remains unchanged:

- 15 initial candidates;
- top-three shortlist plus nominal;
- two additional confirmation rollouts;
- minimum worst-observed stability `0.60`;
- minimum robust success advantage over nominal `0.02`;
- otherwise nominal fallback.

These values must not be changed after any Gate 3.1 result is inspected.

## Outcomes

Primary endpoint:

- paired safe-completion rate difference,
  `GuardianSim rate - baseline rate`.

`task_succeeded` requires:

- reachable execution;
- retained-lift stability at least `0.60`;
- no observed non-support clutter overlap.

`safe_completion` additionally requires:

- minimum sampled non-support clutter clearance at least `0.010 m`.

Secondary endpoints:

- ordinary task-success rate;
- clutter-contact rate;
- mean clutter clearance;
- mean retained-lift stability;
- failure taxonomy by object/layout cell;
- planning and independent-execution wall time.

The `0.010 m` margin is a predeclared safety boundary, not an observed-data
cutoff. Task success remains reported separately so a close but successful
grasp cannot be silently relabeled as a dropped object.

## Evidence and validation

Run on Radeon Cloud:

```bash
python scripts/run_gate31_adversarial_benchmark.py \
  --output outputs/gate-3-1/report.json
```

For a bounded smoke prefix without changing the protocol:

```bash
python scripts/run_gate31_adversarial_benchmark.py \
  --output outputs/gate-3-1/report.json \
  --max-new-scenarios 2
```

Resume by running the same command without `--fresh`. Validate a partial prefix:

```bash
python scripts/validate_gate31_report.py \
  outputs/gate-3-1/report.json \
  --allow-partial
```

Validate the final 30-episode report:

```bash
python scripts/validate_gate31_report.py outputs/gate-3-1/report.json
```

The validator rejects protocol drift, reordered scenarios, missing independent
execution evidence, duplicate fingerprints, incomplete formal reports, and
stored summaries that do not match raw episodes.

## Interpretation rules

- Do not claim GuardianSim improves task success unless the paired task-success
  result supports that statement.
- Do not claim reduced collision rate from clearance alone; report contacts and
  margin violations separately.
- Do not tune thresholds or remove failed cells after inspecting outcomes.
- Preserve a negative result and diagnose it before defining a later gate.
- All results remain Genesis simulation evidence, not physical-robot evidence.
