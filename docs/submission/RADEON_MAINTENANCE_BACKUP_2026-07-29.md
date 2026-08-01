# Radeon Cloud maintenance backup

The organizer will publish and maintain the Radeon platform on
**2026-07-31 at 18:00 (UTC+8)**. Important data must not exist in only one
place before that window.

## Mount-name check

The announcement names `/workspace/persistence`. The current GuardianSim
instance exposes `/workspace/persistent` and stores the repository at:

```text
/workspace/persistent/GuardianSim
```

Do not create a new similarly named directory without checking the actual
mount. The backup tool detects both spellings and uses the first directory
that really exists.

## Required copies

GuardianSim uses three independent copies:

1. GitHub branch and immutable contest tag for committed source and preserved
   evidence.
2. Radeon NFS persistence for the live repository and a restorable maintenance
   archive.
3. A local Mac copy of raw Radeon output and its SHA-256 checksum.

The 2026-07-29 raw Radeon P0 archive is preserved at:

```text
Cloud:
  /workspace/persistent/guardiansim-p0-radeon-2026-07-29.tar.gz
  /workspace/persistent/guardiansim-p0-radeon-2026-07-29.tar.gz.sha256

Local:
  /Users/aolos/Downloads/GuardianSim-backups/2026-07-29/
```

Verified SHA-256:

```text
35c1110711c96a7271fe723ffd2dd8160e179e63cd46864df4e5198f518fa46d
```

The archive contains the raw Radeon scale, Parallel Futures, Safety Critic,
and session-environment outputs. The Safety Critic report remains a negative
result (`showcase_ready=false`); backing it up does not turn it into a
submission claim.

## One-command workspace backup

From the repository root on Radeon Cloud:

```bash
python3 scripts/backup_radeon_workspace.py \
  --include-file /workspace/guardiansim-p0-radeon-2026-07-29.tar.gz \
  --include-file /workspace/guardiansim-p0-radeon-2026-07-29.tar.gz.sha256
```

The command creates a timestamped directory under:

```text
/workspace/persistent/GuardianSim-backups/
```

Each backup contains:

- `GuardianSim.bundle`: all committed Git history and refs;
- `GuardianSim-working-tree.tar.gz`: tracked and untracked workspace files;
- raw external artifacts passed with `--include-file`;
- Git status, environment metadata, restore instructions, and `SHA256SUMS`.

It deliberately excludes `.env*`, private keys, credential files, Python and
Node caches, virtual environments, Playwright scratch data, and Git internals
from the working-tree archive. Git history is preserved separately in the
bundle.

## Verification and restore

```bash
cd /workspace/persistent/GuardianSim-backups/<timestamp>-<commit>
sha256sum -c SHA256SUMS
git bundle verify GuardianSim.bundle
tar -tzf GuardianSim-working-tree.tar.gz >/dev/null
```

Restore committed history:

```bash
git clone GuardianSim.bundle GuardianSim
```

Restore the exact working tree into a separate directory:

```bash
mkdir restored-worktree
tar -xzf GuardianSim-working-tree.tar.gz -C restored-worktree
```

Never restore over the only surviving copy.
