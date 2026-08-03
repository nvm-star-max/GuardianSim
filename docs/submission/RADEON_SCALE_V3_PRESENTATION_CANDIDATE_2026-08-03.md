# Radeon Scale V3 presentation candidate — 2026-08-03

Status: owner approved for V5 publication on 2026-08-03. Publication must use
a new immutable tag, preserve V4 unchanged, replace only the existing
organizer-package directory, and update PR #39 in place.

## Judge-facing thesis

**Think thousands. Execute one.**

AMD Radeon runs thousands of complete Genesis manipulation worlds in parallel.
GuardianSim uses that compute twice: first to demonstrate sustained full-scene
physics scale, then to screen counterfactual actions and reduce them to one
auditable robot decision or a safe stop.

The presentation keeps the two frozen workloads separate:

- Radeon Scale V3: Genesis physics environment steps and full parallel worlds;
- Safety Swarm V2 / Gate 3.2: candidate-world pairs, simulated executions, and
  robot-decision outcomes.

No value is presented as PPO samples, model-training throughput, tokens,
independent robot trials, or physical-robot evidence.

## Locked headline metrics

- 16,384 complete parallel Genesis manipulation worlds;
- 278,051 environment-steps/s P50 at the largest batch;
- 278,660 environment-steps/s P95;
- 274,990–278,672 environment-steps/s five-repeat range;
- 293,601,280 measured environment steps across 15 independent processes;
- 98.33% weighted mean GPU utilization and 100% observed peak utilization;
- 22.05 GiB peak VRAM use;
- separate decision funnel: 4,608 candidate-world pairs → 5 qualifying actions
  → 1 selected action;
- separate Gate 3.2 result: 18/30 → 30/30 repeatable safe scenarios, 58/90 →
  90/90 independent safe Genesis simulations, and 30 → 0 sampled clutter
  contacts.

## Local candidate artifacts

- website source under `showcase/`, with the Radeon scale metrics in the first
  desktop viewport and a separate-unit claim boundary;
- `output/pdf/GuardianSim-Technical-Report-Scale-V3-Candidate.pdf`;
- preserved first cut: `docs/submission/GuardianSim-Radeon-Scale-V3-review-v1.mp4`;
- current review cut: `docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.mp4`;
- current sidecar: `docs/submission/GuardianSim-Radeon-Scale-V3-review-v2.json`;
- narrated review candidate:
  `docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.mp4`;
- narrated sidecar, fixed captions, and strict validation receipt:
  `docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.json`,
  `docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3.ass`, and
  `docs/submission/GuardianSim-Radeon-Scale-V3-narrated-v3-validation.json`;
- `scripts/build_radeon_scale_v3_showcase_cut.py`;
- `scripts/validate_radeon_scale_v3_showcase_cut.py`.

The 90-second V2 video is intentionally silent until the visual sequence is
approved. Its final ten seconds use only the preserved motion window from the
formal Seed 411 Genesis replay: nominal contact on the left and GuardianSim's
safe-clearance action on the right. Its sidecar binds source hashes, output
hash, chapter windows, claim boundaries, and locked metrics. V1 remains intact
as a historical candidate.

The owner approved the V2 visual sequence. The V3 release version adds
seven English Qwen `Ethan` narration segments and fixed English captions without
changing the approved 90-second image sequence. The owner approved that V3
narrated version for final publication on 2026-08-03.

## Review completed locally

- website desktop viewport: 1440×1050, no horizontal overflow;
- website mobile viewport: 390×844, no horizontal overflow;
- full-page desktop and mobile screenshots inspected;
- eight-page A4 report rendered page-by-page and inspected;
- V2 video rendered at 1920×1080, 20 FPS, 90 seconds;
- video full decode, eight sampled decodes, source hashes, metric locks, and
  simulation claim boundaries passed strict validation;
- the 82-, 85-, and 89-second finale frames were inspected at original
  resolution; the complete ending contains robot motion rather than compressed
  explanatory cards, and no title, label, or metric crosses its frame bounds;
- V3 full audio/video decode, all narration and caption hashes, the V2 visual
  identity, frozen source hashes, locked metrics, and claim boundaries passed;
- decoded V3 frames at 10, 30, 45, 65, 75, and 85 seconds were inspected. The
  simulation-finale caption uses a dedicated top safe area and does not cover
  the left/right result labels;
- wording uses “Genesis simulations” rather than “physical executions” to
  avoid implying a hardware-robot experiment.

## Public-release decision

The owner approved the website, report, silent V2 sequence, and narrated V3
version. The V5 release therefore replaces the public presentation layer while
retaining every older immutable tag and evidence set. It publishes a new source
tag and Pages build, replaces only the existing organizer package directory,
and updates PR #39 without opening, closing, or merging another pull request.
