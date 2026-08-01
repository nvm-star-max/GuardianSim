# GuardianSim Parallel Candidate Futures

This engineering demo maps each GuardianSim candidate/repeat pair to one
Genesis environment and executes the full matrix in a single batched scene on
the Radeon GPU.

## Fixed matrix

- 18 obstacle-aware grasp candidates
- 3 physical repeats per candidate
- 54 simultaneous Genesis environments
- Batched inverse kinematics for approach, descent, and lift
- GPU-resident control tensors and vectorized AABB clearance measurements
- The unchanged Gate 3.2 hard-safety boundary:
  reachability = 1, clearance >= 10 mm, stability >= 0.70

The preflight protocol is written before execution. The report validator checks
the protocol hash, all 54 candidate/repeat assignments, derived safety labels,
AMD/HIP identity, throughput arithmetic, and ROCm telemetry.

## Claim boundary

This is engineering evidence for parallel candidate-future execution and
throughput. It does not turn 54 nested futures into 54 independent formal
scenes, does not modify Gate 3.2 or Gate 3.3, and does not replace the preserved
formal safety evidence.

## Radeon Cloud

```bash
python scripts/run_parallel_futures_demo.py \
  --output outputs/parallel-futures/report.json \
  --preflight-output outputs/parallel-futures/preflight.json \
  --validation-output outputs/parallel-futures/validation.json
```
