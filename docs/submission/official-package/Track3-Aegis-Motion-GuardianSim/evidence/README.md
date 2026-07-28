# Supplemental Radeon Evidence

These machine-readable reports support the separate Radeon compute section in
the technical report. They do not modify the frozen Gate 3.2 safety benchmark.

## Parallel physics scale

- Fixed batch sizes: 1, 16, 64, and 256 Genesis worlds.
- Fixed timed interval: 1,000 steps per world after 100 warmup steps.
- Total timed workload: 337,000 environment steps.
- Largest point: 35,166.1 environment-steps/s.
- Speedup at 256 worlds: 228.16x.
- Parallel efficiency at 256 worlds: 89.1%.

`radeon-scale-report.json` contains the raw measurements and ROCm telemetry.
`radeon-scale-validation.json` records the strict validator result.

## Parallel Futures

- Candidate actions: 18.
- Repeats per candidate: 3.
- Simultaneous Genesis worlds: 54.
- Batched execution: 12.839 seconds.
- Hard-safe futures: 32.
- Rejected futures: 22.

`parallel-futures-report.json` contains the per-future measurements and ROCm
telemetry. `parallel-futures-validation.json` records the strict validator
result.

The environment-step count is a throughput workload, not a count of
independent safety trials. The 54 futures are 18 candidates times three
repeats, not 54 independent scenarios.
