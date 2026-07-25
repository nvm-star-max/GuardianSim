# Gate 3.1 formal Radeon Cloud evidence

Gate 3.1 is the frozen, 30-episode multi-object adversarial safety benchmark.
It was declared before the Radeon Cloud run and completed without changing its
protocol, thresholds, scenario order, or existing smoke prefix.

This is a negative primary result. GuardianSim increased mean clutter clearance
but did not improve safe completion on the broader challenge distribution.

## Reproducibility

- Radeon Cloud instance: `u-13907-735d71cb`
- Execution commit: `bca798a`
- Schema: `4`
- Seeds: contiguous `301–330`
- Completed episodes: `30/30`
- Protocol SHA-256:
  `472bb6ea13984dff02124c091ac8d94c67154bbe68858bb782aed8014d2afbba`
- Scenario-matrix SHA-256:
  `b3ba08b367a0c634f66ddbba8670311c9b449aaa4ad7ee55d418bca7c2147936`
- Full validator exit code: `0`
- Cloud tests: `30/30` passed
- Local full validation: passed

Evidence hashes:

- `report.json`:
  `5ac9c37709372627031ea59ab83942e8e0766a449b800d22d06ccffd11936a86`
- `formal.log`:
  `c36adce4176ea03bea3863d9fe3ce04920d17410f8be8eb0aeff1316a08d9a9c`
- `validation.json`:
  `10b16df9a6e4c16c0126376312de5546ab6278ffa290cc3dc552f95defcf7504`
- `cloud-tests.log`:
  `b26b76f94f51b37e132091657a76e5877eb6170306de684985ab6eddea8aacb5`

## Verified results

| Metric | Nominal baseline | GuardianSim | Difference |
| --- | ---: | ---: | ---: |
| Safe completion | 19/30 (63.33%) | 18/30 (60.00%) | -3.33 pp |
| Ordinary task success | 20/30 (66.67%) | 18/30 (60.00%) | -6.67 pp |
| Clutter contact | 10/30 (33.33%) | 10/30 (33.33%) | 0 pp |
| Mean clutter clearance | 0.02157 m | 0.03099 m | +0.00942 m (+43.67%) |
| Mean retained-lift stability | 0.90845 | 0.85091 | -0.05754 |

Paired safe-completion outcomes:

- both safe: 17;
- both unsafe: 10;
- GuardianSim only safe: 1;
- baseline only safe: 2.

GuardianSim used nominal fallback in 19/30 episodes. The mean planning wall time
was `184.84 s` per episode; independent baseline and GuardianSim executions
averaged `8.68 s` and `8.56 s`.

## Cell diagnosis

- Banana/lateral: GuardianSim improved safe completion from 4/5 to 5/5 and
  raised mean clearance from `0.04548 m` to `0.08718 m`.
- Banana/radial: both achieved 5/5; GuardianSim raised mean clearance from
  `0.02674 m` to `0.04545 m`.
- Lemon/lateral: both had 5/5 clutter contacts and 0/5 task success.
- Lemon/radial: baseline achieved 5/5; GuardianSim achieved 4/5 because of one
  unstable lift.
- Plum/lateral: both had 5/5 clutter contacts and 0/5 task success.
- Plum/radial: baseline achieved 5/5; GuardianSim achieved 4/5 because of one
  unstable lift.

The two lateral-contact cells show that the current 15-action
yaw/lateral-offset family cannot resolve those obstacle geometries. The two
GuardianSim-only unstable lifts show that repeatability risk remains under the
broader object distribution. Higher average clearance alone therefore cannot
be claimed as improved safety.

## Raw files

- [`report.json`](report.json)
- [`formal.log`](formal.log)
- [`validation.json`](validation.json)
- [`cloud-tests.log`](cloud-tests.log)

All results are Genesis simulation evidence on an AMD Radeon GPU, not
physical-robot evidence.

