# Radeon Safety Swarm — P0 implementation gate

## The judge-facing idea

**One move. 256 uncertain worlds. Execute only if the swarm agrees.**

GuardianSim already compares candidate actions from the same physical state.
The next P0 layer should make AMD parallel compute visible and useful: take one
candidate action, replay it across a fixed 16×16 uncertainty grid on Radeon,
and turn the batch into a red/green robustness wall.

This is not another training job and does not ask a judge to configure a
model. The judge changes an uncertainty dial, presses one button, and sees:

- 256 physically simulated futures;
- pass/fail tiles grouped by failure cause;
- worst-case clearance and safe-world rate;
- the selected action or a visible `STOP`;
- Radeon device, ROCm version, batch size, wall time, and measured throughput;
- a downloadable evidence receipt with protocol hash and checksums.

The working name is **Radeon Safety Swarm**. The feature must be described as
an engineering robustness stress test until its protocol is frozen and
validated. It is not a physical-robot safety guarantee.

## What is learned, not copied

### Current Track 3 submissions

NaviSense AI makes its hardware story unusually easy to judge: one complete
voice-to-LLM-to-simulation workflow, measured Radeon latency, a live demo, a
CPU convenience fallback, and an upstream reusable component. GuardianSim
should borrow that delivery discipline:

- one sentence that explains the full loop;
- a no-sign-in path;
- a fallback replay that does not pretend to be the GPU run;
- a small reusable output format, not only a monolithic demo.

Source:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/11>

1bit.systems leads with hardware telemetry and low-level throughput. Its
strongest presentational lesson is that the AMD device must be visible in the
result, not buried in setup notes. GuardianSim should show live Radeon batch
telemetry beside the safety decision. It should not imitate unrelated NPU/LLM
claims.

Source:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/13>

### Closest open-source mechanisms

- **cuRobo**: many parallel optimization seeds, batched environments, and
  tensorized collision checking. GuardianSim should accept candidate
  trajectories from any planner and batch-test them; it should not claim to
  replace motion generation. <https://curobo.org/advanced_examples/1_batch_env.html>
- **ManiSkill**: GPU-parallel heterogeneous scenes and batched initialization.
  GuardianSim should make every uncertainty cell an explicit, inspectable
  scene variant. Its official GPU simulation path is NVIDIA-only, so the AMD
  execution path remains a meaningful distinction.
  <https://github.com/haosulab/ManiSkill>
- **Isaac Lab**: vector environments, seeded reproducibility, and domain
  randomization. GuardianSim should freeze the uncertainty matrix before the
  run and record seed plus matrix hash.
  <https://isaac-sim.github.io/IsaacLab/v2.0.0/source/api/lab/isaaclab.envs.html>
- **Safety-Gymnasium**: safety cost is a first-class output separate from
  reward. GuardianSim should emit a typed cost vector (`contact`, `clearance`,
  `stability`, `task_failure`) rather than only a single score.
  <https://github.com/PKU-Alignment/safety-gymnasium>
- **Genesis**: native batched scene simulation. This is the implementation
  foundation for the Radeon path, not a GuardianSim invention.
  <https://genesis-world.readthedocs.io/en/v1.0.0/user_guide/getting_started/parallel_simulation.html>

## Proposed fixed workload

The first implementation should use one selected candidate and 256 worlds.
Each world is one row in a predeclared Cartesian uncertainty matrix:

- target/object XY pose bias;
- target yaw bias;
- clutter gap;
- clutter bearing;
- end-effector pose bias;
- action start delay.

Only perturbations already supported and auditable in the current Genesis
scene may enter V1. Friction, mass, camera noise, and hidden random changes are
out until they have explicit per-environment implementations and tests.

Each world returns:

```text
world_id
perturbation tuple
contact cost
minimum sampled clearance
stability
task completion
stop reason
elapsed environment steps
```

The report aggregates:

- safe worlds / 256;
- worst-case clearance;
- 5th-percentile clearance;
- contacts by failure mode;
- Wilson lower confidence bound for the sampled safe-world rate;
- wall time and environment-steps/s;
- GPU/ROCm identity;
- protocol, matrix, source-commit, and report hashes.

## P0 visual

The public arena gains one panel below the current 18-future choice:

1. The existing frozen gates reduce 18 futures to an eligible candidate.
2. `STRESS TEST ON RADEON` launches or replays the 256-world batch.
3. A 16×16 wall fills from grey to green/red.
4. Hovering a red cell shows the exact perturbation and stop reason.
5. The decision card reads either:
   - `EXECUTE — 256/256 passed, worst margin …`; or
   - `STOP — failure envelope begins at …`.
6. The receipt can be downloaded as JSON.

Recorded evidence must remain available when cloud compute is offline. A
replay is labelled `PRESERVED RADEON RUN`; it never masquerades as a live run.

## Validation gates before any headline claim

Freeze these before a formal run:

- uncertainty dimensions and all 256 rows;
- scenario and candidate source state;
- hard safety thresholds and stop reasons;
- protocol and matrix hashes;
- report schema;
- acceptance thresholds;
- GPU telemetry collection method.

Then run:

1. deterministic local unit tests for matrix construction and aggregation;
2. a 4-world Radeon smoke test;
3. a 16-world visual test;
4. one untouched 256-world formal run;
5. strict schema/checksum validation;
6. independent replay from the preserved report.

Do not tune thresholds after seeing partial results. Do not add 256 to the
existing formal scenario count. It is a separate uncertainty stress-test
population.

## Decision at this gate

Proceed with **Radeon Safety Swarm** as the next P0 feature. Keep the failed
Safety Critic as negative evidence/P3 research; it should not become the
headline. The first coding slice is the frozen 256-row matrix, typed cost
vector, strict report schema, and offline 16×16 replay—before another long
cloud run.
