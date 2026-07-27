# Radeon Evaluator Smoke Evidence - Commit 58a76d4

This directory preserves the accepted Radeon Cloud evaluator-path smoke for
GuardianSim commit
`58a76d407a255f11d57bc401dcecb2604eafaca8`.

## Claim boundary

This smoke proves that a fresh evaluator path can:

1. identify a real AMD Radeon/ROCm environment;
2. validate the source and preserved formal Gate 3.2 report;
3. build and render the real Genesis Franka scene on `gs.amdgpu`;
4. restore one fingerprinted snapshot for three counterfactual candidates;
5. produce and strictly validate the candidate report.

It is not a performance benchmark. The submission's performance claims remain
derived only from the immutable Gate 3.2 30-scenario schema-5 report.

## Verified environment

- Cloud provider: AMD Radeon Cloud
- Template: Blank OpenCode Workspace
- Instance used for capture: `u-13907-735d71cb`
- Operating system: Ubuntu 24.04.4 LTS, x86_64
- GPU count: 1
- GPU: AMD Radeon Graphics, PCI model `0x744b`, GFX `gfx1100`
- Python: 3.12.3 from `/opt/venv/bin/python3`
- PyTorch: `2.9.1+gitff65f5b`
- HIP: `7.2.53211-e1a6bc5663`
- Genesis: 1.2.3
- Source dirty state: `false`
- Environment readiness: `gpu_ready: true`

## Verified outcomes

- Cloud unit tests from the tested commit: 54/54
- Strict preserved Gate 3.2 validation: 30 episodes
- Gate 3.2 protocol SHA-256:
  `8f23247001e05f39817225ed13f028321fbb9b9c694aaacd5b987fe61ee1fb3c`
- Real Genesis scene probe: `passed`
- Counterfactual candidate count: 3
- Candidate validation: `true`
- Snapshot fingerprint:
  `8a3692e8f016af7602ecb54e6f4db1cde765ce232138c9e72f8939ca2c8e2ee2`
- Top smoke candidate: `yaw_+00.0_offset_+0.000`

## Integrity

Downloaded archive:

`evaluator-smoke-58a76d4.tar.gz`

Archive SHA-256:

`6457a20c7a1740eba2df5e62334a3f0c0bce55c4de4fface2675c9cd9861249c`

The cloud archive was downloaded through the normal Jupyter file browser. Its
path list was checked before extraction; no absolute or parent-traversal paths
were present. After local extraction, all 16 entries declared by the root
`SHA256SUMS` manifest passed verification. The expanded files are preserved
unchanged under [`raw`](raw).

Local verification:

```bash
cd docs/evidence/evaluator-smoke-58a76d4
shasum -a 256 -c ARCHIVE_SHA256
cd raw
shasum -a 256 -c SHA256SUMS
```
