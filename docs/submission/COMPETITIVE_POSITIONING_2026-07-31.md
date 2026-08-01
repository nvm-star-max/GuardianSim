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
3. **Compute scale:** the strictly validated Radeon Scale V2 run reached
   4,096 concurrent full manipulation worlds, 50,331,648 environment steps in
   the largest batch, and 98,512,896 across the complete eight-batch sweep.
   The largest batch sustained 152,099 environment-steps/s at 98.7% mean and
   99% peak GPU utilization.

These are three deliberately separate claims. The scale workload is not
relabelled as PPO experience or independent safety trials.

## Judge experience

The first screen should answer four questions without a judge running
training:

- What is the robot deciding?
- Why are thousands of parallel worlds needed?
- What did the Radeon GPU actually execute?
- Can I inspect the raw receipt?

The site now leads with a compact AMD compute receipt: 4,096 worlds, 152,099
environment-steps/s, 98.7% mean / 99% peak GPU use, 6.25 GiB peak VRAM, and
98.51 million measured steps across the sweep. The final published version
must link those numbers to the raw schema-2 report and protocol hash. The video
should show the one-action funnel first and the eight-batch scale curve second.

## What to borrow without copying

Chaal's PPO loop and GuardianSim's pre-execution verification layer are
different products. The useful follow-up is presentation discipline:

- give the workload a one-line definition before the headline number;
- show the entire scale curve and its saturation, not only the peak;
- separate physics throughput from end-to-end policy or training throughput;
- keep raw JSON, telemetry, protocol identity, and a playable demo adjacent;
- show one failure case where the system stops instead of hiding it.

GuardianSim should not add PPO merely to resemble a competitor. Its more
defensible hook is that any PPO, VLA, or scripted policy can propose the
action, while Radeon performs the parallel physical check before execution.
