# Gate 3.2 Radeon Cloud Engineering Smoke

Status: two-scenario prefix complete and schema-5-valid; raw archive retrieval
pending one manual browser download.

This smoke used frozen seeds `401–402` and commit `67d3235` on Radeon Cloud
instance `u-13907-735d71cb`. It is an engineering check only, not competition
performance evidence.

Verified cloud results:

- baseline repeatable safe completion: `2/2`;
- GuardianSim repeatable safe completion: `2/2`;
- clutter contacts: zero for both;
- mean clearance: baseline `0.0479732 m`, GuardianSim `0.0927164 m`;
- mean stability: baseline `0.902032`, GuardianSim `0.860738`;
- both selector decisions: `higher_margin_alternative`;
- planning wall time: `269.55 s` and `266.57 s`.

The schema-5 validator confirmed all 18 initial candidate measurements,
four observations per confirmed candidate, three final executions per
executed strategy, protocol identity, scenario order, timing, fingerprints,
aggregates, and stored summary.

The raw cloud archive is currently:

`/workspace/GuardianSim/outputs/gate-3-2/gate-3-2-smoke-evidence.tar.gz`

It contains:

- `smoke-report.json`;
- `smoke.log`;
- `smoke-validation.json`;
- `cloud-tests.log`;
- `smoke-sha256.txt`.

After manual download, extract these files into this directory, verify the
manifest locally, and replace this pending note with the verified file hashes.
