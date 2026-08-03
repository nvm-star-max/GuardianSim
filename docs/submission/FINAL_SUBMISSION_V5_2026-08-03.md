# GuardianSim V5 publication record — 2026-08-03

This record supersedes the public presentation layer of V4 without changing or
moving any V1–V4 tag, report, threshold, or historical artifact.

## Owner-approved release scope

- Slogan: **Think Thousands. Execute One.**
- Public website: Scale V3 first, decision funnel second, robot replay last.
- Technical report: final eight-page Scale V3 submission edition.
- Supplementary preview: approved 90-second narrated V3 with formal Seed 411
  simulation replay in the final ten seconds.
- Organizer workflow: replace only the existing project package and update
  organizer PR #39 in place. Do not open, close, or merge another PR.

## Frozen V5 artifacts before publication

| Artifact | SHA-256 |
| --- | --- |
| Scale V3 report file | `dd640537b820a85a30f0fca8012ca269512dd855d873bcf5e3ad968bb91dfa48` |
| Scale V3 sealed evidence manifest | `6d8364bacacd31b627e67c2af6e965521cd1af0d49eb80e0d81aede12dea63f7` |
| Final technical-report PDF | `9707b3c49c2a74eeb74a1dc898bf7b49d133012a2a8892b3b9ce0c7e96d2cc47` |
| Narrated Scale V3 preview | `2ac6959ed73588d60e0cdea0aa901330a13e5ff60f8fca620704c718679c850e` |
| Narrated sidecar | `ac65e5075638d6b6fbc0b643484988a67fb7f096260735019b596b247c611e58` |
| Fixed captions | `bb626f978518ca03b465370489484e0752077c5f53e30bdd29095d74a913f825` |
| Narrated validation receipt | `71d802a7d0b24b8dc88cd7ba733dc5fb2d6b579621ccabad5ff92caa9eaf438d` |
| Organizer-package manifest | `827f442d5f31d7824f2699c3c1853cd5e6f544abb549f3a9ec0824370b9d98d6` |

The organizer package is 4,127,637 bytes including its manifest. It contains
ten payload files plus `SHA256SUMS`.

## Verified V5 headline metrics

- 16,384 complete parallel Genesis robot worlds;
- 278,051.244 environment-steps/s P50 and 278,660.488 P95;
- 293,601,280 measured environment steps across 15 independent processes;
- 98.330% weighted mean GPU utilization and 100% observed peak;
- 22.05 GiB peak VRAM;
- separate decision funnel: 4,608 candidate-world pairs → 5 qualifiers → 1
  selected action;
- separate Gate 3.2 result: 18/30 → 30/30 repeatable safe scenarios, 58/90 →
  90/90 independent safe Genesis simulations, and 30 → 0 sampled clutter
  contacts.

Environment steps, candidate-world pairs, and independent simulations are
never added together.

## Local release gate

- 116/116 Python tests passed.
- Python compilation passed.
- Strict Scale V3 schema-3 validation and every sealed evidence checksum
  passed.
- 5/5 server-rendered and 3/3 static Pages tests passed.
- Both website builds and ESLint passed.
- Strict silent and narrated Scale V3 media validation passed; the packaged
  video is byte-identical and passed complete audio/video decode.
- The latest PDF was rendered to eight PNG pages and inspected page by page;
  no clipping, overlap, broken table, draft marker, or unreadable glyph was
  found.
- All organizer-package checksums and `git diff --check` passed.

## Publication receipt

The exact source commit, annotated V5 tag object, Pages commit, organizer fork
commit, normalized PR-body hash, public-link checks, and fresh-download package
verification are appended to `PROJECT_MEMORY.md` and `WORKLOG.md` only after
the remote operations succeed.
