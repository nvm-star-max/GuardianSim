# Gate 2.7 Fixed-Seed Benchmark Evidence

Twenty paired baseline-versus-GuardianSim episodes ran on Radeon Cloud from
commit `f0cc4e3`. Seeds `101–120` produced 20 unique episode snapshot
fingerprints. Each strategy was independently re-executed from the same
per-episode snapshot.

## Result

| Metric | Nominal baseline | GuardianSim | Paired difference |
| --- | ---: | ---: | ---: |
| Success | 20/20 (100%) | 17/20 (85%) | -15 percentage points |
| Mean clutter clearance | 0.04399 m | 0.07438 m | +0.03038 m |
| Mean retained-lift stability | 0.90413 | 0.76416 | -0.13996 |

GuardianSim increased clutter clearance in all 20 episodes, by
`0.02610–0.03600 m`, and neither strategy produced a measured clutter overlap.
However, GuardianSim had lower independent-execution stability in 19/20
episodes.

Candidate selections:

- `yaw_-22.5_offset_+0.020`: 10
- `yaw_-22.5_offset_+0.000`: 7
- `yaw_-22.5_offset_-0.020`: 3

All three negative-offset selections failed:

| Seed | Candidate | Counterfactual success estimate | Independent stability |
| ---: | --- | ---: | ---: |
| 104 | `yaw_-22.5_offset_-0.020` | 0.78783 | 0.0 |
| 107 | `yaw_-22.5_offset_-0.020` | 0.85040 | 0.0 |
| 120 | `yaw_-22.5_offset_-0.020` | 0.70665 | 0.0 |

The baseline stability in those episodes was `0.90059–0.90573`. This is a
repeatability failure: a single counterfactual rollout can overestimate a
candidate that fails when independently replayed. The current one-shot ranking
therefore buys additional clearance too aggressively.

## Gate decision

Gate 2.7 is a valid benchmark but not a winning final result. Do not tune the
published evidence or hide the negative outcome. The next planner revision
should use repeated confirmation rollouts with conservative aggregation and a
nominal fallback when stability evidence is weak. Rerun the same seeds only
after that rule is fixed in advance.

Raw evidence:

- [`report.json`](report.json)
- [`report.log`](report.log)

SHA-256:

- `report.json`:
  `8de796a466ec3ca902c9527939f257fa2bafb77d70eb4d2d02d3983d6a8dde36`
- `report.log`:
  `1974c57c3cfbac8b8c4b70c208e3d18638a17ba1e325d11e660ee2fcaf03fea9`

