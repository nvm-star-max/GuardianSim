# Radeon Scale V2 Result

- Date: 2026-07-31
- Environment: AMD Radeon Cloud, one `gfx1100` Radeon GPU, ROCm/HIP
- Source commit: `3d8021a237ca0dfca41c98df1b492b7b9a523b4f`

## What was measured

The frozen suite built a full headless Genesis manipulation scene per
environment: Franka, table, and four active YCB entities. After a separate
warmup, each batch ran 12,288 measured steps. Scene build, shader setup, and
JIT warmup were outside the timed interval.

Eight predeclared batches ran once:

| Worlds | Environment steps/s | Speedup | Parallel efficiency | Mean / peak GPU |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 147.946 | 1.000× | 100.000% | 95.037% / 97% |
| 16 | 2,214.149 | 14.966× | 93.537% | 95.397% / 97% |
| 64 | 8,704.403 | 58.835× | 91.929% | 95.419% / 96% |
| 256 | 35,637.980 | 240.884× | 94.095% | 95.009% / 96% |
| 512 | 56,928.068 | 384.789× | 75.154% | 96.352% / 97% |
| 1,024 | 96,589.308 | 652.867× | 63.757% | 96.290% / 97% |
| 2,048 | 136,859.540 | 925.062× | 45.169% | 97.341% / 98% |
| 4,096 | 152,099.018 | 1,028.069× | 25.099% | 98.651% / 99% |

The curve continues rising through 4,096 worlds, while parallel efficiency
falls after 256 worlds. That is the saturation story: the GPU reaches 99%
utilization and still gains throughput, but each doubling yields a smaller
increment.

## Headline receipts

- Largest batch: `4,096` simultaneous full scenes
- Largest-batch workload: `50,331,648` environment steps
- Complete sweep: `98,512,896` environment steps
- Peak throughput: `152,099.018 environment-steps/s`
- Largest-batch speedup: `1,028.069×`
- Largest-batch GPU use: `98.651%` mean, `99%` peak
- Peak VRAM: `6,706,667,520` bytes, approximately `6.25 GiB`

## Integrity

- Frozen protocol:
  `bcb91e081b196a5b6274ce1efd461d2005f1c1505dbd7020e9fbbaab0bb536e8`
- Canonical report:
  `971769c6a051f6b2794982a02828601e91406320023a90bf85fc28103fa8b742`
- Evidence archive:
  `71b7b0a2958444ec4d6b35831684223b38123291a54c8debbf25ed77a53d88de`
- Strict schema-2 validation: passed
- Failed or retried formal batches: none

Raw evidence is preserved under
[`docs/evidence/radeon-scale-v2-formal-20260731`](../evidence/radeon-scale-v2-formal-20260731).

## Claim boundary

The reported unit is a Genesis environment step. It is not a PPO training
sample, a dataset row, an independent safety trial, or a physical-robot
execution. The benchmark demonstrates how one Radeon GPU can evaluate a large
population of simulated physical futures; GuardianSim's safety results are
reported separately.
