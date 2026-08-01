# Safety Swarm Radeon smoke evidence

This directory records the predeclared engineering-smoke gate that preceded
the frozen 256-world Safety Swarm run. The smoke reports are not formal
results, remain `showcase_ready=false`, and must not be merged into the
256-world population.

## What happened

1. The first 4-world run used the wrong already-defined candidate: an extra
   `25 mm` retreat caused all four gripper approaches to miss the target. The
   report is preserved as implementation-error evidence; no threshold or
   uncertainty row was changed.
2. The candidate binding was corrected from the preserved Gate 3.2 replay to
   `yaw_+67.5_retreat_+0.000_approach_+0.140`. The repeated 4-world smoke
   passed `4/4` with zero clutter contacts.
3. The predeclared balanced 16-world smoke passed `12/16`. Three worlds made
   sampled clutter contact and one additional world missed the frozen
   `10 mm` clearance gate.

Because the 16-world gate did not pass, the 256-world formal run was not
started. The frozen matrix, protocol, thresholds, and row order were not
changed after observing these outcomes.

## Verified smoke measurements

| Run | Safe | Contacts | Worst clearance | Min stability | Wall time | Environment steps/s | Peak AMD GPU use |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Corrected 4-world | 4/4 | 0 | 16.372 mm | 0.925 | 8.323 s | 239.806 | 89% |
| Balanced 16-world | 12/16 | 3 | 0 mm | 0 | 10.676 s | 747.843 | 94% |

The four failing 16-world rows were:

- world `69`: `9.680 mm` clearance, no contact, stability `1.0`;
- world `91`: contact, zero clearance, zero stability, task failure;
- world `109`: contact, zero clearance, zero stability, task failure;
- world `209`: contact, zero clearance, zero stability, task failure.

These figures describe two engineering-smoke batches on the Radeon Cloud
instance. They are useful for debugging and scale-path verification, not as a
headline robustness claim.

## Provenance

- Local source commit: `738da71c2221c6c5e7ec2120a0f95d0ce42e3e69`
- Cloud evidence commit: `599c04770aca17b32971ed417d678122dbe4c453`
- Frozen matrix SHA-256:
  `71ea95a7194f1e9afdc0690ecdb30037b2a309a03049d26d832b9b21789b43eb`
- Frozen formal protocol SHA-256:
  `9a8c5763d2ca007be924326812e9fd19c3125b8cfa968cdd734e01e7980f462c`
- Cloud evidence package SHA-256:
  `31a4c1c6923c793a501915260fa66eb5f8179dab8e728fc003d99b41687571c0`

The downloaded package matched the recorded package hash. The archive was
checked before extraction and contained no absolute path, parent traversal,
or symbolic/hard link. All 16 files covered by the recursive `SHA256SUMS`
passed locally, and all three reports passed the repository's strict
`--require-radeon` validator.
