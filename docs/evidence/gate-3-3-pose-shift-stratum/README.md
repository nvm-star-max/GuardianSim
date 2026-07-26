# Gate 3.3 Pose-Shift Stratum Evidence

Evidence status: **complete engineering stratum; excluded from formal
performance claims**

This directory preserves the first complete six-scenario stratum from the
frozen Gate 3.3 breadth matrix. Seeds 501–506 cover three YCB target objects
across lateral- and radial-clutter layouts. The run started from an independent
report and did not resume or overwrite the earlier two-scenario smoke.

## Frozen identity

- Protocol SHA-256:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`
- Scenario-matrix SHA-256:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`
- Cloud checkout: `dac822a`
- Radeon Cloud instance: `u-13907-735d71cb`
- Stratum: `pose_shift`
- Seeds: 501–506

## Strictly validated outcomes

- Partial schema-6 validation passed `6/6`.
- Frozen stop reasons: none.
- Baseline safe completion: `4/6` (`66.67%`).
- GuardianSim safe completion: `6/6` (`100%`).
- Absolute safe-completion lift: `+33.33` percentage points.
- Baseline clutter contacts: `2/6`; GuardianSim clutter contacts: `0/6`.
- Both baseline contacts occurred in lateral-clutter layouts:
  - seed 503, lemon;
  - seed 505, plum.
- GuardianSim replaced the unsafe nominal action in both contact cases and
  completed the task without clutter contact.
- Mean observed clearance:
  - baseline: `0.026178 m`;
  - GuardianSim: `0.042806 m`;
  - difference: `+0.016628 m` (`+63.52%` relative).
- Mean stability:
  - baseline: `0.908395`;
  - GuardianSim: `0.905240`;
  - difference: `-0.003155`.
- GuardianSim safe stops: `0/6`.
- Mean planning wall time: `230.48 s` per scenario.

The complete stratum passed all predeclared engineering stop rules:

- GuardianSim task-failure rate was `0%`, not above `25%`;
- GuardianSim introduced no clutter-contact regression;
- no-safe-candidate / safe-stop rate was `0%`, not above `20%`;
- snapshot and strict validator checks passed.

These six scenarios are useful engineering evidence, but they are one
perturbation stratum with one execution per strategy. They do not establish a
robustness rate or statistical confidence interval.

## Scenario audit

| Seed | Object | Layout | Baseline | GuardianSim | Selected behavior |
|---:|---|---|---|---|---|
| 501 | banana | lateral | safe success | safe success | higher-margin alternative |
| 502 | banana | radial | safe success | safe success | higher-margin alternative |
| 503 | lemon | lateral | clutter contact | safe success | unsafe nominal replaced |
| 504 | lemon | radial | safe success | safe success | eligible nominal fallback |
| 505 | plum | lateral | clutter contact | safe success | unsafe nominal replaced |
| 506 | plum | radial | safe success | safe success | eligible nominal fallback |

## Integrity

Transferred archive:

`gate-3-3-pose-shift-stratum-evidence.tar.gz`

Cloud and local archive SHA-256:

`fba1e73b1bce8da0079547a312b90389f14ce3f41ee631e99b3571f4ceae780c`

Key raw-file hashes:

- `pose-shift-report.json`:
  `4b716814efae6f0fe659d5981a2538a6601c964a344b29aa3627b1d996c80413`
- `pose-shift.log`:
  `740540e7117d89c5a83992929ad3ddd26446ab14165aeb653f264d739f3d1ef3`
- `validation.txt`:
  `6c6b56c56ed44ce08c3c691f076be4e4f6a70e5442c83bc02b95d9fed37f2ff2`
- `final-check.json`:
  `f23d43608549f2c5f41ee1603f9bbcc66b5f3ad2156cb80bd01e7136aed21eb5`

The cloud-generated [`raw/SHA256SUMS`](raw/SHA256SUMS) manifest passed locally
for all seven listed evidence files. The schema-6 validator also reproduced
the cloud result locally:

```bash
(cd docs/evidence/gate-3-3-pose-shift-stratum/raw && \
  sed 's#outputs/gate-3-3-stratum/##' SHA256SUMS | shasum -a 256 -c -)

PYTHONPATH=. python3 scripts/validate_gate33_report.py \
  docs/evidence/gate-3-3-pose-shift-stratum/raw/pose-shift-report.json \
  --allow-partial
```
