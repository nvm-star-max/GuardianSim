# GuardianSim 4-Minute Demo Script

Target duration: **4:00–4:30**
Language: **English narration and English on-screen text**
Claim rule: use Gate 3.2 for performance metrics; label the three-candidate
smoke as reproducibility proof only.

## Visual rule that fixes the previous comparison problem

Do not rely on two similar robot views. Every comparison shot must contain all
four signals:

1. colored action-geometry overlays that do not imply an unrecorded path;
2. a freeze-frame circle/arrow at the baseline contact or clearance event;
3. large labels for `CONTACT`, `SAFE`, or `SAFE STOP`;
4. numeric minimum clearance in millimeters.

The baseline is always left/orange. GuardianSim is always right/green. Show a
top-down inset when the wrist geometry is visually ambiguous.

## Timeline

### 0:00–0:20 — Hook: success is not the same as safety

**Visual**

- Begin with a clearly annotated Gate 3.2 formal comparison.
- Freeze the baseline at first clutter contact.
- Zoom to the contact location and display a red pulse.
- Keep GuardianSim moving on the right with a green path.

**On-screen**

```text
AEGIS MOTION PRESENTS
Same task. Same initial state.
Baseline: CLUTTER CONTACT
GuardianSim: SAFE COMPLETION
```

**Narration**

> A robot can complete a grasp and still take an unsafe path through clutter.
> GuardianSim evaluates counterfactual actions before execution and chooses a
> safer eligible action—or stops.

### 0:20–0:45 — Project and AMD GPU proof

**Visual**

- Repository title and one-sentence product statement.
- Live terminal capture of `rocm-smi`.
- Show the compact JSON fields from the evaluator manifest:
  `git_commit`, `gpu_ready`, `torch`, `hip`, and `gpu_count`.

**On-screen**

```text
AMD Radeon Cloud · gfx1100 · ROCm/HIP 7.2
PyTorch 2.9.1 · Genesis 1.2.3
```

**Narration**

> GuardianSim is a Physical AI safety layer for Franka fruit picking in
> Genesis. The physical counterfactual rollouts run on one AMD Radeon GPU
> through the Genesis amdgpu backend.

### 0:45–1:20 — How it works

**Visual**

- Animate the report architecture diagram from left to right:
  nominal action → candidate generator → same snapshot → Radeon rollouts →
  hard safety gates → execute or stop.
- Display three candidate paths around one clutter object.

**Narration**

> The nominal policy proposes a grasp. GuardianSim generates bounded yaw and
> obstacle-retreat alternatives. Every candidate is restored to the same
> fingerprinted scene snapshot, then measured for reachability, stability,
> path length, uncertainty, and clutter clearance. Utility ranking happens
> only after every hard safety gate passes.

### 1:20–2:05 — Live reproducibility smoke

**Visual**

- Type or paste one command:
  `./scripts/run_evaluator_smoke.sh`.
- Speed up installation/compilation pauses; do not cut validation output.
- Show:
  - `gpu_ready: true`;
  - 55 tests passing after the environment-path patch;
  - world and wrist probe frames;
  - `candidate_count: 3`;
  - one snapshot fingerprint;
  - `validated: true`.

**On-screen**

```text
Bounded evaluator smoke — not a performance benchmark
3 alternatives · 1 identical snapshot · strict schema validation
```

**Narration**

> An evaluator can run this bounded smoke from a fresh checkout. It verifies
> the source, the Radeon environment, the real Genesis scene, three
> counterfactual alternatives from one snapshot, and the preserved formal
> report. This smoke proves the execution path; it is not used for the
> performance claim.

### 2:05–2:55 — Make the physical difference unmistakable

**Visual**

- Use a Gate 3.2 formal scenario whose recorded replay satisfies the
  claim-boundary validator.
- Show the validated top-down action-geometry illustration first.
- Then show synchronized side-by-side execution.
- Pause at:
  1. baseline contact;
  2. GuardianSim's nearest approach;
  3. retained lift.
- Display candidate/decision reason.

**On-screen example**

```text
BASELINE
yaw 0° · fixed approach
CONTACT · clearance 0.0 mm

GUARDIANSIM
unsafe nominal replaced
yaw +67.5° · raised approach
SAFE · clearance XX.X mm
```

The accepted Seed 411 replay value is `17.1 mm`; it is bound to the source
video and formal report by `scripts/validate_gate32_demo.py`.

**Narration**

> Here the baseline uses its fixed nominal grasp and contacts the neighboring
> object. GuardianSim identifies the nominal action as unsafe, selects an
> eligible higher-clearance orientation, and completes the lift without
> clutter contact. The decision and physical measurements are preserved in the
> machine-readable report.

### 2:55–3:35 — Formal results

**Visual**

- Use one clean result table; animate one row at a time.
- Keep `Genesis simulation` visible.

**On-screen**

| Gate 3.2 | Baseline | GuardianSim |
| --- | ---: | ---: |
| Repeatable safe completion | 18/30 | 30/30 |
| Independent safe executions | 58/90 | 90/90 |
| Clutter contacts | 30 | 0 |
| Mean clearance | 23.191 mm | 46.003 mm |

**Narration**

> In the frozen 30-scenario Gate 3.2 benchmark, repeatable safe completion
> improved from 18 of 30 to 30 of 30. Across three independent executions per
> scenario, safe executions improved from 58 of 90 to 90 of 90. Clutter
> contacts decreased from 30 to zero, and mean sampled clearance increased by
> 98.36 percent.

### 3:35–4:05 — Honest limitation and safe stop

**Visual**

- Show a Gate 3.3 gap/bearing case as a diagram, not a rejected replay.
- Mark all candidate certificates below threshold.
- Show `SAFE STOP: no eligible action`.

**Narration**

> GuardianSim does not guarantee completion for arbitrary geometry. In two
> harder gap-and-bearing cases, no candidate passed every frozen safety gate,
> so the system stopped. This is the intended fail-safe behavior and also
> reveals where the action space must improve.

### 4:05–4:20 — Close

**Visual**

- Repository URL, reproducibility command, QR code, and concise claim boundary.

**On-screen**

```text
Aegis Motion · GuardianSim
Counterfactual action safety on AMD Radeon GPUs
Open source · reproducible evidence · Genesis simulation
```

**Narration**

> GuardianSim turns a nominal manipulation action into an explainable,
> uncertainty-aware execute-or-stop decision on AMD Radeon GPUs. The source,
> frozen reports, validators, and reproduction path are available in the
> repository.

## Required capture assets

- [ ] Live `rocm-smi` and compact environment JSON.
- [ ] Terminal run of the final submission commit's evaluator smoke.
- [ ] World and wrist probe frames.
- [ ] Architecture animation.
- [x] One accepted Gate 3.2 formal comparison replay.
- [x] Top-down action-geometry illustration.
- [x] Contact freeze-frame annotation.
- [x] Exact decision, yaw, overlap, and clearance.
- [x] Formal result table.
- [ ] Gate 3.3 safe-stop diagram.
- [ ] Repository URL and QR code.

## Hard exclusions

- Do not use either rejected Seed 503 Gate 3.3 replay as performance evidence.
- Do not describe the synthetic CLI smoke as a physical result.
- Do not imply that a single three-candidate smoke produced the 30-scenario
  metrics.
- Do not claim physical-robot validation.
- Do not hide Gate 3.1 negative evidence or Gate 3.3 safe stops.
- Do not display personal email, cloud account details, tokens, or instance
  credentials.

## Accepted hero clip

The final video should embed:

`docs/demo/gate-3-2-seed-411-aegis-showcase-v3.mp4`

Verified presentation properties:

- 1920×1080, 20 FPS, 17.55 seconds;
- source replay SHA-256
  `a6b8fa20b924268955c7c40e002faf3b048f5de534f3c19a2ba071f0c7a4e3be`;
- showcase SHA-256
  `38e9adfb2a3f2d90719b60449d092e4caca53afaa2b2f71fe1ade136357dff86`;
- formal report: complete schema-5, 30/30;
- formal Seed 411 executions: baseline 0/3 safe, GuardianSim 3/3 safe;
- replay: 1.42 mm baseline overlap versus 17.1 mm GuardianSim clearance;
- presentation-only post-processing: no physics re-execution and no added
  statistical trial.
