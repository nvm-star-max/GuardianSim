# Radeon Scale V2 Frozen Protocol

Date frozen: 2026-07-31
Status: implementation protocol; no V2 performance result exists yet

## Question

How much full-scene Genesis physics can one Radeon GPU sustain when GuardianSim
uses it as a robot safety co-processor?

This benchmark isolates the AMD capability that makes GuardianSim practical:
running many physical futures before the real robot commits to one action.

## Scene

Every parallel world contains:

- one Franka manipulator;
- one table;
- four active YCB entities;
- the same fixed position-hold command;
- headless Genesis physics with all cameras disabled.

Scene construction, shader setup, and JIT warmup are excluded from the primary
throughput timing. Build and warmup durations remain in the raw report.

## Frozen formal workload

| Field | Frozen value |
|---|---:|
| Batch sizes | 1, 16, 64, 256, 512, 1,024, 2,048, 4,096 worlds |
| Warmup | 200 simulator steps per batch |
| Measurement | 12,288 simulator steps per batch |
| Largest-batch workload | 50,331,648 environment steps |
| Full sweep workload | 98,512,896 environment steps |
| Primary metric | environment steps per wall-clock second |

The measured batch order is fixed and strictly increasing. A batch is valid
only if its immutable raw JSON passes strict validation against the same
protocol hash.

## AMD receipts

Each batch must preserve:

- AMD device name, PyTorch version, HIP version, and Genesis version;
- measurement duration and independently recomputed throughput;
- mean and peak GPU utilization;
- peak and total VRAM bytes;
- build and warmup durations;
- source hashes, Git receipt, launch command, logs, and SHA-256 checksums.

No minimum throughput or GPU-utilization threshold is declared. The report
records the measured saturation point even if throughput stops scaling before
4,096 worlds.

## Capacity preflight

Before formal launch, a separate non-performance preflight may build short
512, 1,024, 2,048, and 4,096-world processes to detect out-of-memory or scene
construction failures. Preflight samples are not combined with the formal
report and cannot be quoted as performance evidence.

If the declared 4,096-world scene does not fit, this V2 formal protocol fails.
A lower-capacity run would require a new dated protocol and a new hash. The
batch list, timing, and workload may not be edited after partial formal
results.

## Resume and overwrite rules

- A new formal run starts in a new output directory.
- Existing evidence is never overwritten.
- A restart may skip only a complete raw trial that revalidates against the
  exact current source hashes and frozen protocol.
- Failed and interrupted attempt logs remain preserved under numbered names.
- The final report is written only after all eight batches validate.
- Public metrics must come from the final strict report, not terminal output.

## Claim boundary

The 98,512,896 count is measured Genesis physics environment steps. It is not:

- a dataset row count;
- PPO training experience;
- an independent safety-trial count;
- physical-robot evidence;
- proof of real-time robot control.

GuardianSim's separate 4,608-pair Safety Swarm V2 result explains what the
parallel compute is used for: evaluating candidate actions across uncertainty
worlds and selecting one eligible action or stopping.

## Judge-facing message after verification

The intended one-line explanation is:

> A policy proposes the motion. One Radeon GPU simulates thousands of physical
> futures before GuardianSim allows the robot to move.

The final PR, website, report, and video may add V2 numbers only after the raw
report and telemetry pass strict validation.
