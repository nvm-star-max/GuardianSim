# Radeon Scale V3 Frozen Protocol

Date frozen: 2026-08-03
Status: implementation protocol; no V3 formal performance result exists yet

## Question

Can one AMD Radeon GPU sustain thousands of complete robot-world simulations,
repeatedly, at a scale large enough to make **Think thousands. Execute one.** a
measured compute claim rather than a visual slogan?

## Frozen workload

| Field | Frozen value |
|---|---:|
| Complete worlds per batch | 4,096; 8,192; 16,384 |
| Independent processes per batch | 5 |
| Warmup per process | 200 simulator steps |
| Measurement per process | 2,048 simulator steps |
| Measured processes | 15 |
| Total measured environment steps | 293,601,280 |
| Primary metric | P50 environment steps per wall-clock second |

Each process rebuilds the same headless scene: one Franka manipulator, one
table, and four active YCB entities per world. Cameras remain disabled. Build,
shader setup, kernel compilation, and warmup are excluded from throughput but
preserved in raw evidence.

The nested V2 trial contract declares a one-world compatibility baseline
because the reusable raw-trial validator requires it. The V3 suite never runs
or reports that entry; only the three frozen high-scale batches above are
measured.

## Statistics

For each batch the report preserves all five independent raw measurements and
derives minimum, P50, mean, P95, maximum, and population coefficient of
variation. Percentiles use linear interpolation at rank `(n - 1) * q`.

The report also preserves weighted mean GPU utilization, peak GPU utilization,
peak VRAM, device name, HIP/PyTorch/Genesis versions, logs, source commit,
protocol hash, report hash, and a SHA-256 evidence manifest.

No minimum throughput, utilization, or scaling threshold is declared. Results
are recorded even if throughput flattens or variance is unfavorable.

## Capacity preflight boundary

Separate 8,192- and 16,384-world runs used five warmup and ten measurement
steps only to confirm that the scenes fit and execute. Those short runs are not
performance evidence, are not merged into V3, and cannot be quoted as formal
throughput.

## Failure and resume rules

- A formal run starts in a new output directory.
- Existing JSON, logs, receipts, and checksums are never overwritten.
- A failed process stops the suite; its numbered attempt log remains evidence.
- Resume skips only raw trials that strictly validate against the same protocol
  and source commit.
- Batch order and repeat order are fixed.
- The final report is written only after all 15 raw trials pass validation.

## Claim boundary

The measured count is Genesis physics environment steps. It is not a training
dataset size, PPO experience count, inference-token count, independent safety
trial count, real-time-control guarantee, or physical-robot evidence.

Radeon Scale V3 measures the compute engine. The separate frozen Safety Swarm
and Gate 3.2 reports explain how GuardianSim uses that engine to choose one
eligible robot action or stop.
