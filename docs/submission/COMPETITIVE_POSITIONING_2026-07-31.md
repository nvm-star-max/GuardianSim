# Track 3 Positioning Notes

Date reviewed: 2026-07-31
Purpose: internal product and judging strategy; do not quote competitors
negatively in the submission

## What Chaal does well

Chaal provides a strong Radeon story around PPO locomotion:

- one concrete training workload with a large, correctly defined number:
  49,152,000 environment experience steps;
- separate physics-only and end-to-end PPO throughput;
- scaling and saturation measurements rather than one cherry-picked point;
- robustness tests over payload, friction, and pushes;
- raw JSON, checkpoints, a playable result, and upstream engineering notes.

The useful lesson is not “add PPO.” It is to make the AMD workload immediately
legible, expose the bottleneck, and let a judge trace every headline number to
an artifact.

## GuardianSim's distinct position

PPO, VLA, or a hand-authored policy may propose an action. GuardianSim is the
policy-agnostic verification layer:

> A policy proposes the motion. Radeon simulates the physical futures.
> GuardianSim executes one eligible action—or stops.

This avoids competing with a locomotion trainer on its strongest axis. It
also creates a clearer AMD product story: Radeon is used as a parallel robot
safety co-processor immediately before action execution.

## Evidence stack

The presentation should use three separate denominators:

1. **Safety outcome:** frozen 30-scenario benchmark, 30/30 repeatable safe
   completion and 30 → 0 sampled contacts.
2. **Decision workload:** 18 actions × 256 uncertainty worlds = 4,608 measured
   candidate-world pairs, narrowed to five eligible actions and one selected
   action.
3. **Compute scale:** Radeon Scale V2 targets 4,096 concurrent full
   manipulation worlds, 50,331,648 environment steps in the largest batch,
   and 98,512,896 across the sweep.

The third item remains a target until a strict Radeon report exists.

## Judge experience

After V2 verification, the first screen should answer four questions without a
judge running training:

- What is the robot deciding?
- Why are thousands of parallel worlds needed?
- What did the Radeon GPU actually execute?
- Can I inspect the raw receipt?

The final site should include a compact “AMD compute receipt” with concurrency,
environment-step throughput, GPU use, VRAM, HIP version, protocol hash, and a
link to raw evidence. The video should show the one-action funnel first and the
scale curve second.
