# GuardianSim Final Hackathon Submission Record

Recorded: 2026-07-28 (GMT+8)

## Entry

- Event: AMD AI DevMaster Hackathon
- Track: Track 3 - Physical AI
- Team: Aegis Motion
- Application: GuardianSim
- Official pull request:
  <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39>
- Pull-request title: `Track 3, Aegis Motion, GuardianSim`
- State at verification: `OPEN`
- Draft: no
- Mergeability at verification: `MERGEABLE`
- Base: `AMD-DEV-CONTEST/Radeon-hackathon-2026-07:main`
- Head:
  `nvm-star-max:submission/track3-aegis-motion-guardiansim`
- Head commit:
  `abd0cfd72056eefe94298f513449e4f48842620b`

## Submitted files

1. `.gitattributes`
2. `submissions/Track3-Aegis-Motion-GuardianSim/README.md`
3. `submissions/Track3-Aegis-Motion-GuardianSim/GuardianSim-Technical-Report.pdf`
4. `submissions/Track3-Aegis-Motion-GuardianSim/SHA256SUMS`

The path-scoped attribute marks the report as binary. The report is 19,435
bytes, and the copied README and PDF both passed the submitted checksum
manifest.

## Linked deliverables

- Public source/evidence identity:
  `25e27aced13237b5af93fd91697d7abb12101a30`
- Public release payload tag:
  `hackathon-2026-submission-v1`
- Owner-approved video SHA-256:
  `e235a315cf4370ccd10cce5f50d317a7ec3376725940235482b530a641804888`
- Final report SHA-256:
  `d4d5596645c4f971280f779eb585d0e675b62695d5f114db72dbbbf398054a66`

At submission verification, the immutable source, video, evidence, and Docker
reproduction URLs in the pull-request body all returned HTTP 200.

## Rules and authorization

The official 15-page Rules and Conditions were reviewed and reconciled before
submission. The owner then explicitly confirmed the personal eligibility and
legal terms and authorized final submission. No legal name, private contact
detail, account credential, payment information, or identity document is
stored in this record.

Under the official process, accepted Luma registration establishes prize
eligibility and the official-repository pull request is the project entry.
No separate project-upload form was stated in the governing document or the
official repository instructions.

## Local post-submission update prepared on 2026-07-29

The record above describes the public PR exactly as verified on 2026-07-28.
It has not been rewritten.

A separate local update is now prepared but has not been pushed to GuardianSim
or organizer PR #39. It adds:

- a seven-page technical report with separately scoped Radeon scale evidence;
- an 80-second supplementary Radeon/Parallel Futures preview;
- raw scale and Parallel Futures reports plus validator outputs;
- an updated recursive package checksum manifest.

The local report SHA-256 is
`6a735fe0a77c0c6ec3e9461051bac29ce371a3ca04d74246f0d39d6a64a3291c`.
The local package-manifest SHA-256 is
`392e624b5839e4af0799d59d321ae27d31b12a34cb225fe20d342bd4ceef0d94`.

## Public P0 update completed on 2026-07-29

The owner authorized the release and PR update.

- GuardianSim release commit:
  `830e4fc8e2467bc4a0eacbb9777b91351e20f924`
- Immutable release tag:
  `hackathon-2026-submission-v2`
- Official fork update commit:
  `d73bad667db22d67d737ec50ceb8ff761b0c3816`
- Organizer PR:
  <https://github.com/AMD-DEV-CONTEST/Radeon-hackathon-2026-07/pull/39>
- Verified PR state: `OPEN`, non-draft, merge state `CLEAN`
- Supplementary preview SHA-256:
  `2be66996eb0e3bb460148c5afc8060f69680f1d7e314e2e46cf2d363d53a923a`

The remote package files were downloaded after the update and passed their
recursive checksum manifest. The PR was not merged.

## Public judge showcase completed on 2026-07-29

The owner authorized public access to the interactive evidence arena. The
existing Sites workspace did not permit internet-public access, so an
independent static build was published through GitHub Pages:

<https://nvm-star-max.github.io/GuardianSim/>

- GuardianSim static-build source commit:
  `1d66d3ffe6d6a05956d4e4ae314347f1ebb9d073`
- GitHub Pages deployment commit:
  `3b4b438b57d3d7c1539f74c33e8c14358fe45cc1`
- Updated official fork commit:
  `289e4c09211974f12f74b8298e493ab93e78037f`
- Updated official-package manifest SHA-256:
  `5ffab05ff5ef602fefc6b42f1d993090a113f411fb2bc8ab16c45d1868fee621`

An unsigned request verified HTTP 200 responses for the public HTML, compiled
JavaScript, stylesheet, Seed 411 replay video, and social-preview image. The
organizer PR now presents this no-sign-in arena before the metric summary and
remains open, non-draft, and cleanly mergeable. The PR was not merged.

## Local V3 decision-scale update prepared on 2026-07-30

This section records work prepared after the public V2 update. It does not
claim that organizer PR #39 or a V3 release tag already contains the payload.

- Added the completed Safety Swarm V2 formal result:
  18 candidates × 256 uncertainty worlds = 4,608 candidate-world pairs.
- Preserved the complete 5.7 MB report, strict validator receipt, logs,
  environment, protocol, source identity, and recursive checksums in the
  GuardianSim repository.
- Updated the judge-facing website to render the exact 18 × 256 matrix and
  `4,608 → 5 → 1` decision funnel.
- Rebuilt the final seven-page technical report. PDF SHA-256:
  `4028372be15ca2fba2a0cd7f1ddd7e51c8d9cd012521e4be80cc40a523500ef3`.
- Added a compact formal summary and validation receipt to the organizer
  package while keeping the full report in the dedicated source repository.
- Kept the approved 4:41 workflow video and 80-second Radeon preview unchanged;
  neither is relabeled as footage of the later 4,608-pair run.
- Published the updated static showcase to GitHub Pages at deployment commit
  `c649178c638fcd8302d01a2e7ec7af7e705d54c4`. An unsigned online check loaded
  asset `assets/index-DZNAy0i7.js` and confirmed the `4,608 futures` payload.
  Browser QA recorded zero page-level horizontal overflow and no console
  warnings or errors.

Planned immutable release tag: `hackathon-2026-submission-v3`. It must not be
created until final checks pass. Updating organizer PR #39 remains an external
publication step requiring owner authorization.
