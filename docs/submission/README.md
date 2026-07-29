# GuardianSim Submission Working Set

This directory contains the English source material for the Track 3
submission. It is a working set, not yet the final uploaded package.

## Current artifacts

- [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md): final technical-report source,
  aligned to the official Track 3 section list and limited to preserved
  metrics.
- [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf):
  visually inspected seven-page submission edition with no draft markings.
  The Radeon section now includes the separately scoped 1/16/64/256-world
  scale run and the 54-world Parallel Futures engineering run.
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
- [`FINAL_SUBMISSION_2026-07-28.md`](FINAL_SUBMISSION_2026-07-28.md): the
  verified organizer PR, commit, file list, checksums, and authorization
  record without private identity data.
- [`OFFICIAL_PR_DRAFT.md`](OFFICIAL_PR_DRAFT.md): the English official-repo
  pull-request title and body draft.
- **Public judge-facing showcase:**
  <https://nvm-star-max.github.io/GuardianSim/> (no sign-in required).
- [`official-package/Track3-Aegis-Motion-GuardianSim`](official-package/Track3-Aegis-Motion-GuardianSim):
  self-contained directory prepared for the official contest fork. It now
  includes the report, the 80-second supplementary Radeon preview, the raw
  scale/Parallel Futures reports, validator outputs, and recursive checksums.

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

The owner accepted the optically centered 80-second Radeon scale-first V4 on
2026-07-29 as a supplementary preview. It does not replace the previously
approved 4:41 V2 workflow video because the official Track 3 guidance
recommends a 3-5 minute complete-workflow demonstration.

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
