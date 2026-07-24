# GuardianSim Project Memory

Last updated: 2026-07-24

This file is the durable source of truth for continuing GuardianSim work across
machines and agent sessions. Update it after every verified milestone, cloud
session, architectural decision, or change to the competition plan.

## Mission

Build a competition-ready Physical AI demo that improves Franka pick-and-place
reliability by evaluating counterfactual grasp actions in Genesis, explaining
their risk, monitoring execution, and attempting bounded recovery.

The judge-facing claim must be supported by fixed-seed Genesis experiments on an
AMD Radeon GPU. Synthetic benchmark numbers are development smoke tests only.

## Current stage

**Gate 1 — Baseline: complete.**

Verified on Radeon Cloud:

- ROCm/HIP PyTorch sees one AMD Radeon GPU.
- Genesis builds and steps the retained Franka/YCB scene on the GPU.
- The scripted `011_banana -> 024_bowl` task succeeds.
- Eight reference-policy frames and two scene-probe frames were preserved.
- GuardianSim unit tests pass: 7/7.

Evidence: [`evidence/session-a/README.md`](evidence/session-a/README.md)

**Gate 2 — Counterfactual planning: local implementation complete; cloud
validation pending.**

The repository now includes:

- a serializable episode snapshot and stable SHA-256 state fingerprint;
- a concrete `GenesisSceneDriver` that captures and restores Franka qpos and all
  YCB poses with dynamic velocity cleared;
- physical trace measurement for path length, retained lift, alignment, and
  sampled collision-AABB clearance;
- a real five-candidate Franka grasp-and-lift executor;
- an exact Session B dry-run command that emits ranked JSON.

No real candidate ranking result may be presented until the Session B command
has run successfully on Radeon Cloud.

## Verified environment

- Cloud template: Radeon Cloud Blank OpenCode Workspace
- Python: 3.12.3
- PyTorch: 2.9.1 (`gitff65f5b`)
- HIP: 7.2.53211
- `uv`: `/opt/venv/bin/uv`
- Compatible image stack:
  - `numpy>=1.26.4,<2.3`
  - `scikit-image>=0.25.2`

The NumPy upper bound is required by Numba. The newer scikit-image is required
to avoid a NumPy 2 ABI mismatch.

## Repository state

- Repository: <https://github.com/nvm-star-max/GuardianSim>
- Branch: `main`
- Latest verified documentation commit: `1c17e90`
- Relevant commits:
  - `2119d0d` — Genesis evaluation and benchmark pipeline
  - `2283818` — compatible NumPy/scikit-image bounds
  - `64991a7` — Radeon Cloud Session A evidence
  - `1c17e90` — durable project memory and worklog

## Architecture already implemented

- Deterministic grasp-candidate generation.
- Simulator-independent candidate metrics and risk scoring.
- Failure diagnosis and bounded recovery planning.
- Baseline-vs-GuardianSim benchmark schema and CSV/JSON export.
- Lazy Genesis adapter boundary so local macOS tests do not import Genesis.

## Next-stage proposal

Review and commit the local Gate 2 implementation. Then launch Session B only to
run the five-candidate dry run documented in [`RADEON_CLOUD.md`](RADEON_CLOUD.md).
Inspect the ranked JSON and trace log before deciding whether to:

1. refine the measurement implementation locally; or
2. continue the same session into a 20-episode fixed-seed comparison.

## Working agreement

- Maintain [`WORKLOG.md`](WORKLOG.md) as an append-only experiment log.
- Update this memory after verified changes or decisions.
- Work locally whenever GPU execution is not required.
- Before a major stage, stop and present:
  - what has been proven;
  - the proposed route;
  - major alternatives and tradeoffs;
  - the exit criteria and expected credit cost.
- Do not begin the next major stage until the route has been reviewed with the
  owner.
- Destroy cloud instances after evidence is copied and code is pushed. Closing
  the browser is not sufficient.

## Cloud access and instance state

- A dedicated local ED25519 key was created at
  `~/.ssh/guardiansim_radeon_ed25519`.
- Only its public key was saved to Radeon Cloud.
- Key fingerprint:
  `SHA256:8VLTCjgZI8Ufo+CTDck01Zv8WUJMgPw9zTFa/FPF83Q`.
- The key applies only to future SSH-enabled templates that expose a host and
  port. Blank OpenCode did not display an SSH endpoint.
- The Session A instance was destroyed after its evidence was secured.
- Final profile check: `No active instance`, `Key on file`, and 10 credits
  available.
