# GuardianSim Submission Working Set

This directory contains the English source material for the Track 3
submission. It is a working set, not yet the final uploaded package.

## Current artifacts

- [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md): final technical-report source,
  aligned to the official Track 3 section list and limited to preserved
  metrics.
- [`GuardianSim-Technical-Report.pdf`](GuardianSim-Technical-Report.pdf):
  visually inspected six-page submission edition with no draft markings.
- [`DEMO_VIDEO_SCRIPT.md`](DEMO_VIDEO_SCRIPT.md): a 4:00–4:30 production
  script designed to make the baseline/GuardianSim physical difference
  visually explicit.
- [`GuardianSim-Aegis-Motion-demo-review-v1.mp4`](GuardianSim-Aegis-Motion-demo-review-v1.mp4):
  a strictly validated 4:15 English-narrated review cut. It combines the
  accepted formal replay with preserved Radeon environment, evaluator,
  aggregate-result, and safe-stop evidence.
- [`GuardianSim-Aegis-Motion-demo-review-v1.json`](GuardianSim-Aegis-Motion-demo-review-v1.json):
  machine-readable narration, source hashes, timing, claim boundary, and
  verified metrics for the review cut.
- [`GuardianSim-Aegis-Motion-demo-review-v1-validation.json`](GuardianSim-Aegis-Motion-demo-review-v1-validation.json):
  strict duration, decode, source-identity, metric, and claim-boundary
  validation.
- [`GuardianSim-Aegis-Motion-demo-review-v2.mp4`](GuardianSim-Aegis-Motion-demo-review-v2.mp4):
  the 4:41 review cut with Qwen3-TTS Instruct narration, fixed per-chapter
  captions, and normalized presentation loudness.
- [`GuardianSim-Aegis-Motion-demo-review-v2.json`](GuardianSim-Aegis-Motion-demo-review-v2.json):
  V2 narration model, voice, instructions, per-segment audio hashes, timing,
  evidence bindings, and verified metrics.
- [`GuardianSim-Aegis-Motion-demo-review-v2-validation.json`](GuardianSim-Aegis-Motion-demo-review-v2-validation.json):
  strict V2 narration, caption-policy, duration, decode, source-identity,
  metric, and claim-boundary validation.
- [`../../output/pdf/GuardianSim-Technical-Report-DRAFT.pdf`](../../output/pdf/GuardianSim-Technical-Report-DRAFT.pdf):
  visually reviewed six-page A4 draft for owner review. It is labeled as a
  draft and identifies the solo team as Aegis Motion.
- [`COMPETITOR_SCAN_2026-07-27.md`](COMPETITOR_SCAN_2026-07-27.md): a
  time-stamped inventory of the official repository and GuardianSim's
  evidence-backed competitive position.
- [`OFFICIAL_PR_DRAFT.md`](OFFICIAL_PR_DRAFT.md): the English official-repo
  pull-request title and body draft.
- [`official-package/Track3-Aegis-Motion-GuardianSim`](official-package/Track3-Aegis-Motion-GuardianSim):
  self-contained directory prepared for the official contest fork.

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

## Blocking owner inputs

Before exporting or submitting the report:

1. confirm whether the organizer requires the owner's legal name in the public
   report, rather than the verified public GitHub identity;
2. manually review the complete Luma Rules & Conditions;
3. approve the final public repository, video, report, and submission.

Do not add private email addresses, identity documents, cloud-account details,
tokens, or payment information to this directory.

## Evidence rule

Performance statements must map to the immutable Gate 3.2 schema-5 report in
[`../evidence/gate-3-2`](../evidence/gate-3-2). Gate 3.3 may be used only as
separately labeled breadth and limitation evidence. The bounded evaluator
smoke proves that the documented Radeon/Genesis execution path works; it is
not a performance benchmark.
