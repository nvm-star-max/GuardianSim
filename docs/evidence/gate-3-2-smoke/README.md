# Gate 3.2 Radeon Cloud Engineering Smoke

Status: two-scenario prefix complete, raw evidence preserved, and independently
schema-5-validated on both Radeon Cloud and local macOS.

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

The downloaded cloud archive SHA-256 is:

`f2545cfe89708e2626976d357eb7aabab0b68c0b45913005a23675878b2a61dd`

Preserved raw files:

- `smoke-report.json`:
  `8ec01ff4b2bc19ee5512796f1609fb8e86b6df082dade728713c1560b2f9ac23`;
- `smoke.log`:
  `49832528b2d0340b3292d845af1c1cd2566d59cb45f2d3eaae85ddc4cabd39c5`;
- `smoke-validation.json`:
  `cf390121e3c62ac9d6fa4daa6eae67b648888aea6d9d06fada1401d6eb2f204b`;
- `cloud-tests.log`:
  `dd79d9a7a28e84e5038e23be17f8bb20c8679ceb9b5f21ee5fe0eaea68779353`;
- `smoke-sha256.txt`, the cloud-generated manifest.

Local verification artifacts:

- `local-validation.json`, generated from the raw report with the same frozen
  validator;
- `local-tests.log`, recording 39/39 passing tests.

The local validator confirmed the same protocol SHA, completed episode count,
and complete stored summary as the cloud validator.
