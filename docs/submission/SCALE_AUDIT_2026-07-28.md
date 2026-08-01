# GuardianSim Scale Audit — 2026-07-28

Purpose: distinguish comparable evaluation volume from visually large but
different training or throughput numbers. This is a public-source audit, not a
claim about competitors' unpublished work.

## Current Track 3 comparison

### G1D-Organize-Table — official PR #28

Public source:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/28>

- Reports 30,000 model-training steps and a final step-29,999 checkpoint.
- The repository labels its data directory “no large datasets”.
- It documents real-robot demonstrations and an impressive VLA deployment,
  but its submitted README does not publish an evaluation episode count or a
  task-success rate. Adding automatic reset and task-success metrics remains
  listed as future work.

Conclusion: 30,000 optimizer steps are not 30,000 independent robot trials.

### NaviSense AI — official PR #11

Public source:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/11>

- Emphasizes a complete speech/LLM/simulation product.
- Publishes approximately 90 tokens/s and 1.0–1.5 s order-evaluation latency.
- The public submission does not foreground hundreds or thousands of
  independent robot-evaluation episodes.

### 1bit.systems Physical AI — official PR #13

Public source:
<https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/13>

- Emphasizes hardware work and throughput: 97 tok/s NPU, 318 tok/s Vulkan, and
  64 tok/s ROCm.
- Its large numbers are inference throughput and reverse-engineering scope,
  not robot-scenario sample size.

## External evaluation scale

- LIBERO provides 130 tasks and fixed initial states for evaluation:
  <https://github.com/Lifelong-Robot-Learning/LIBERO>.
- The common full LIBERO evaluation convention is 10 tasks × 50 episodes,
  or 500 rollouts.
- RoboTwin 2.0 documents 50 tasks and 100 evaluation episodes per task:
  <https://huggingface.co/docs/lerobot/main/robotwin>.
- RoboCasa365 provides 365 tasks and thousands of scenes and objects:
  <https://github.com/robocasa/robocasa>.

These are mature public benchmarks with a broader objective than this
hackathon entry. GuardianSim should not imply comparable task breadth.

## Decision

Use two honest scale layers:

1. **Preserved evidence ledger now:** 42 independent scene units, 1,185
   counterfactual rollouts, 202 final executions, and 1,387 simulated action
   traces.
2. **Gate 4 next:** 240 new paired scenes, 1,440 planned final executions, and
   up to 14,400 nested action traces under a predeclared protocol.

The judge-facing copy must always state that 1,387 or 14,400 traces are nested
inside 42 or 240 independent scenes.
