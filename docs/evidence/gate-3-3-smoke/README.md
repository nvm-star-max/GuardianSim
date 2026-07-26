# Gate 3.3 Radeon Cloud Engineering Smoke Evidence

Evidence status: **engineering smoke only; excluded from formal performance
claims**

This directory preserves the first two scenarios from the frozen Gate 3.3
multi-factor uncertainty breadth matrix. Seeds 501–502 are both in the
`pose_shift` stratum. The run does not alter or extend Gate 3.2.

## Frozen identity

- Protocol SHA-256:
  `5f9497c363c32f8bbabb62e395d5814958e273d3b6d235fb46a7a5f23be6b130`
- Scenario-matrix SHA-256:
  `c934f3427a937f2cc8594a1408e97d1ed9bf3692fa41af066f2fb8652435e983`
- Successful cloud implementation commit: `5ec31f3`
- Radeon Cloud instance: `u-13907-735d71cb`
- Requested prefix: 2/24 scenarios

## Verified engineering outcomes

- Partial schema-6 validation passed `2/2`.
- Stop reasons: none.
- Baseline safe completion: `2/2`.
- GuardianSim safe completion: `2/2`.
- Clutter contacts: zero for both.
- Mean observed clearance:
  - baseline: `0.062413 m`;
  - GuardianSim: `0.090384 m`.
- Mean stability:
  - baseline: `0.881576`;
  - GuardianSim: `0.879571`.
- Both decisions were `higher_margin_alternative`.
- Selected risk certificates:
  - seed 501: `94.467 mm` observed − `4 mm` relative-position bound =
    `90.467 mm` certified clearance;
  - seed 502: `91.469 mm` observed − `4 mm` relative-position bound =
    `87.469 mm` certified clearance.
- Planning wall time:
  - seed 501: `246.96 s`;
  - seed 502: `292.70 s`.

These two scenarios verify plumbing, true/perceived-pose separation,
certificate persistence, strict validation, and physical execution. They are
too small and intentionally excluded from any robustness-rate claim.

## Preserved failed-launch audit trail

Two earlier launches completed physical work for seed 501 but stopped before
the first atomic report write:

1. `failed-prewrite-validator.log` — the new validator accepted only
   JSON-round-tripped list/native-float poses, not the equivalent in-memory
   tuple/NumPy-real representation.
2. `failed-numpy-bool-validator.log` — an internal certificate comparison did
   not use the project NumPy-aware JSON adapter.

Neither attempt produced a report, so neither contributes an outcome. Their
logs and PIDs are retained. Both fixes were covered by regression tests and
changed no scenario, threshold, selector, protocol payload, or matrix.

## Integrity

Downloaded archive:

`gate-3-3-smoke-evidence.tar.gz`

Archive SHA-256:

`f2040a53f4fbf2172a94df1003feac1137bcf4684bc9281d60f8991780da83ea`

Key raw-file hashes:

- `smoke-report.json`:
  `42c04b9ab500f3d113e96ca2739dbc1958b9ac94f6ad9d3ca42e3b860730360c`
- `smoke.log`:
  `7007eb2988e4bd46890f7a023f51265ac94875e1de5ec5ebb1a7c9f8e831d39a`
- `validation.txt`:
  `115150c90346b077a72ed2f5a5165b68cf520fe075ebf0e70178f061389978d8`

The cloud-generated [`raw/SHA256SUMS`](raw/SHA256SUMS) manifest passed locally
for all nine listed evidence files.

Local reproduction:

```bash
(cd docs/evidence/gate-3-3-smoke/raw && \
  sed 's#outputs/gate-3-3/##' SHA256SUMS | shasum -a 256 -c -)

PYTHONPATH=. python3 scripts/validate_gate33_report.py \
  docs/evidence/gate-3-3-smoke/raw/smoke-report.json \
  --allow-partial
```
