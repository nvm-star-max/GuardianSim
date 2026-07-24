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

**Gate 2 — Counterfactual planning: not started.**

The decision core and `GenesisCandidateEvaluator` boundary exist, but
`GenesisRolloutBackend` is still a protocol. No real candidate ranking result
may be presented until a concrete Genesis backend restores an identical episode
state and measures every candidate rollout.

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
- Latest verified milestone commit: `64991a7`
- Relevant commits:
  - `2119d0d` — Genesis evaluation and benchmark pipeline
  - `2283818` — compatible NumPy/scikit-image bounds
  - `64991a7` — Radeon Cloud Session A evidence

## Architecture already implemented

- Deterministic grasp-candidate generation.
- Simulator-independent candidate metrics and risk scoring.
- Failure diagnosis and bounded recovery planning.
- Baseline-vs-GuardianSim benchmark schema and CSV/JSON export.
- Lazy Genesis adapter boundary so local macOS tests do not import Genesis.

## Next-stage proposal

Before spending another cloud credit:

1. Define a serializable episode snapshot with object poses, robot qpos, task,
   seed, and perturbation condition.
2. Implement a concrete reference-scene rollout backend behind the existing
   `GenesisRolloutBackend` protocol.
3. Measure reachability, path length, minimum clearance, alignment, retained
   lift height, and execution outcome from the simulator.
4. Add deterministic fake-scene and snapshot/restore tests on macOS.
5. Prepare one exact cloud command for a five-candidate dry run.

Only after those checks pass should Session B launch. Session B should first run
five candidates from one identical state, then expand to a 20-episode fixed-seed
baseline comparison if the dry run is valid.

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

## Pending operational action

The Session A instance had completed its end-of-session script and was idle at
the last check. Its final destruction was intentionally not performed without
an explicit confirmation because it removes the cloud environment.

