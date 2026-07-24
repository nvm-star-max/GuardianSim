# Ten-Credit Radeon Cloud Budget

One credit is charged per GPU per hour. Billing granularity is not documented, so
every launch is budgeted conservatively as at least one full credit.

## Rule

Do all coding, unit tests, report writing, plotting, and video editing locally.
Radeon Cloud is reserved for ROCm verification, Genesis GPU simulation, model
training, GPU benchmarks, and final evidence recording.

## Planned sessions

| Session | Maximum | Purpose | Exit evidence |
| --- | ---: | --- | --- |
| A | 1 credit | Environment verification and one Genesis render | GPU report, frame, dependency lock |
| B | 2 credits | Baseline task and simulator adapter | Baseline video and 20-episode result |
| C | 2 credits | Randomized rollout generation and RiskNet training | Dataset manifest and checkpoint |
| D | 2 credits | Baseline vs GuardianSim benchmark | 100+ episode JSON/CSV and plots |
| E | 1 credit | Final clean reproduction and demo recording | 3–5 minute raw demo and logs |
| Reserve | 2 credits | Failures, reruns, or final evaluator reproduction | Used only when necessary |

## Before any launch

- Source code is committed and available to the cloud workspace.
- The exact command and expected output are written down.
- Downloads are complete or cached on Persistent PVC.
- A timer is ready.
- The platform page is open so the instance can be destroyed immediately.

## During every session

1. Run `scripts/start_gpu_session.sh`.
2. Run only the commands planned for that session.
3. Save results under `outputs/`, `datasets/`, or the configured checkpoint directory.
4. Run `scripts/end_gpu_session.sh`.
5. Push code and copy critical evidence off the instance.
6. Destroy the instance in Radeon Cloud Profile.

## Stop conditions

Stop and destroy the instance when:

- setup is blocked for more than 10 minutes;
- a download fails twice;
- GPU/ROCm verification fails;
- the experiment command is not ready;
- the planned session time is reached.
