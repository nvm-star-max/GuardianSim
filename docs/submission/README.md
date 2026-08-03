# GuardianSim Submission Working Set

This directory contains the English source material and immutable release
records for the Track 3 submission.

## Current artifacts

- [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md): final technical-report source,
  aligned to the official Track 3 section list and limited to preserved
  metrics.
- [`../../output/pdf/GuardianSim-Technical-Report.pdf`](../../output/pdf/GuardianSim-Technical-Report.pdf):
  final eight-page Scale V3 report generated from the source below.
- [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf):
  package copy of that final report.
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
- [`GuardianSim-Radeon-Scale-V3-narrated-v3.mp4`](GuardianSim-Radeon-Scale-V3-narrated-v3.mp4):
  owner-approved 90-second Scale V3 Radeon preview with Qwen `Ethan` narration,
  fixed captions, and the formal Seed 411 simulation replay finale.
- [`GuardianSim-Radeon-Scale-V3-narrated-v3.json`](GuardianSim-Radeon-Scale-V3-narrated-v3.json),
  [`GuardianSim-Radeon-Scale-V3-narrated-v3.ass`](GuardianSim-Radeon-Scale-V3-narrated-v3.ass),
  and [`GuardianSim-Radeon-Scale-V3-narrated-v3-validation.json`](GuardianSim-Radeon-Scale-V3-narrated-v3-validation.json):
  source identity, narration, caption, locked-metric, and strict decode receipts.
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
- [`OFFICIAL_PR_BODY_V5.md`](OFFICIAL_PR_BODY_V5.md): the exact approved V5
  body for updating organizer PR #39 in place.
- **Public judge-facing showcase:**
  <https://nvm-star-max.github.io/GuardianSim/> (no sign-in required). The
  published V3 static build promotes the exact 4,608-pair matrix and
  `4,608 → 5 → 1` funnel.
- [`official-package/Track3-Aegis-Motion-GuardianSim`](official-package/Track3-Aegis-Motion-GuardianSim):
  self-contained V5 package for the existing official contest PR. It includes
  the Scale V3 report, approved 90-second preview, strict schema-3 scale report,
  compact Safety Swarm V2 summary, validator outputs, and recursive checksums.

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

Those approved videos remain unchanged evidence-bound artifacts. The silent
review V4 binds the later Scale V2 and 4,608-pair formal reports without
relabeling an old frame; its owner-approved narrated V5 is the V4 package's
80-second supplementary Radeon preview.

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

## V5 release state

The owner approved the Scale V3 presentation on 2026-08-03. V5 promotes the
verified 16,384-world endurance result, 293,601,280 measured environment steps,
278,051 env-steps/s P50, 98.330% full-suite weighted mean GPU use, and 22.05
GiB peak VRAM. The units remain separate from the 4,608 → 5 → 1 decision
funnel and the 30-scenario safety result.

The approved 90-second narrated preview is
[`GuardianSim-Radeon-Scale-V3-narrated-v3.mp4`](GuardianSim-Radeon-Scale-V3-narrated-v3.mp4).
Its sidecar, fixed captions, and strict validation receipt are retained beside
it. V4 remains immutable as historical evidence.

V5 was released as annotated tag `hackathon-2026-submission-v5`, which peels
to `32ded989d575602f0427badaf98e4c1a20d92934`. Pages was deployed at
`bc7167770fd2b79466e0f2bfe973d22354f8168e`. The official package is at fork
commit `49c94b37bdf2b5fff28a3b215cba873aae1a14a1`; a fresh API archive passed
all ten payload checksums and reproduced manifest SHA-256
`827f442d5f31d7824f2699c3c1853cd5e6f544abb549f3a9ec0824370b9d98d6`.
Existing PR #39 remains open, non-draft, and mergeable.

## V4 release state

The Scale V2 release was published from `agent/parallel-futures-showcase` as
annotated tag `hackathon-2026-submission-v4`, which peels to
`0710dca1de8e7627c19a992164169c41e70ac338`. GitHub Pages was deployed at
`43af7d9578ff0f992fd1b3b242e59400123ede8f` with the 4,096-world Scale V2
receipt and policy-to-Radeon decision narrative.

The official package was synchronized to the existing contest-fork branch at
`2dad3d4037b4cf7c3ed7dd6a8ea64df874dc7f62`. Existing organizer PR #39 was
updated in place and verified `OPEN`, non-draft, and `MERGEABLE`. All ten
package checksums passed from a fresh GitHub API branch archive; the manifest
SHA-256 is
`f8a18439e1b1009ae807e79142f499df4a65de939c7f5e83729e0647afd8b0bd`.
The PR remains unmerged for organizer review.

## Owner-controlled eligibility record

The owner previously confirmed these private items before the public release
and remains responsible for their accuracy:

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
