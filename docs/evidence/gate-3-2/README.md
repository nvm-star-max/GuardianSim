# Gate 3.2 Radeon Cloud Formal Evidence

This directory preserves the complete Gate 3.2 formal Radeon Cloud result and
the audit trail that explains why the earlier two-episode engineering smoke was
not appended across a new Genesis process.

## Verified identity

- Schema: `5`
- Formal episodes: `30/30`, seeds `401–430`
- Protocol SHA-256:
  `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`
- Scenario-matrix SHA-256:
  `69f87994b87f2def788cd944ad75210cdeddeafcaa3d0a3844fef04efca9cb03`
- Cloud source snapshot: commit `67d3235`
- Evidence archive SHA-256:
  `57b53cda9d4352cb2d99ae9da01e1051840705725002a9e32e4076493b7b84ad`

`formal-validation.json` is the output of the strict, complete schema-5
validator. The archive and every file listed in `formal-sha256.txt` were
rechecked after download.

## Verified formal result

- Repeatable safe completion:
  - baseline: `18/30` (`60%`);
  - GuardianSim: `30/30` (`100%`);
  - paired absolute lift: `+40.00` percentage points.
- Independent execution safe completion:
  - baseline: `58/90`;
  - GuardianSim: `90/90`.
- Clutter-contact executions:
  - baseline: `30`;
  - GuardianSim: `0`.
- Mean sampled clutter clearance:
  - baseline: `0.023191 m`;
  - GuardianSim: `0.046003 m` (`+98.36%`).
- Mean retained-lift stability:
  - baseline: `0.892762`;
  - GuardianSim: `0.905099`.
- GuardianSim decision taxonomy:
  - `higher_margin_alternative`: `11`;
  - `unsafe_nominal_replaced`: `10`;
  - `eligible_nominal_fallback`: `9`.
- Mean planning time: `264.95 s` per scenario.
- Mean independent execution time:
  - baseline: `9.08 s`;
  - GuardianSim: `8.94 s`.

Each strategy received three independent physical executions per scenario.
Repeatable safe completion required all three to pass reachability, retained
stability, clutter-overlap, and minimum-clearance checks.

## Smoke/formal separation

The original two-episode smoke report is preserved unchanged as
`smoke-report.json`. Strict resume validation rejected two attempts to append
it from a newly initialized Genesis process because the captured base-scene
snapshot fingerprint differed. The rejected logs are preserved as
`formal-attempt-*-fingerprint-mismatch.log`.

To avoid mixing episodes derived from different base snapshots, the formal run
used the untouched `formal-report.json` output path and ran all 30 scenarios in
one process. No `--fresh` flag was used, the smoke report was not overwritten,
and the frozen protocol, thresholds, and scenario order were not changed.

## Files

- `formal-report.json` — complete raw schema-5 report.
- `formal.log` — full Radeon Cloud runner log.
- `formal-validation.json` — strict validator output.
- `formal-environment.txt` — cloud commit and AMD/ROCm environment record.
- `formal-sha256.txt` — cloud-generated file manifest.
- `gate-3-2-formal-evidence.tar.gz` — downloaded source archive.
- `formal-attempt-*.log`, `formal-*-check.txt` — launch and resume audit trail.
- `smoke-report.json`, `smoke.log`, `smoke-validation.json` — preserved smoke
  evidence included to prove separation and non-overwrite.

The Radeon Cloud instance was intentionally left running per the owner's
instruction.
