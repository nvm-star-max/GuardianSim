# Radeon Scale V2 Capacity Preflight

This directory preserves the 2026-07-31 Radeon Cloud capacity check for the
frozen Radeon Scale V2 protocol.

## Scope

The preflight built and stepped 512, 1,024, 2,048, and 4,096 full headless
Genesis scenes. All four batch sizes passed and the 4,096-world formal target
was supported.

These short runs answer one question only: can the declared batch sizes run on
the available Radeon instance? Their timing and telemetry are not performance
evidence and are not combined with the formal report.

## Receipts

- Source commit: `3d8021a237ca0dfca41c98df1b492b7b9a523b4f`
- Preflight protocol SHA-256:
  `6fed36e1cb006f9c5b9a44ac8e677c32d9bdc70d3f19ade28420d1aa82e1b935`
- Evidence archive SHA-256:
  `3e5d1de9161ebba346c4d499d24957a1d650b80963f15ed651582e5fdfc96b1f`
- Summary: [`raw/preflight-summary.json`](raw/preflight-summary.json)
- Complete file manifest: [`raw/SHA256SUMS`](raw/SHA256SUMS)
