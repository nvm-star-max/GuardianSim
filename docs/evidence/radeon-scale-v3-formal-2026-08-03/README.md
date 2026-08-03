# Radeon Scale V3 formal evidence

This directory preserves the raw evidence for the frozen Radeon Scale V3 run
completed on AMD Radeon Cloud on 2026-08-03.

## Frozen scope and provenance

- Source commit: `64ca781471d9ba0729f19b48058030df26509f4f`
- Schema: `3`
- Batches: `4,096`, `8,192`, and `16,384` complete Genesis robot worlds
- Repeats: five independent processes and independently rebuilt scenes per batch
- Warmup: `200` steps per process
- Measurement: `2,048` steps per process
- Formal measurements: `15`
- Measured environment steps: `293,601,280`
- Protocol SHA-256:
  `118b2757a1ce71c1d7fc2f5143f21072b86adf25f7e1fb1a9e50d6a9f71ff203`
- Report SHA-256:
  `c09573787e474f8573b9a3ebab7bd9d1f6a81502c6d880c43b07aec5817bc692`

The primary metric is P50 environment steps per wall-clock second. Scene
construction, shader setup, and JIT warmup are outside the timed interval.
Capacity-preflight runs are not included in this evidence or the formal
aggregate.

## Strictly validated result

| Parallel worlds | Measured steps | P50 env-steps/s | Min–max env-steps/s | Mean GPU | Peak VRAM |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 4,096 | 41,943,040 | 152,697.384 | 151,505.802–153,127.087 | 97.768% | 6,706,696,192 B |
| 8,192 | 83,886,080 | 214,944.307 | 213,958.838–215,431.231 | 97.978% | 12,373,348,352 B |
| 16,384 | 167,772,160 | 278,051.244 | 274,989.939–278,671.733 | 98.817% | 23,677,100,032 B |

At the largest batch, P95 throughput was `278,660.488 env-steps/s`. P50
throughput rose `1.821x` from 4,096 to 16,384 worlds. Across all 15 formal
measurements, weighted mean GPU utilization was `98.330%` and observed peak
utilization was `100%`. Peak VRAM use was `23.677 GB` (`22.05 GiB`) of the
observed `51.523 GB` device capacity.

## AMD Radeon execution

- Device: AMD Radeon Graphics
- PyTorch: `2.9.1+gitff65f5b`
- HIP: `7.2.53211-e1a6bc5663`
- Genesis: `1.2.3`
- Telemetry sampling errors: none

## Integrity and claim boundary

- Downloaded archive: `radeon-scale-v3-formal-evidence-20260803.tar.gz`
- Archive SHA-256:
  `b5adc496eadf9257cbcedf52104b2864ced3c459a2ca4fd2eb74909a549e3b0a`
- Every payload listed in the sealed `SHA256SUMS` passed local verification.
- `validation.json` and `radeon-scale-v3-strict-validation.json` both record a
  passing strict schema-3 validation.

These are Genesis physics environment steps from full simulated robot worlds.
They are not training samples, inference tokens, independent safety trials, or
physical-robot evidence. The Safety Swarm decision and Gate 3.2 robustness
results remain separate evidence sets with different units.
