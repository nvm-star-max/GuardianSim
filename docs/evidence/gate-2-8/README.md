# Gate 2.8 Robust-Selection Benchmark Evidence

The repeatability-aware policy was fixed before this run:

- score all 15 candidates once;
- confirm the top three plus the nominal action;
- run two additional confirmations for each shortlisted action;
- aggregate clearance, reachability, alignment, and stability pessimistically;
- require worst-observed stability of at least `0.60`;
- require robust predicted success at least `0.02` above nominal;
- otherwise fall back to nominal.

The benchmark ran on Radeon Cloud from commit `3c63236`. Cloud verification
passed 24/24 tests before execution.

## Result

Seeds `101–120` produced 20 unique episode fingerprints. Baseline and
GuardianSim were independently executed from each episode snapshot.

| Metric | Nominal baseline | GuardianSim | Paired difference |
| --- | ---: | ---: | ---: |
| Success | 20/20 (100%) | 20/20 (100%) | 0 percentage points |
| Mean clutter clearance | 0.04399 m | 0.07212 m | +0.02813 m (+63.93%) |
| Mean retained-lift stability | 0.90338 | 0.89731 | -0.00607 |

Compared with the unchanged Gate 2.7 one-shot selector, Gate 2.8 improved
GuardianSim success from 17/20 to 20/20 and mean stability from `0.76416` to
`0.89731`. Mean clearance decreased by `0.00226 m` versus Gate 2.7 GuardianSim,
but remained `0.02813 m` above the nominal baseline.

The report contains 240 recorded confirmation observations:
20 episodes × 4 confirmed candidates × 3 observations (one initial and two
additional rollouts). The nominal fallback activated once, on seed 113, and
succeeded.

Candidate selections:

- `yaw_-22.5_offset_+0.020`: 10
- `yaw_-22.5_offset_+0.000`: 8
- `yaw_+45.0_offset_+0.020`: 1
- nominal `yaw_+00.0_offset_+0.000`: 1

The three Gate 2.7 failure seeds all succeeded in both the authorized smoke
reruns and the full benchmark:

| Seed | Full-run candidate | Stability | Clutter clearance |
| ---: | --- | ---: | ---: |
| 104 | `yaw_-22.5_offset_+0.000` | 0.89350 | 0.07901 m |
| 107 | `yaw_-22.5_offset_+0.000` | 0.89694 | 0.08319 m |
| 120 | `yaw_-22.5_offset_+0.020` | 0.90201 | 0.05365 m |

## Validation

- evidence schema: `3`;
- completed episodes: `20/20`;
- seed sequence: contiguous `101–120`;
- unique episode fingerprints: `20`;
- confirmation shortlist size: `3` plus nominal;
- additional confirmation rollouts: `2`;
- minimum stability: `0.60`;
- minimum success margin: `0.02`;
- normal process exit: `GATE28_FULL_EXIT:0`;
- report log contains no Python traceback.

The terminal screenshot preserves the exit code because the shell `echo`
occurred after the `tee` command finished and therefore is not present in
`report.log`.

## Raw evidence

- [`report.json`](report.json)
- [`report.log`](report.log)
- [`terminal-final.png`](terminal-final.png)
- [`failure-seed-104.json`](failure-seed-104.json)
- [`failure-seed-104.log`](failure-seed-104.log)
- [`failure-seed-107.json`](failure-seed-107.json)
- [`failure-seed-107.log`](failure-seed-107.log)
- [`failure-seed-120.json`](failure-seed-120.json)
- [`failure-seed-120.log`](failure-seed-120.log)

SHA-256:

- `report.json`:
  `018deb70e6540f638bbfb732e5ec85ba847e0a5de7ffe807d9fd274299f2fad0`
- `report.log`:
  `b5255deb6db5720114dfb3e68a56bfeefe0ff9a49f0102d77b56e52a182cce04`
- `terminal-final.png`:
  `df14058ff79db6d5cfc33d356de051a64a9eb473289320e7b6cda9fc118e55eb`
- `failure-seed-104.json`:
  `1bce42417d7cd9060cabd8003c1a1841ed655640479d265adc0b75ad47a93be3`
- `failure-seed-104.log`:
  `8c34226f88a96c54b231e52f5c932cb49554e67641693a76f0db4197a6437108`
- `failure-seed-107.json`:
  `6588826c3d4a122ff1f6012d97d0122f3e3516f6e0ec81542cfe9ae436add566`
- `failure-seed-107.log`:
  `8258e180cd0734c792bdea2dabe2e012c19bcd38168e17756b749f92c3f79822`
- `failure-seed-120.json`:
  `bf3351a50a3e39fb8d864de0046582cd8b495f148d7d7f3acb81ce6ad6b9a287`
- `failure-seed-120.log`:
  `1aae74b91b4868d9b33d87252b4725584d81a9202088f26a79f348d8b653ded7`
