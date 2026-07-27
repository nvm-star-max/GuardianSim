# Official Repository Pull Request Draft

Do not open this pull request until the final report, video, source commit, and
Luma rules sign-off are complete.

## Title

```text
Track 3, Aegis Motion, GuardianSim
```

## Body

```markdown
## Project

**GuardianSim — Counterfactual Safety Certification for Robot Manipulation on
AMD Radeon GPUs**

Team: **Aegis Motion** (solo developer)

GuardianSim is a policy-agnostic safety layer for robot manipulation in
Genesis. It evaluates bounded counterfactual grasp actions from the same
fingerprinted physical state on an AMD Radeon GPU, applies frozen hard safety
gates, and either selects an eligible action or explicitly stops.

## Verified result

In the frozen 30-scenario Gate 3.2 Genesis benchmark:

- repeatable safe completion: **18/30 baseline → 30/30 GuardianSim**;
- independent safe executions: **58/90 → 90/90**;
- sampled clutter contacts: **30 → 0**;
- mean sampled clutter clearance: **23.191 mm → 46.003 mm**.

These are simulation results, not physical-robot deployment claims.

## AMD Radeon use

Counterfactual physical rollouts were evaluated with Genesis 1.2.3 on the
`gs.amdgpu` backend in Radeon Cloud. The preserved evaluator environment used
PyTorch `2.9.1+gitff65f5b` with HIP `7.2.53211-e1a6bc5663` and one gfx1100
Radeon GPU.

## Deliverables

- Source and reproducibility instructions:
  https://github.com/nvm-star-max/GuardianSim
- Technical report: [FINAL PUBLIC URL]
- 3–5 minute workflow demo: [FINAL VIDEO URL]
- Immutable benchmark evidence and checksums:
  https://github.com/nvm-star-max/GuardianSim/tree/[FINAL_COMMIT]/docs/evidence
- Optional container artifact: [FINAL IMAGE OR DOCUMENTED FALLBACK]

## Reproduction

The repository documents a bounded evaluator smoke that verifies source
identity, Radeon/ROCm readiness, the real Genesis scene, three alternatives
from one scene snapshot, strict report validation, and checksums. The smoke is
an execution-path proof and is not used as the performance benchmark.

## Limitations

GuardianSim currently uses Genesis simulation, sampled clearance proxies, a
bounded action space, and non-real-time planning. Harder unsupported geometry
can produce a deliberate safe stop.
```

## Release-time replacements

- Replace every `[FINAL ...]` value with a public immutable URL.
- Use the final source commit or tag in evidence links.
- Add the exact video URL only after the complete workflow is reviewable.
- Confirm public member naming against the Luma rules.
