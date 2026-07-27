# AMD AI DevMaster Hackathon Rules Review

Reviewed: 2026-07-28 (GMT+8)

This is a concise compliance review, not legal advice. The governing source is
the official Rules and Conditions linked from the Luma event page:

- Luma event: <https://luma.com/amd-4dhi?utm_source=CN>
- Rules document:
  <https://docs.google.com/document/d/1TwgwBNUAv8fRNQbkcTZmcRR0__Oi4WMsBfkW38ALZp4/edit?tab=t.0>
- Rules PDF retrieved for this review: 15 pages
- Retrieved PDF SHA-256:
  `bfbc8787f8397f95ed8e426d0279a7889b1b0a9adfaf69eadccee335671cc382`

## Submission and schedule

- Final deadline: 2026-08-06 at 23:59, Beijing/Singapore time (UTC+8).
- Entry method: fork `AMD-DEV-CONTEST/Radeon-hackathon-2026-07` and submit
  the project through a pull request.
- Entries and pull requests must be in English.
- Individuals and teams of up to three people are allowed.
- Track 3 requires a technical report, dedicated source repository, detailed
  reproducibility README, and a recommended 3–5 minute workflow video.
- A complete-source Docker image is preferred, not stated as mandatory.
- Supplementary formats may be included but are optional for Track 3.

## Track 3 technical requirements

- The solution must use Radeon Cloud, an AMD Radeon GPU, and ROCm.
- Environment execution and applicable training/inference must use a single
  Radeon GPU.
- Genesis and MuJoCo are explicitly recognized open-source simulation
  frameworks.
- Track 3 may demonstrate simulation, learning, robustness, closed-loop
  control, GPU optimization, multimodal fusion, or another supported Physical
  AI capability.
- Public and self-built evaluation data are allowed, subject to licensing,
  legal, and ethical compliance.
- Core evaluation weights are robot capability (30), Radeon/ROCm adoption
  (20), innovation (20), application value (20), and upstream open-source
  contribution (10).

## Eligibility and legal terms requiring owner awareness

- Luma approval and AMD Developer Program registration are mandatory for prize
  eligibility.
- Every participant must register using their legal name and contact details,
  provide the same team name, be at least 18 or the local age of majority, and
  have valid Discord and GitHub IDs.
- The rules contain sanctions/export-control exclusions and AMD employee and
  household exclusions. These are personal eligibility facts that the
  repository cannot verify.
- Submitting grants AMD and its designees a broad royalty-free, irrevocable,
  non-exclusive worldwide license to use and promote the entry and associated
  participant name or social handle. The rules also state that entries become
  AMD property and are not returned.
- Participation includes releases and publicity terms. Winners may need to
  provide eligibility/publicity forms and a W-8BEN or W-9 within ten days.
- Winners are responsible for taxes. China prizes are converted to CNY using
  the Bank of China exchange rate on the disbursement date, less applicable
  withholding.

The rules require the legal name in registration, but they do not require the
legal name to be displayed in the public technical report or pull request.
GuardianSim can therefore use team name **Aegis Motion** and public contributor
identity **@nvm-star-max** in public materials, provided the private Luma
registration contains the participant's legal name.

## GuardianSim compliance matrix

| Requirement | Evidence/status |
| --- | --- |
| Track 3 Physical AI application | GuardianSim is a Genesis Franka manipulation safety layer |
| Single Radeon GPU and ROCm | Preserved `gfx1100`, HIP, PyTorch, and `gs.amdgpu` evidence |
| Complete workflow | Counterfactual generation, snapshot replay, hard safety gates, selection/safe stop, report |
| Technical report | Final six-page English PDF |
| Dedicated source repository | Public `nvm-star-max/GuardianSim` repository |
| Reproducibility README | Environment, dependencies, commands, smoke, strict validation, troubleshooting |
| Docker preference | Complete-source ROCm Dockerfile present; native Radeon Cloud route is the verified path |
| 3–5 minute video | Owner-approved 4:41.5 English workflow video |
| Evaluation data disclosure | Frozen procedural 30-scenario matrix and separate breadth evidence documented |
| Open-source/core-function boundary | Core Genesis evaluator and safety algorithm are open source and local; Qwen TTS is presentation-only |
| English submission | Report, README, video, and PR draft are English |
| Code of conduct and responsible claims | No restricted content; simulation-only limitations are explicit |

## Remaining owner-only checks

Before the final pull request is opened, the owner should personally confirm:

1. the Luma registration contains the owner's legal name;
2. the registered team name is `Aegis Motion`, or the organizer accepts the
   solo registration's existing team-name value;
3. `yunlong7868` is a valid Discord ID, or a valid Discord ID is supplied to
   the organizer;
4. the owner satisfies the age, sanctions/export-control, and employment
   eligibility provisions;
5. the owner accepts the entry-license, publicity, release, prize-form, and
   tax terms summarized above.
