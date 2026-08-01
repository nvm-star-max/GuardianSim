# GuardianSim Submission Working Set

This directory contains the English source material for the Track 3
submission. It is a working set, not yet the final uploaded package.

## Current artifacts

- [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md): final technical-report source,
  aligned to the official Track 3 section list and limited to preserved
  metrics.
- [`../../output/pdf/GuardianSim-Technical-Report.pdf`](../../output/pdf/GuardianSim-Technical-Report.pdf):
  local eight-page Scale V2 release candidate. It was rendered page by page
  and visually inspected, but has not replaced the released V3 package PDF.
  PDF SHA-256:
  `42338e06481c4caa08b6e53ab61ed7d522de0216931dfa402314cbcbdd6e850e`.
- [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf):
  currently released seven-page V3 submission edition with no draft markings.
  The Radeon section now separates the 1/16/64/256-world throughput curve, the
  30-scenario safety benchmark, and the formal 18 × 256 = 4,608-pair decision
  run. PDF SHA-256:
  `4028372be15ca2fba2a0cd7f1ddd7e51c8d9cd012521e4be80cc40a523500ef3`.
- [`GuardianSim-Aegis-Motion-demo-review-v2.mp4`](GuardianSim-Aegis-Motion-demo-review-v2.mp4):
  the approved 4:41 complete-workflow submission video with Qwen3-TTS Instruct
  narration, fixed chapter captions, and normalized loudness.
- [`GuardianSim-Aegis-Motion-demo-review-v2.json`](GuardianSim-Aegis-Motion-demo-review-v2.json):
  V2 narration model, voice, instructions, per-segment audio hashes, timing,
  evidence bindings, and verified metrics.
- [`GuardianSim-Aegis-Motion-demo-review-v2-validation.json`](GuardianSim-Aegis-Motion-demo-review-v2-validation.json):
  strict V2 narration, caption-policy, duration, decode, source-identity,
  metric, and claim-boundary validation.
- [`GuardianSim-Radeon-Parallel-Futures-review-v3.mp4`](GuardianSim-Radeon-Parallel-Futures-review-v3.mp4):
  final silent source for the supplementary Radeon preview. Each metric row is
  optically centered from measured pixel widths.
- [`GuardianSim-Radeon-Parallel-Futures-review-v3.json`](GuardianSim-Radeon-Parallel-Futures-review-v3.json):
  source hashes, locked metrics, chapter timing, layout policy, and claim
  boundaries.
- [`GuardianSim-Radeon-Parallel-Futures-review-v3-validation.json`](GuardianSim-Radeon-Parallel-Futures-review-v3-validation.json):
  strict visual decode, source-hash, metric, layout, and claim-boundary
  validation.
- [`GuardianSim-Radeon-Parallel-Futures-review-v4.mp4`](GuardianSim-Radeon-Parallel-Futures-review-v4.mp4):
  local Scale V2 silent preview candidate. It shows the eight-point
  1-to-4,096-world curve, the formal `4,608 → 5 → 1` Safety Swarm funnel,
  accepted Seed 411 replay, and frozen 30-scenario result. It is not public.
- [`GuardianSim-Radeon-Parallel-Futures-review-v4.json`](GuardianSim-Radeon-Parallel-Futures-review-v4.json):
  V4 source hashes, locked metrics, chapter timing, layout policy, and claim
  boundaries.
- [`GuardianSim-Radeon-Parallel-Futures-review-v4-validation.json`](GuardianSim-Radeon-Parallel-Futures-review-v4-validation.json):
  strict V4 full-video decode, source-hash, metric, layout, duration, and
  claim-boundary validation.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v5.mp4`](GuardianSim-Radeon-Parallel-Futures-narrated-v5.mp4):
  local Qwen `Ethan` narration candidate built byte-for-byte from the silent
  V4 visual source. It has not replaced the released narrated V4.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v5.json`](GuardianSim-Radeon-Parallel-Futures-narrated-v5.json):
  V5 narration text, timing, audio hashes, immutable visual identity, evidence
  bindings, and locked metrics.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v5.ass`](GuardianSim-Radeon-Parallel-Futures-narrated-v5.ass):
  fixed V5 chapter captions.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v5-validation.json`](GuardianSim-Radeon-Parallel-Futures-narrated-v5-validation.json):
  strict V5 full audio/video decode, narration and caption hashes, source
  identity, metric, duration, and claim-boundary validation.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v4.mp4`](GuardianSim-Radeon-Parallel-Futures-narrated-v4.mp4):
  approved 80-second supplementary preview using the final silent source and
  direct-language Qwen narration.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v4.json`](GuardianSim-Radeon-Parallel-Futures-narrated-v4.json):
  narration timing, audio hashes, immutable visual identity, evidence
  bindings, and locked metrics.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v4.ass`](GuardianSim-Radeon-Parallel-Futures-narrated-v4.ass):
  fixed chapter captions.
- [`GuardianSim-Radeon-Parallel-Futures-narrated-v4-validation.json`](GuardianSim-Radeon-Parallel-Futures-narrated-v4-validation.json):
  strict V4 full audio/video decode, narration and caption hashes, source
  identity, metric, duration, and claim-boundary validation.
- [`COMPETITOR_SCAN_2026-07-27.md`](COMPETITOR_SCAN_2026-07-27.md): a
  time-stamped inventory of the official repository and GuardianSim's
  evidence-backed competitive position.
- [`RULES_REVIEW_2026-07-28.md`](RULES_REVIEW_2026-07-28.md): a source-linked
  compliance review of the official 15-page Rules and Conditions document.
- [`OPEN_SOURCE_OVERLAP_AUDIT_2026-07-29.md`](OPEN_SOURCE_OVERLAP_AUDIT_2026-07-29.md):
  a primary-source comparison of the closest robotics projects, their overlap
  with GuardianSim, and whether their official GPU path supports AMD/ROCm.
- [`FINAL_SUBMISSION_2026-07-28.md`](FINAL_SUBMISSION_2026-07-28.md): the
  verified organizer PR, commit, file list, checksums, and authorization
  record without private identity data.
- [`OFFICIAL_PR_DRAFT.md`](OFFICIAL_PR_DRAFT.md): the English official-repo
  pull-request title and body draft.
- **Public judge-facing showcase:**
  <https://nvm-star-max.github.io/GuardianSim/> (no sign-in required). The
  published V3 static build promotes the exact 4,608-pair matrix and
  `4,608 → 5 → 1` funnel.
- [`official-package/Track3-Aegis-Motion-GuardianSim`](official-package/Track3-Aegis-Motion-GuardianSim):
  self-contained V4 release candidate prepared for the official contest fork.
  It now includes the eight-page Scale V2 report, owner-approved narrated V5
  supplementary preview, strict eight-batch scale report, compact Safety Swarm
  V2 formal summary, validator outputs, and recursive checksums. The candidate
  remains local until the V4 release gate is explicitly opened.

Earlier scale-video review iterations remain local development artifacts and
are intentionally excluded from the public release.

Rebuild the final PDF with ReportLab:

```bash
python scripts/build_technical_report_pdf.py --final \
  --output output/pdf/GuardianSim-Technical-Report.pdf
```

The build script is separate from the evaluator runtime. Install `reportlab`
only on a documentation workstation if it is not already available.

Rebuild and validate the narrated review video on macOS:

```bash
uv run --frozen --no-sync python scripts/build_submission_video.py
uv run --frozen --no-sync python scripts/validate_submission_video.py \
  --output docs/submission/GuardianSim-Aegis-Motion-demo-review-v2-validation.json
```

The default V2 build uses
`qwen3-tts-instruct-flash-2026-01-26` with the `Ethan` voice. Configure
`DASHSCOPE_API_KEY` in the environment or in the Git-ignored `.env.local`
file. Generated narration chunks are cached under `tmp/`, and no credential
is written to the sidecar. Set `GUARDIANSIM_TTS_PROVIDER=macos` only when the
offline Samantha review voice is explicitly desired.

The owner approved the complete V2 cut on 2026-07-28. It is the frozen video
artifact for submission; do not change its narration, captions, timing, or
evidence claims without a new explicit owner decision. A real-time
final-commit Radeon terminal capture is no longer required for this version;
the current terminal section is clearly labeled archived evidence.

The owner accepted the optically centered 80-second Radeon scale-first narrated V4 on
2026-07-29 as a supplementary preview. It does not replace the previously
approved 4:41 V2 workflow video because the official Track 3 guidance
recommends a 3-5 minute complete-workflow demonstration.

Those approved videos remain unchanged evidence-bound artifacts. A separate
silent review V4 now binds the later Scale V2 and 4,608-pair formal reports
without relabeling an old frame. It remains a local candidate until visual
approval and a separately generated narrated V5 are complete.

## V3 release state

The V3 package was released from `agent/parallel-futures-showcase` as
`hackathon-2026-submission-v3`, which peels to
`5f7e3f7c8f984fd378f8c147038d84fb2e4983b3`. The public GitHub Pages build was
published at deployment commit
`c649178c638fcd8302d01a2e7ec7af7e705d54c4` and verified online with the
`4,608 futures` payload, zero page-level horizontal overflow, and no browser
console warnings or errors.

Existing organizer PR #39 was updated in place at fork commit
`2657aa23e84c9f75e4f55b8cdec49bba985a8870`. Fresh-clone verification passed
all ten package checksums; PR state was `OPEN`, non-draft, and `MERGEABLE`.
The organizer repository reports no configured status checks for the branch.
The PR remains unmerged for organizer review.

## Blocking owner inputs

Before opening the final organizer pull request, the owner must personally:

1. confirm that the Luma registration contains the legal name and the intended
   `Aegis Motion` team identity;
2. confirm a valid Discord ID and the personal age, sanctions/export-control,
   and employment eligibility facts;
3. accept the entry-license, publicity, release, prize-form, and tax terms
   summarized in the rules review.

The rules do not require the legal name in the public report or pull request,
so the public GitHub identity `@nvm-star-max` remains appropriate.

Do not add private email addresses, identity documents, cloud-account details,
tokens, or payment information to this directory.

## Evidence rule

Performance statements must map to the immutable Gate 3.2 schema-5 report in
[`../evidence/gate-3-2`](../evidence/gate-3-2). Gate 3.3 may be used only as
separately labeled breadth and limitation evidence. The bounded evaluator
smoke checks that the documented Radeon/Genesis execution path runs; it is not
a performance benchmark. Radeon scale and Parallel Futures measurements must
remain separately labeled compute evidence and must not be added to the formal
safety sample count.
