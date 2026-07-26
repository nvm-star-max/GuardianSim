# Gate 3.3 — Multi-factor Uncertainty Breadth Smoke

Status: **frozen before cloud execution; two-scenario engineering smoke now
complete**

Protocol SHA-256:
`5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`

Exact scenario-matrix SHA-256:
`c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`

The canonical declaration is implemented in
[`guardian_sim/gate33_benchmark.py`](../guardian_sim/gate33_benchmark.py).
This implementation and document must be committed before any Gate 3.3 cloud
outcome is inspected. Gate 3.2 remains unchanged.

## Purpose and evidence boundary

Gate 3.2 demonstrated obstacle-aware selection on a frozen close-clutter
matrix. Gate 3.3 asks whether the system architecture still behaves sensibly
when several assumptions move outside that matrix.

This is a 24-scenario **engineering breadth smoke**, not formal performance
evidence. Its outcomes may expose defects, stop a later experiment, or motivate
an implementation fix. They must not be merged into Gate 3.2 or advertised as
an independent benchmark result.

## Frozen 24-scenario matrix

- New contiguous seeds: `501–524`.
- Four perturbation strata.
- Each stratum covers all three target objects and both clutter layouts once.
- One baseline and at most one GuardianSim final execution per scenario.
- Scenario order is stratum → object → layout.

| Stratum | Seeds | Physical or observation change |
| --- | --- | --- |
| pose shift | 501–506 | target XY up to ±2.5 cm and yaw up to ±35° |
| gap / bearing | 507–512 | clutter gap 6 or 24 mm; bearing offset −35° or +35° |
| dynamics extreme | 513–518 | friction ratio 0.55 or 1.10; mass ratio 1.55 or 0.70 |
| perception bias | 519–524 | deterministic target/obstacle XY bias inside declared 6 mm bounds |

The physical target and clutter poses remain separate from the perceived
poses. Candidate generation receives only the biased observation. Genesis
rollouts and final classification use the true scene.

## Frozen uncertainty certificate

For every candidate rollout:

1. Preserve the raw observed clearance and all physical diagnostics.
2. Compute the worst-case relative-position uncertainty as:

   `target position bound + obstacle position bound`.

3. Compute a certified lower bound:

   `observed clearance − relative-position uncertainty`.

4. Replace the selector's point clearance with that non-negative conservative
   lower bound.
5. Reject the action if any hard gate fails:
   - unreachable;
   - stability below `0.70`;
   - sampled physical overlap;
   - certified clearance below `0.010 m`.
6. Preserve a per-candidate risk certificate with the raw margin, uncertainty
   deduction, certified margin, thresholds, hard-safe decision, and explicit
   failed-gate names.

Normal strata use 2 mm target and 2 mm obstacle bounds. The perception-bias
stratum uses 6 mm per entity, yielding a 12 mm worst-case relative-position
deduction.

The existing Gate 3.2 18-action family, five-action shortlist, three
confirmation rollouts, conservative repeat aggregation, 0.02 success-margin
rule, and replace-or-safe-stop policy remain fixed. Safe-stop executes no
GuardianSim action and is not task success.

## Engineering endpoints

Diagnostics only:

- safe completion, task completion, contact, and safe-stop rates;
- observed clearance and stability;
- results by perturbation stratum;
- point-measurement versus certified-clearance decisions;
- planning and execution wall time.

No confidence interval or formal pass claim will be computed from this smoke.

## Frozen stop rules

Snapshot mismatch and validator failure stop immediately. Outcome-dependent
rules are evaluated only after each complete six-scenario stratum:

- GuardianSim task-failure rate above 25%;
- any GuardianSim clutter-contact regression where the paired baseline did not
  contact clutter;
- no representable hard-safe candidate / safe-stop rate above 20%.

If a rule triggers, preserve the partial report and investigate. Do not retune
thresholds using the observed prefix.

## Evidence and validation

Engineering prefix:

```bash
python scripts/run_gate33_breadth_smoke.py \
  --output outputs/gate-3-3/smoke-report.json \
  --max-new-scenarios 2

python scripts/validate_gate33_report.py \
  outputs/gate-3-3/smoke-report.json \
  --allow-partial
```

Schema 6 preserves:

- true and perceived target/obstacle positions;
- all 18 raw initial candidate measurements;
- all 18 certified metrics and risk certificates;
- every certified confirmation observation;
- selector decision, safe-stop state, physical final executions, scenario
  identity, snapshot fingerprint, protocol hashes, summary, stop reasons, and
  timing.

The strict validator recomputes every initial certificate from raw metrics and
the frozen scenario bound. It rejects scenario drift, certificate drift,
incomplete candidates, malformed confirmation evidence, selection/execution
contradictions, duplicate fingerprints, stored-summary drift, and
stored-stop-reason drift.

## Interpretation

- A positive smoke permits design of a separately frozen larger robustness
  gate; it does not itself prove broad generalization.
- A negative smoke is useful evidence and must be preserved.
- Do not change this protocol after inspecting any Gate 3.3 cloud outcome.
- All results remain Genesis simulation evidence on an AMD Radeon GPU.
- Do not proceed automatically to the 120-scenario Stage 2 gate.

## Post-declaration smoke record

After this protocol and its hashes were committed, the owner approved a
two-scenario engineering prefix. Seeds 501–502 passed partial schema-6
validation with no stop reason. The raw evidence, including two failed
pre-write validator attempts that produced no report, is preserved at
[`evidence/gate-3-3-smoke/README.md`](evidence/gate-3-3-smoke/README.md).

This record does not change the declaration above and is not a formal
performance claim.

The owner subsequently approved an independent run of the complete
`pose_shift` stratum. Seeds 501–506 passed partial schema-6 validation with no
stop reason. Baseline safe completion was 4/6 with two lateral-clutter
contacts; GuardianSim safe completion was 6/6 with no clutter contact or safe
stop. The raw evidence is preserved at
[`evidence/gate-3-3-pose-shift-stratum/README.md`](evidence/gate-3-3-pose-shift-stratum/README.md).

This post-declaration record does not alter the frozen protocol, matrix,
thresholds, or engineering-only claim boundary.
