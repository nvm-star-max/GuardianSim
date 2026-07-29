# GuardianSim Open-Source Overlap Audit

Date: 2026-07-29

This review asks two separate questions:

1. Which open-source projects overlap with GuardianSim's function?
2. Does each project document an official AMD GPU or ROCm execution path?

The review uses project-owned repositories and documentation. “No documented
AMD path” means that the reviewed official material does not describe one; it
does not claim that an unofficial port is impossible.

## Short conclusion

No reviewed project combines the complete GuardianSim workflow:

- restore one physical state;
- evaluate bounded action futures in parallel physics;
- reject futures with frozen safety gates;
- require repeatable physical outcomes;
- choose an eligible action or stop;
- preserve a decision receipt;
- run the demonstrated GPU path on AMD Radeon through ROCm/HIP.

The closest projects overlap with individual layers. cuRobo and MoveIt 2 are
motion-planning systems. ManiSkill and Isaac Lab are high-throughput robotics
simulation and training platforms. Safety-Gymnasium is a safe-RL benchmark.
Genesis is GuardianSim's simulation foundation and the only reviewed project
with an explicit native AMD ROCm backend.

## Comparison

| Project | Functional overlap | Important difference from GuardianSim | Official compute path | AMD status in official material |
| --- | --- | --- | --- | --- |
| [Genesis](https://github.com/Genesis-Embodied-AI/Genesis) | Very high at the physics and parallel-world layer; it is GuardianSim's simulator dependency. | Genesis supplies the physics engine. GuardianSim adds the same-state counterfactual protocol, hard gates, repeatability rule, execute-or-stop decision, and auditable receipt. | GPU/CPU backends, including `gs.amdgpu`. | **Yes.** Genesis documents ROCm/HIP, `gs.init(backend=gs.amdgpu)`, and an AMD Dockerfile. Its [backend documentation](https://genesis-world.readthedocs.io/en/latest/user_guide/configuration/initialization.html) also lists `gs.amdgpu`. |
| [cuRobo](https://github.com/NVlabs/curobo) | Very high for GPU-parallel kinematics, collision checking, trajectory optimization, geometric planning, and collision-free motion generation. | cuRobo generates motion efficiently. GuardianSim evaluates bounded candidate actions through restored physical rollouts, requires repeatability, can refuse execution, and records evidence. | CUDA kernels on NVIDIA GPUs. | **No official AMD path.** The maintainer states that an [NVIDIA GPU is required](https://github.com/NVlabs/curobo/discussions/77) because motion generation uses CUDA kernels. |
| [ManiSkill](https://github.com/haosulab/ManiSkill) | High for GPU-parallel manipulation simulation, heterogeneous scenes, rendering, and synthetic-data collection. | ManiSkill is a simulator and learning benchmark, not a policy-agnostic pre-execution safety decision layer with frozen gates and evidence receipts. | SAPIEN/PhysX GPU simulation exposed as `physx_cuda`; the [quickstart](https://maniskill.readthedocs.io/en/latest/user_guide/getting_started/quickstart.html) uses CUDA and `nvidia-smi`. | **No AMD GPU simulation path in the support matrix.** The official repository lists Linux/NVIDIA for GPU simulation. Windows/AMD supports CPU simulation and rendering, but not GPU simulation. |
| [Isaac Lab](https://github.com/isaac-sim/IsaacLab) | High for vectorized robot simulation, training, domain randomization, and multi-GPU workloads. | Isaac Lab is a broad training and simulation platform. It does not provide GuardianSim's frozen, per-action execute-or-stop certification protocol and receipt format. | Isaac Sim/PhysX with NVIDIA drivers and CUDA-enabled PyTorch. | **No official AMD path for the documented full workflow.** The [installation requirements](https://isaac-sim.github.io/IsaacLab/develop/source/setup/installation/index.html) specify a recent NVIDIA driver and CUDA PyTorch builds. |
| [MoveIt 2](https://github.com/moveit/moveit2) | Medium-high for manipulation planning, planning scenes, collision checking, and trajectory processing. | MoveIt 2 primarily checks planned geometry through planners and collision libraries. GuardianSim tests candidate actions in repeated physics from a fingerprinted state and can stop when none pass. | ROS 2 planning stack, primarily CPU libraries such as FCL, Bullet, and OMPL. | **Vendor-neutral CPU stack; no official AMD GPU acceleration path documented.** MoveIt's [concept documentation](https://moveit.ai/documentation/concepts/) describes FCL-based collision checking rather than a ROCm backend. |
| [Safety-Gymnasium](https://github.com/PKU-Alignment/safety-gymnasium) | Medium conceptual overlap through constraints, safety costs, vectorized environments, and safe-RL evaluation. | Safety-Gymnasium is a training benchmark with cost-augmented environments. GuardianSim is a runtime action-screening layer for manipulation and does not require retraining the policy. | MuJoCo for its standard environments; optional Safe Isaac Gym tasks belong to the NVIDIA Isaac stack. | **No official AMD/ROCm acceleration path documented.** Standard MuJoCo tasks are portable CPU workloads; the project does not describe an AMD GPU backend. |

## What can be claimed safely

GuardianSim should not be presented as a replacement for cuRobo, MoveIt,
ManiSkill, Isaac Lab, Safety-Gymnasium, or Genesis. It occupies a narrower
layer between a nominal action source and execution:

> GuardianSim is a simulator-backed action safety filter. It restores one
> state, evaluates bounded physical futures in parallel, applies frozen hard
> gates and repeatability checks, then emits an action-or-stop decision with a
> preserved evidence receipt.

The strongest AMD-specific distinction is not “robotics has never run on
AMD.” It is:

> The demonstrated GuardianSim workflow uses Genesis's documented AMD
> ROCm/HIP backend to turn Radeon parallel physics into an auditable
> pre-execution decision.

## Boundaries

- This is a source review, not a performance benchmark between projects.
- Project stars, marketing throughput, and paper metrics are intentionally not
  compared because the workloads and validation units differ.
- GuardianSim's preserved results remain Genesis simulation results, not a
  physical-robot deployment claim.
- The review was current on 2026-07-29 and should be refreshed if any project
  adds a documented ROCm backend.
