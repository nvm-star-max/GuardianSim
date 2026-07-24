# Radeon Cloud Session B Evidence

Date: 2026-07-25 (China Standard Time)

Session B validates the first real counterfactual candidate ranking on the AMD
Radeon Cloud GPU.

## Environment and command

- Instance: `u-13907-735d71cb`
- Template: `Blank OpenCode Workspace`
- GPU backend: `gs.amdgpu`
- Device: `AMD Radeon Graphics`
- Device memory reported by Genesis: `47.98 GB`
- Genesis: `1.2.3`
- Repository commit under test: `004e47c`
- Pick object: `011_banana`
- Seed: `41`

```bash
PYTHONUNBUFFERED=1 /opt/venv/bin/python \
  scripts/run_candidate_dry_run.py \
  --pick 011_banana \
  --seed 41 \
  --output outputs/guardian_dry_run/candidates.json
```

## Verified result

- Unit tests: 14/14 passed before the rerun.
- Process exit code: `0`.
- Five candidates were restored from the same snapshot and ranked.
- Snapshot fingerprint:
  `8a3692e8f016af7602ecb54e6f4db1cde765ce232138c9e72f8939ca2c8e2ee2`.
- Exact output: [`candidates.json`](candidates.json).

| Rank | Candidate | Predicted success | Risk | Utility | Stability |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | yaw `0°` | 0.4648 | 0.5862 | 0.7509 | 0.9043 |
| 2 | yaw `+22.5°` | 0.4293 | 0.5876 | 0.6945 | 0.8998 |
| 3 | yaw `-22.5°` | 0.4279 | 0.5878 | 0.6924 | 0.8990 |
| 4 | yaw `+45°` | 0.3945 | 0.5888 | 0.6391 | 0.8958 |
| 5 | yaw `-45°` | 0.3827 | 0.6007 | 0.6279 | 0.8559 |

## Interpretation and limitation

The real Genesis rollouts discriminate candidates and sensibly favor the
aligned `0°` grasp. All five candidates remain reachable and retain most of the
requested `0.10 m` lift.

However, every candidate reports `collision_margin_m = 0.0`. The current
scoring function therefore applies nearly the same, large collision-risk
penalty to every candidate. This result proves the end-to-end GPU rollout and
ranking path, but it is not yet sufficient evidence that the safety metric is
calibrated. The next gate should inspect which obstacle/link pair drives the
minimum clearance and add lateral-offset candidates before scaling to a
multi-episode benchmark.

## Incident resolved during the session

The first completed five-candidate run failed while exporting JSON because
Genesis returned NumPy/array-library scalar values. Commit `004e47c` added a
small JSON adapter for scalar and array-like values plus a regression test. The
same fixed-seed run then completed with exit code `0`.

The owner explicitly requested that the active cloud instance remain running;
it was not destroyed at the end of this evidence capture.
