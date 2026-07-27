# GuardianSim Submission Working Set

This directory contains the English source material for the Track 3
submission. It is a working set, not yet the final uploaded package.

## Current artifacts

- [`TECHNICAL_REPORT.md`](TECHNICAL_REPORT.md): complete technical-report V1,
  aligned to the official Track 3 section list and limited to preserved
  metrics.
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
- [`../../output/pdf/GuardianSim-Technical-Report-DRAFT.pdf`](../../output/pdf/GuardianSim-Technical-Report-DRAFT.pdf):
  visually reviewed six-page A4 draft for owner review. It is labeled as a
  draft and identifies the solo team as Aegis Motion.
- [`COMPETITOR_SCAN_2026-07-27.md`](COMPETITOR_SCAN_2026-07-27.md): a
  time-stamped inventory of the official repository and GuardianSim's
  evidence-backed competitive position.
- [`OFFICIAL_PR_DRAFT.md`](OFFICIAL_PR_DRAFT.md): the English official-repo
  pull-request title and body draft.

Rebuild the review PDF with ReportLab:

```bash
python scripts/build_technical_report_pdf.py
```

The build script is separate from the evaluator runtime. Install `reportlab`
only on a documentation workstation if it is not already available.

Rebuild and validate the narrated review video on macOS:

```bash
uv run --frozen --no-sync python scripts/build_submission_video.py
uv run --frozen --no-sync python scripts/validate_submission_video.py \
  --output docs/submission/GuardianSim-Aegis-Motion-demo-review-v1-validation.json
```

The generated narration uses the local macOS Samantha voice and is suitable
for content review. A human narration take and a real-time final-commit Radeon
terminal capture remain recommended before declaring the upload final.

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
