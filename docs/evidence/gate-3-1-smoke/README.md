# Gate 3.1 cloud smoke evidence

This directory preserves the first two episodes of the frozen Gate 3.1
adversarial benchmark. It is a technical smoke prefix, not the formal
30-episode result, and must not be presented as a statistically meaningful
performance claim.

- Instance: `u-13907-735d71cb`
- Commit used for execution: `e5ce9b84f36070b4197592795cfd9c02d2974d50`
- Validator fix used to verify persisted JSON: `e68753a`
- Completed scenarios: `2/30`, seeds `301–302`
- Protocol SHA-256:
  `472bb6ea13984dff02124c091ac8d94c67154bbe68858bb782aed8014d2afbba`
- Report SHA-256:
  `6f13148289384ff89988befded0af7bc5473d8755f0bc4cbb2723b2f7c639ec9`
- Log SHA-256:
  `b599e571efb9d3b92a4c0d7153cb08e67f1a686a7bde67d837d7bf95173f1565`

The partial validator accepted both episodes after the JSON tuple/list
canonicalization fix. Baseline and GuardianSim both completed the ordinary
task in both episodes. Baseline met the safety margin in `1/2`; GuardianSim met
it in `2/2`. The second baseline execution was classified as a clearance
violation without physical clutter contact.

Raw files:

- [`report.json`](report.json)
- [`report.log`](report.log)

