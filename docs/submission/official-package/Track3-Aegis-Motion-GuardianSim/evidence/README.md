# Supplemental Radeon Evidence

These machine-readable reports support the separate Radeon compute section in
the technical report. They do not modify the frozen Gate 3.2 safety benchmark.

## Parallel physics scale

- Full scene per world: Franka, table, and four active YCB entities.
- Frozen batch sizes: 1, 16, 64, 256, 512, 1,024, 2,048, and 4,096 worlds.
- Fixed timed interval: 12,288 measured steps after 200 warmup steps.
- Total measured sweep: 98,512,896 environment steps.
- Largest point: 152,099.018 environment-steps/s at 4,096 worlds.
- Speedup at 4,096 worlds: 1,028.069x.
- Largest-point GPU use: 98.651% mean and 99% peak.
- Largest-point peak VRAM: approximately 6.25 GiB.

`radeon-scale-report.json` contains the raw measurements and ROCm telemetry.
`radeon-scale-validation.json` records the strict validator result.

## Historical bounded Parallel Futures smoke

- Candidate actions: 18.
- Repeats per candidate: 3.
- Simultaneous Genesis worlds: 54.
- Batched execution: 12.839 seconds.
- Hard-safe futures: 32.
- Rejected futures: 22.

`parallel-futures-report.json` contains the per-future measurements and ROCm
telemetry. `parallel-futures-validation.json` records the strict validator
result.

This earlier run is retained as an execution-path engineering receipt. It is
not the project's main scale result. The 54 futures are 18 candidates times
three repeats, not 54 independent scenarios.

## Safety Swarm V2 formal decision run

- Candidate actions: 18.
- Frozen uncertainty worlds per candidate: 256.
- Candidate-world pairs: 4,608.
- Candidates passing all 256 worlds: 5.
- Selected action: 256/256 safe worlds and zero sampled clutter contacts.
- Measured execution: 2,299,392 environment steps in 226.676 seconds.
- Radeon telemetry: 73.406% mean and 97% peak GPU utilization.

`safety-swarm-v2-summary.json` is the compact derivative used for review.
`safety-swarm-v2-validation.json` is the strict validation receipt. The full
5.7 MB report, logs, protocol, environment, and recursive checksums remain in
the dedicated source repository under
`docs/evidence/safety-swarm-v2-formal-2026-07-30`.

The 4,608 pairs form a candidate-by-uncertainty engineering stress-test
population. They are not 4,608 independent robot trials and not a
physical-robot safety guarantee.

## Claim boundary

Scale V2 environment steps measure sustained Genesis physics throughput after
warmup. They are not PPO samples, training examples, dataset rows, independent
safety trials, or physical-robot executions. The Scale V2, Safety Swarm V2,
and Gate 3.2 units remain separate throughout the report and package.
