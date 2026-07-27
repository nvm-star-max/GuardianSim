# Gate 3.3 Two-Strata Engineering Evidence

Evidence status: **two complete engineering strata; excluded from formal
performance claims**

This directory preserves one independent, continuous 12-scenario prefix from
the frozen Gate 3.3 breadth matrix. It covers all `pose_shift` and
`gap_bearing` scenarios, seeds 501–512. The run started from zero in one
Radeon Cloud process. It did not splice or resume the earlier independent
six-scenario report.

## Frozen identity

- Schema: `6`
- Protocol SHA-256:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`
- Scenario-matrix SHA-256:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`
- Cloud checkout:
  `4cbbdf64ed3557e4e379a5bf7d3bc4028e231a80`
- Radeon Cloud instance: `u-13907-735d71cb`
- Strata: `pose_shift`, `gap_bearing`
- Seeds: 501–512
- Scenario coverage per stratum: three target objects × two clutter layouts

## Validation and overall result

- The process completed normally at `12/12`.
- Cloud and local strict partial schema-6 validators passed `12/12`.
- The protocol and matrix hashes match the frozen declaration exactly.
- Stored and recomputed frozen `stop_reasons`: `[]`.
- Baseline:
  - 12 physical executions;
  - 7 safe task completions;
  - 4 clutter-contact classifications;
  - 1 clearance violation;
  - mean clearance `0.019033 m`;
  - mean stability `0.913322`.
- GuardianSim:
  - 10 physical executions, all safe task completions;
  - 2 explicit safe stops where no hard-safe action was available;
  - zero clutter contacts and zero clearance-violating executions;
  - mean clearance across executed actions `0.043547 m`;
  - mean stability across executed actions `0.916772`.
- Decision distribution:
  - 4 unsafe-nominal replacements;
  - 4 eligible nominal fallbacks;
  - 2 higher-margin alternatives;
  - 2 safe stops.
- Mean planning wall time: `221.53 s` per scenario.

The stored summary reports an absolute safe-completion-rate lift of `+41.67`
percentage points. That statistic uses only executed GuardianSim actions in
its safe-completion denominator and reports safe stops separately. For
judge-facing clarity, use the raw counts above: ten safe executions, two safe
stops, and no unsafe GuardianSim execution. This remains an engineering smoke,
not a formal performance estimator.

## Result by stratum

### Pose shift — seeds 501–506

- Baseline: 4/6 safe completions and 2 lateral-clutter contacts.
- GuardianSim: 6/6 safe completions, zero contacts, zero safe stops.
- Mean clearance:
  - baseline `0.027648 m`;
  - GuardianSim `0.046696 m`.
- Mean stability:
  - baseline `0.914622`;
  - GuardianSim `0.904200`.
- Mean planning wall time: `215.67 s`.

This independently reproduces the earlier complete pose-shift stratum's
qualitative result.

### Gap and obstacle bearing — seeds 507–512

- Baseline:
  - 3/6 safe task completions;
  - 2 clutter contacts;
  - 1 non-contact clearance violation;
  - mean clearance `0.010417 m`;
  - mean stability `0.912022`.
- GuardianSim:
  - 4/4 executed actions were safe task completions;
  - 2/6 scenarios safe-stopped before physical execution;
  - zero clutter contacts and zero clearance-violating executions;
  - mean executed-action clearance `0.038823 m`;
  - mean executed-action stability `0.935631`.
- Mean planning wall time: `227.39 s`.

The two safe stops are the lateral-clutter lemon and plum cases. No candidate
in the frozen action family satisfied all hard safety gates. GuardianSim
therefore refused to execute rather than convert uncertainty into contact.
This is correct fail-safe behavior, but the `33.33%` isolated-stratum
safe-stop/task-noncompletion rate is an important action-space coverage
limitation.

## Scenario audit

| Seed | Stratum | Object | Layout | Baseline | GuardianSim | Decision |
|---:|---|---|---|---|---|---|
| 501 | pose shift | banana | lateral | safe success | safe success | higher-margin alternative |
| 502 | pose shift | banana | radial | safe success | safe success | higher-margin alternative |
| 503 | pose shift | lemon | lateral | clutter contact | safe success | unsafe nominal replaced |
| 504 | pose shift | lemon | radial | safe success | safe success | eligible nominal fallback |
| 505 | pose shift | plum | lateral | clutter contact | safe success | unsafe nominal replaced |
| 506 | pose shift | plum | radial | safe success | safe success | eligible nominal fallback |
| 507 | gap/bearing | banana | lateral | clearance violation | safe success | unsafe nominal replaced |
| 508 | gap/bearing | banana | radial | safe success | safe success | unsafe nominal replaced |
| 509 | gap/bearing | lemon | lateral | clutter contact | safe stop | no hard-safe action |
| 510 | gap/bearing | lemon | radial | safe success | safe success | eligible nominal fallback |
| 511 | gap/bearing | plum | lateral | clutter contact | safe stop | no hard-safe action |
| 512 | gap/bearing | plum | radial | safe success | safe success | eligible nominal fallback |

## Frozen stop-rule interpretation

The schema-6 implementation evaluates the frozen rates on the cumulative
prefix at each six-scenario boundary. At 12 scenarios, GuardianSim has two
task noncompletions and two safe stops, both `16.67%`, so the stored and
strictly recomputed stop-reason list is empty.

When `gap_bearing` is inspected as an isolated stratum, its task
noncompletion and safe-stop rates are both `2/6 = 33.33%`, above the protocol's
numeric `25%` and `20%` warning thresholds. This isolated diagnostic does not
rewrite the frozen report or its cumulative stop-rule implementation. It does
justify stopping before the remaining two strata and improving coverage only
under a future, separately declared protocol.

## Rejected Seed 503 visual replays

The archive also preserves both Seed 503 replay attempts:

- the first replay regenerated the scene geometry;
- the second reconstructed target and obstacle geometry from the report.

Both reproduced the baseline contact. Neither reproduced the formal
GuardianSim clearance:

- formal GuardianSim clearance: `24.0836 mm`;
- first replay: `2.8406 mm`;
- second replay: `3.0122 mm`.

The hard claim-boundary check rejected both attempts. Their logs, PID files,
and diagnostic JSON are preserved as reproducibility diagnostics only. They
are not presentation videos, statistical trials, or performance evidence.

## Integrity

Transferred archive:

`gate-3-3-two-strata-evidence.tar.gz`

Cloud and local archive SHA-256:

`49ce9196de91f997f7233a4f4533e94292d0b502e8b2cc85fdbeac6173694595`

All 14 files in the cloud-generated `raw/SHA256SUMS` manifest passed local
SHA-256 verification. The archive includes:

- preflight, report, process PID, and complete log;
- cloud validation output and exit status;
- final summary and frozen-protocol identity;
- replay claim-boundary statement;
- two rejected replay logs, PID files, and diagnostics.

Local reproduction:

```bash
(cd docs/evidence/gate-3-3-two-strata/raw && \
  sed \
    -e 's#  outputs/gate-3-3-two-strata/#  #' \
    -e 's#  outputs/demo/#  #' \
    SHA256SUMS | shasum -a 256 -c -)

PYTHONPATH=. python3 scripts/validate_gate33_report.py \
  docs/evidence/gate-3-3-two-strata/raw/two-strata-report.json \
  --allow-partial
```
