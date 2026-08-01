# Radeon Parallel Physics Scale Protocol

Status: **Radeon Cloud run complete; strict validation passed**

This benchmark is a judge-facing compute demonstration, not a replacement for
GuardianSim's paired safety evaluation. It measures how many independent
Franka manipulation worlds Genesis can advance per second on one AMD Radeon
GPU.

## Claim boundary

- `42` preserved scene units, `1,185` counterfactual rollouts, and `202` final
  executions remain the current GuardianSim effectiveness evidence.
- This benchmark reports **physics throughput** at batch sizes
  `1 / 16 / 64 / 256`.
- Batched environment steps are not relabeled as independent safety trials.
- No throughput, speedup, utilization, or VRAM number may enter the showcase
  until the strict report validator accepts the Radeon Cloud output.

## Verified Radeon Cloud result — 2026-07-29

The frozen four-point matrix completed on one AMD Radeon GPU with PyTorch
`2.9.1+gitff65f5b`, HIP `7.2.53211-e1a6bc5663`, and Genesis `1.2.3`.

| Parallel worlds | Environment steps/s | Speedup vs 1 | Parallel efficiency | Mean GPU use | Peak VRAM |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 154.1 | 1.00× | 100.0% | 84.3% | 1.00 GiB |
| 16 | 2,383.7 | 15.47× | 96.7% | 87.8% | 1.06 GiB |
| 64 | 9,354.3 | 60.69× | 94.8% | 89.0% | 1.09 GiB |
| 256 | 35,166.1 | 228.16× | 89.1% | 85.5% | 1.34 GiB |

- All four trials reached `96%` peak GPU utilization.
- Total measured workload: `337,000` environment steps.
- Protocol SHA-256:
  `4944cd288c1a855414c987e4229e1488498e56cd61e4d45136c62f3fb98d7603`.
- Report SHA-256:
  `a372727b5280ca6be9e58ca6ab82b01899ed24eaa45c8df39359aab83dfe539e`.
- Evidence archive SHA-256:
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`.
- Preserved evidence:
  [`docs/evidence/radeon-p0-2026-07-29/radeon-scale`](evidence/radeon-p0-2026-07-29/radeon-scale).

Genesis documents that `scene.build(n_envs=...)` adds an environment batch
dimension and runs parallel worlds on the GPU. Genesis also documents the AMD
ROCm/HIP backend and recommends keeping operations batched to avoid CPU
synchronization bottlenecks:

- <https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/parallel_simulation.html>
- <https://github.com/Genesis-Embodied-AI/Genesis>
- <https://genesis-world.readthedocs.io/en/latest/user_guide/policy_training/best_practices/efficient_environment.html>

## Frozen measurement method

Each batch size runs in a fresh Python process so build state and device memory
cannot leak between trials.

1. Initialize Genesis on the GPU and build the same headless Franka + table +
   four-active-YCB-entity scene.
2. Exclude scene build and compilation from steady-state timing.
3. Run `100` warmup simulation steps.
4. Synchronize the HIP device.
5. Time `1,000` control-plus-physics steps.
6. Poll `rocm-smi` during the timed interval.
7. Derive:
   - environment steps/s;
   - simulated seconds per wall second;
   - speedup versus the one-environment baseline;
   - parallel efficiency;
   - mean/peak GPU utilization;
   - peak used and total VRAM.

The four trials represent `337,000` measured environment steps in total:

```text
(1 + 16 + 64 + 256) environments × 1,000 measured steps
```

## Strict evidence requirements

The report is rejected when any of the following occurs:

- batch sizes differ from the protocol or are reordered;
- the protocol hash changes;
- a trial is missing or failed;
- the backend is not `genesis_gpu`;
- the device name does not identify AMD or HIP is missing;
- source timing and derived metrics disagree;
- ROCm telemetry has no samples.

Scene source and configuration SHA-256 values are embedded in the protocol.
Raw per-trial JSON and logs remain separate from the aggregate report.

## Radeon Cloud command

Run from `/workspace/persistent/GuardianSim` in the Radeon Cloud instance:

```bash
/opt/venv/bin/python scripts/run_radeon_scale_suite.py \
  --batch-sizes 1 16 64 256 \
  --warmup-steps 100 \
  --measurement-steps 1000 \
  --output-dir outputs/radeon-scale
```

Then validate independently:

```bash
/opt/venv/bin/python scripts/validate_radeon_scale_report.py \
  outputs/radeon-scale/report.json
```

The instance must not be destroyed. If batch `256` exceeds memory, preserve the
failure log as a measured capacity boundary; do not silently replace or remove
the failed point.

## Intended presentation

The finished experience will show a wall of `256` simultaneous robot worlds,
then zoom into one GuardianSim episode:

1. Radeon scales the physics workload.
2. Parallel Futures evaluates alternative actions.
3. GuardianSim executes a safe candidate or refuses motion.

The visual must label the scale panel **physics throughput** and the existing
formal panel **safety effectiveness** so judges cannot confuse the two.
