# GuardianSim Hackathon Submission Plan

Last updated: 2026-07-27

This is the operational source of truth for turning GuardianSim into a valid
Track 3 submission before the announced deadline. Experimental protocols and
their frozen thresholds remain governed by the corresponding `GATE_*.md`
documents.

## 1. Submission contract

### Source priority

When requirements conflict or change, use this order:

1. Luma `Rules & Conditions`:
   <https://luma.com/amd-4dhi?utm_source=CN>
2. Official AMD contest repository:
   <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07>
3. Organizer announcements and live Q&A.
4. This repository's internal plans.

The Luma page and the Chinese cloud guide could not be read automatically from
the development environment. The owner must complete a final manual rules
check before submission and record any requirement not already listed here.

### Confirmed project identity

- Track: **Track 3 — Physical AI Challenge**
- Project: **GuardianSim**
- Repository: <https://github.com/nvm-star-max/GuardianSim>
- Core application: uncertainty-certified, counterfactual action selection for
  safer Franka fruit-picking in Genesis on AMD Radeon/ROCm.
- Claim boundary: simulation evidence only; no physical-robot deployment
  claim.

The group announcement's Track 1 examples are not a track change. GuardianSim
remains a Track 3 project.

### Announced timing

- Organizer announcement: submission closes **2026-08-06 23:59**.
- Working timezone: GMT+8, based on the event calendar previously shown during
  registration.
- Internal code and evidence freeze: **2026-08-05 23:59 GMT+8**.
- Target PR/submission time: **2026-08-06 18:00 GMT+8 or earlier**.
- The owner must re-check the exact deadline and timezone on Luma before the
  internal freeze.

### Official Track 3 package

The official contest repository requires:

1. An English technical report covering:
   - target application;
   - architecture and solution design;
   - training/evaluation datasets;
   - AMD Radeon GPU use;
   - innovations and technical contributions;
   - deliverables and output forms;
   - team members and contributions.
2. A dedicated source repository.
3. A detailed reproducibility README with environment setup, dependencies,
   commands, usage, and step-by-step result reproduction.
4. Preferably, a Docker image containing the complete source and runtime
   components.
5. A 3–5 minute demonstration video showing the complete workflow, including
   command-line or GUI operation, execution, and results.
6. Optional supplementary material such as a presentation or poster.
7. A fork of the official contest repository and an English pull request whose
   title follows `Track 3, <Team Name>, GuardianSim`.
8. All project descriptions, submission materials, and the pull request must
   be in English.

The live Radeon Cloud instance itself is not a submission artifact. Its exact
environment must be reproducible. At minimum preserve:

- operating-system and image/template identity;
- Radeon GPU, ROCm/HIP, PyTorch, Python, Genesis, and dependency versions;
- dependency lock files and installation scripts;
- asset and dataset origins plus download/setup steps;
- GPU preflight commands and expected output;
- exact smoke/demo/benchmark commands;
- expected report schema, representative checksums, and troubleshooting notes.

## 2. Current readiness

| Deliverable | State on 2026-07-27 | Required next proof |
| --- | --- | --- |
| Track and application direction | Ready | Keep Track 3 claim consistent everywhere |
| AMD Radeon/ROCm execution | Strong evidence | Add concise evaluator preflight |
| Dedicated source repository | Ready | Prepare stable public submission branch/tag |
| Formal benchmark evidence | Strong Gate 3.2 evidence | Preserve claim boundary and checksums |
| Breadth evidence | Gate 3.3 in progress | Finish only the authorized 12-scenario run |
| Reproducibility README | Partial | Clean-room reproduction from documented commands |
| Dependency/environment capture | Partial | Add a complete manifest and exact setup path |
| Docker image or Dockerfile | Missing | Produce and validate if feasible; document fallback |
| English technical report | Missing | Draft, review, and export final PDF |
| 3–5 minute complete demo | Missing | Record real workflow, GPU proof, comparison, results |
| Supplementary deck/poster | Missing | Produce only after report/video reach review quality |
| English official-repo PR | Missing | Fork, add submission entry/materials, open PR |
| Luma Rules sign-off | Manual action pending | Owner reads full page and records extra requirements |

## 3. Winning MVP

The minimum judge-facing workflow is:

1. Show `rocm-smi` and PyTorch/HIP detecting the AMD Radeon GPU.
2. Run one documented GuardianSim representative scenario.
3. Show the same scene's nominal and GuardianSim decisions.
4. Explain the risk certificate and why an action is accepted, replaced, or
   safely stopped.
5. Show the physical simulation outcome and machine-readable report.
6. Connect the example to the immutable Gate 3.2 aggregate evidence.
7. State limitations: Genesis simulation, frozen matrices, and no claim of
   universal or physical-robot safety.

This is more valuable for submission than adding an unbounded number of
experiments. The product story is:

> A nominal robot policy proposes an action; GuardianSim evaluates
> counterfactual alternatives on an AMD Radeon GPU, certifies uncertainty-aware
> safety margins, and executes the safest eligible action or stops.

## 4. Priority order

### P0 — Submission validity

- Manually verify Luma Rules & Conditions.
- Create an evaluator-first English reproducibility guide.
- Capture the exact Radeon Cloud environment.
- Produce a clean-room smoke command with expected output.
- Draft the English technical report and team contribution section.
- Record a complete 3–5 minute real-workflow video.
- Prepare the official fork and English pull request.

### P1 — Award quality

- Make the visual difference unmistakable with obstacle markers, action paths,
  safety margins, and decision reasons.
- Use the verified Gate 3.2 result as the primary quantitative claim.
- Present Gate 3.1 as the failure that motivated Gate 3.2, not as hidden
  negative evidence.
- Include the interactive showcase, architecture diagram, evidence checksums,
  and a concise competitive-value narrative.
- Complete one independent reproduction review by a clean agent or machine.

### P2 — Optional evidence depth

- Preserve the authorized Gate 3.3 12-scenario two-strata run.
- Run the remaining Gate 3.3 scenarios only if every P0 item is already on
  schedule.
- Do not start the proposed 120-scenario robustness gate before submission
  unless it cannot threaten the package, video, or reproduction deadline.

## 5. Calendar

### July 27–28 — Freeze the MVP and capture reproducibility

- Finish and preserve the authorized 12-scenario Gate 3.3 run without changing
  its frozen protocol.
- Add the exact environment manifest and evaluator preflight.
- Define one-command installation, smoke, demo, and report-validation paths.
- Start the English technical-report skeleton and architecture figure.
- Owner manually reviews Luma Rules & Conditions.

Exit criterion: a new evaluator can identify exactly what to install, run, and
expect without reading the worklog.

### July 29–30 — Clean-room reproduction

- Reproduce from a fresh checkout using only the submission documentation.
- Validate a practical Docker path, or document why a pinned native ROCm image
  is the supported fallback.
- Fix missing assets, implicit paths, version drift, and unstated cloud
  assumptions.
- Record environment and output checksums.

Exit criterion: the representative run completes from documented steps and the
report validator passes.

### July 31–August 1 — English report and submission narrative

- Complete report sections required by the official Track 3 README.
- Use only verified Gate 3.2 metrics for formal performance claims.
- Add Gate 3.3 only as separately labeled engineering breadth evidence after
  its report and checksums are preserved.
- Complete team-member and contribution text.

Exit criterion: report version 1 is complete enough for external review.

### August 2–3 — Final demonstration video

- Record the real Radeon GPU preflight, launch path, scene, decision evidence,
  execution, and aggregate result.
- Target 3–5 minutes; do not use a rejected replay as performance evidence.
- Add English narration or captions and readable overlays.
- Produce the final video, poster/deck draft, and checksums.

Exit criterion: a reviewer can understand the problem, innovation, AMD usage,
  physical effect, measured result, and limitation without repository context.

### August 4 — Independent evaluator rehearsal

- Give a clean machine/agent only the public repository and instructions.
- Record every ambiguity or failure and repair P0 issues.
- Verify all report, video, repository, and evidence links.

Exit criterion: independent reproduction and submission checklist both pass.

### August 5 — Internal freeze

- Freeze code, evidence, report, video, and supplementary material.
- Create the final release commit/tag and SHA-256 manifest.
- Draft the official English pull request and final Luma submission text.

Exit criterion: no unfinished mandatory artifact remains.

### August 6 — Submit with buffer

- Re-check Luma rules, deadline, timezone, file limits, and visibility.
- Fork/update the official repository and open the English PR.
- Complete the Luma submission no later than 18:00 GMT+8 if the platform
  permits.
- Save screenshots, URLs, timestamps, PR number, and final checksums.

## 6. Stop/go rules

- The active Gate 3.3 12-scenario run may finish and be preserved.
- After it finishes, pause new GPU experiments at the next major-stage gate.
- If clean-room reproduction has not passed by July 30, stop all optional
  benchmarks.
- If report version 1 is incomplete by August 1, stop supplementary polish.
- If the 3–5 minute video is not reviewable by August 3, all non-video P1/P2
  work stops.
- Never alter a frozen protocol or threshold after inspecting partial outcomes.
- Never present engineering smoke, rejected replay, or partial-stratum results
  as formal generalization evidence.

## 7. Ownership

- Owner:
  - manually read and accept Luma legal/rules text;
  - provide final team name and member/contribution details;
  - approve public visibility and final submission;
  - perform browser actions involving identity, acceptance, and final submit.
- Codex:
  - implementation, evidence preservation, documentation, report/video assets,
    reproducibility validation, checksums, and precise submission instructions.

## 8. Final acceptance checklist

- [ ] Luma rules manually reviewed and any extra requirements recorded.
- [ ] Track 3 identity and English naming are consistent.
- [ ] Public source commit/tag is fixed.
- [ ] English technical report PDF is complete.
- [ ] Reproducibility README passes a clean-room test.
- [ ] AMD Radeon/ROCm environment manifest is complete.
- [ ] Docker image/Dockerfile is validated, or the supported fallback is clear.
- [ ] 3–5 minute English demo video shows real execution and results.
- [ ] Formal claims map to preserved evidence and checksums.
- [ ] Team members and contributions are present.
- [ ] Supplementary material is complete if used.
- [ ] Official repository is forked and the English PR is ready.
- [ ] Final Luma submission and PR evidence are archived.
