# Radeon Scale V2 Formal Evidence

This directory preserves the completed 2026-07-31 Radeon Scale V2 run from AMD
Radeon Cloud.

## Result

The frozen suite ran each declared batch exactly once:

`1 / 16 / 64 / 256 / 512 / 1,024 / 2,048 / 4,096`

At 4,096 simultaneous full Franka/table/four-YCB scenes it measured:

- `50,331,648` environment steps;
- `152,099.018` environment-steps/s;
- `1,028.069×` speedup over the one-world measurement;
- `25.099%` parallel efficiency;
- `98.651%` mean and `99%` peak GPU utilization;
- `6,706,667,520` peak VRAM bytes, approximately `6.25 GiB`.

The complete eight-batch sweep measured `98,512,896` environment steps. Strict
schema-2 validation passed, and every file listed in `raw/SHA256SUMS` passed
checksum verification.

## Claim boundary

This is a sustained Genesis physics-throughput benchmark after a separate
warmup. Environment steps are not training examples, independent safety
trials, dataset rows, or physical-robot evidence. Safety outcomes remain in
the separately frozen Gate 3.2 and Safety Swarm reports.

## Receipts

- Source commit: `3d8021a237ca0dfca41c98df1b492b7b9a523b4f`
- Frozen protocol SHA-256:
  `bcb91e081b196a5b6274ce1efd461d2005f1c1505dbd7020e9fbbaab0bb536e8`
- Canonical report SHA-256:
  `971769c6a051f6b2794982a02828601e91406320023a90bf85fc28103fa8b742`
- Evidence archive SHA-256:
  `71b7b0a2958444ec4d6b35831684223b38123291a54c8debbf25ed77a53d88de`
- Strict report: [`raw/report.json`](raw/report.json)
- Validation receipt: [`raw/validation.json`](raw/validation.json)
- File manifest: [`raw/SHA256SUMS`](raw/SHA256SUMS)
- Validator output:
  [`radeon-scale-v2-formal-strict-validation-20260731T0615Z.txt`](radeon-scale-v2-formal-strict-validation-20260731T0615Z.txt)
- Checksum audit:
  [`radeon-scale-v2-formal-checksums-20260731T0615Z.txt`](radeon-scale-v2-formal-checksums-20260731T0615Z.txt)
