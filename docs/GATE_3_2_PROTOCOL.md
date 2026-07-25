# Gate 3.2 — Obstacle-aware Repeatable Safety Benchmark

Status: **predeclared locally; no Gate 3.2 Radeon Cloud outcome has been
inspected**

Protocol SHA-256:
`8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`

Exact scenario-matrix SHA-256:
`69f87994b87f2def788cd944ad75210cdeddeafcaa3d0a3844fef04efca9cb03`

The canonical declaration is implemented in
[`guardian_sim/gate32_benchmark.py`](../guardian_sim/gate32_benchmark.py).
This implementation and document must be committed before any Gate 3.2 cloud
result is inspected.

## Why this gate exists

Gate 3.1 preserved a negative primary result:

- GuardianSim safe completion was 18/30 versus baseline 19/30;
- mean clearance improved by 43.67%, but contact remained 10/30 for both;
- lemon/lateral and plum/lateral produced 5/5 contacts for both strategies;
- GuardianSim had two additional unstable independent executions.

The raw evidence identified two separable defects:

1. the ±45°, ±2 cm action family could not represent a safe grasp in some
   lateral-clutter geometries;
2. the old selector could fall back to a nominal candidate already observed to
   overlap clutter, and one final execution was still allowed to decide the
   scenario result.

Gate 3.2 tests a new policy on unseen seeds. Gate 3.1 remains unchanged and is
not reused as the formal test set.

## Frozen scenario matrix

- Pick objects: banana, lemon, and plum.
- Layouts: lateral clutter and radial clutter.
- Five repeats per object/layout cell.
- Total paired scenarios: 30.
- New contiguous seeds: `401–430`.
- Target XY/yaw, friction, mass, clutter gap, parking rules, and shared
  baseline/GuardianSim snapshot construction remain the same as Gate 3.1.

| Cell | Seeds |
| --- | --- |
| banana / lateral | 401–405 |
| banana / radial | 406–410 |
| lemon / lateral | 411–415 |
| lemon / radial | 416–420 |
| plum / lateral | 421–425 |
| plum / radial | 426–430 |

## Frozen 18-action family

The nominal action is retained exactly:

- yaw `0°`;
- no target retreat;
- pregrasp height `0.10 m`.

Eight additional centered actions use yaw:

`-90°, -67.5°, -45°, -22.5°, 22.5°, 45°, 67.5°, 90°`

Nine obstacle-retreating actions use all nine yaws including `0°`. Their target
XY is shifted `0.025 m` along the normalized vector from the obstacle toward
the target, so the shift always moves away from the declared clutter object.

All non-nominal actions use:

- pregrasp height `0.14 m`;
- gripper width `0.06 m`;
- top-down grasp orientation.

The retreat is part of the executed grasp target, not merely a scoring
heuristic.

## Frozen safety-first selector

1. Execute one initial rollout for all 18 candidates.
2. Before ranking, hard-filter candidates that fail any requirement:
   - reachability `1.0`;
   - stability at least `0.70`;
   - sampled clutter clearance at least `0.010 m`;
   - no sampled non-support overlap.
3. Shortlist the top five hard-safe candidates and include nominal for explicit
   counterfactual evidence.
4. Run three additional confirmations per shortlisted candidate, giving four
   observations including the initial rollout.
5. Aggregate pessimistically using minimum clearance/reachability/alignment/
   stability and maximum path length/uncertainty.
6. If nominal is hard-safe, an alternative must exceed it by at least `0.02`
   robust success probability; otherwise execute nominal.
7. If nominal is not hard-safe, execute the highest-ranked hard-safe
   alternative without requiring the `0.02` margin.
8. If no candidate is hard-safe, issue `safe_stop` and execute no GuardianSim
   action. Safe-stop is not task success or safe completion.

The baseline always executes the unchanged nominal action.

## Repeated independent execution

For every scenario:

- baseline executes nominal three times from the same frozen episode snapshot;
- GuardianSim executes its selected candidate three times from that snapshot;
- a GuardianSim safe-stop has zero physical executions and is recorded
  separately.

The primary scenario outcome is **repeatable safe completion**, requiring all
three independent executions to:

- be reachable;
- retain lift stability of at least `0.70`;
- avoid clutter overlap;
- maintain at least `0.010 m` sampled clutter clearance.

Primary endpoint:

- paired repeatable-safe-completion rate difference,
  `GuardianSim rate - baseline rate`.

Secondary endpoints:

- per-execution safe-completion rate;
- repeatable task-success rate;
- clutter-contact rate;
- safe-stop rate;
- mean clutter clearance and retained-lift stability;
- decision/failure taxonomy and wall time.

## Evidence and validation

Technical smoke prefix:

```bash
python scripts/run_gate32_benchmark.py \
  --output outputs/gate-3-2/report.json \
  --max-new-scenarios 2

python scripts/validate_gate32_report.py \
  outputs/gate-3-2/report.json \
  --allow-partial
```

Formal resume:

```bash
python scripts/run_gate32_benchmark.py \
  --output outputs/gate-3-2/report.json

python scripts/validate_gate32_report.py \
  outputs/gate-3-2/report.json
```

Schema 5 preserves:

- all 18 initial candidate metrics;
- every confirmation observation;
- selector decision and safe-stop state;
- three independent execution records per executed strategy;
- scenario-level repeatability aggregates;
- protocol, scenario order, snapshot fingerprints, and timing.

The validator rejects protocol drift, scenario reordering, duplicate
fingerprints, incomplete 18-candidate initial evidence, missing confirmation
rollouts, duplicate or missing execution-repeat indices, safe-stop/execution
contradictions, aggregate mismatch, and stored-summary mismatch. Every
resumable checkpoint is validated before it is written.

## Interpretation and stopping rules

- Do not change this protocol after inspecting any Gate 3.2 cloud outcome.
- Do not claim safe-stop as successful task completion.
- Do not claim reduced contact from higher clearance alone.
- Preserve a negative or neutral result.
- All results remain Genesis simulation evidence on an AMD Radeon GPU.
- Cloud smoke is only an engineering gate; no performance claim may use its
  first two scenarios.
