# Radeon P0 Evidence — 2026-07-29

This directory preserves the raw Radeon Cloud evidence for GuardianSim's
judge-facing parallel-compute demonstration. It does not modify or extend the
frozen Gate 3.2 or Gate 3.3 safety reports.

## Accepted results

### Parallel physics scale

- Fixed batches: `1 / 16 / 64 / 256` headless Franka worlds.
- Fixed timing: `100` warmup steps and `1,000` measured steps per batch.
- Largest point: `35,166.1 environment-steps/s`.
- Speedup versus one world: `228.16×`.
- 256-world parallel efficiency: `89.1%`.
- 256-world mean/peak GPU utilization: `85.5% / 96%`.
- Total measured workload: `337,000` environment steps.
- Strict validator: passed with ROCm telemetry required.

### Parallel Futures

- `18` candidate actions × `3` repeats = `54` simultaneous Genesis worlds.
- Batched execution: `12.839 s`, or `4.206 candidate futures/s`.
- `32` futures passed the unchanged hard gates; `22` were rejected.
- Mean/peak GPU utilization: `71.8% / 95%`.
- Strict validator: passed.

These values are physics-throughput and engineering-demo evidence. Neither
environment steps nor nested candidate futures are independent safety scenes.

## Preserved negative result

The Safety Critic report is structurally valid but is not showcase-ready:

- held-out hard-safe F1: `0.789`, below the frozen `0.80` gate;
- unsafe precision: `0.791`, below the frozen `0.90` gate.

The thresholds were not changed after observing the result. Learned-model
throughput is therefore excluded from the judge-facing presentation.

## Identity

- Scale protocol SHA-256:
  `4944cd288c1a855414c987e4229e1488498e56cd61e4d45136c62f3fb98d7603`
- Scale report SHA-256:
  `a372727b5280ca6be9e58ca6ab82b01899ed24eaa45c8df39359aab83dfe539e`
- Parallel Futures protocol SHA-256:
  `0a741806852b4333d41a1296c016d67dce988f5393f7800eaf1020a185a4c076`
- Parallel Futures report SHA-256:
  `126c0a2e10ffd387652c866c7c9407a4e84bbd4d5b6af1b47169bd429a37b4c4`
- Safety Critic report SHA-256:
  `61ddb0d7935665a445b81fcdfdcd67037011f0e995b405be34a7718dd4467aac`
- Outer archive SHA-256:
  `35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d`

The archive contains the original reports, preflight records, logs, ROCm
telemetry, validator output, environment manifest, failed pre-install
diagnostics, rendered scale card, checkpoint, and recursive checksums.
