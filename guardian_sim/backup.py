"""Create a restorable, secret-aware GuardianSim workspace backup."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

PERSISTENCE_CANDIDATES = (
    Path("/workspace/persistence"),
    Path("/workspace/persistent"),
)

EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".playwright-cli",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
    "tmp",
    "venv",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    "id_ed25519",
    "id_rsa",
}

EXCLUDED_FILE_SUFFIXES = {
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
}


@dataclass(frozen=True)
class BackupResult:
    backup_dir: str
    bundle: str
    working_tree_archive: str
    manifest: str
    metadata: str
    excluded_entry_count: int


def resolve_persistence_root(explicit: Path | None = None) -> Path:
    """Resolve the real cloud persistence mount.

    The organizer announcement names ``/workspace/persistence`` while the
    current Radeon image exposes ``/workspace/persistent``.  Existing mounts
    win over spelling assumptions.
    """

    if explicit is not None:
        return explicit.expanduser().resolve()
    for candidate in PERSISTENCE_CANDIDATES:
        if candidate.is_dir():
            return candidate.resolve()
    expected = ", ".join(str(path) for path in PERSISTENCE_CANDIDATES)
    raise FileNotFoundError(f"No Radeon persistence mount found; checked: {expected}")


def _is_excluded(relative_path: Path) -> bool:
    if any(part in EXCLUDED_DIRECTORY_NAMES for part in relative_path.parts):
        return True
    name = relative_path.name
    lowered = name.lower()
    if name in EXCLUDED_FILE_NAMES or lowered.startswith(".env"):
        return True
    if relative_path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return True
    return lowered in {"credentials", "credentials.json", "secrets.json"}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(
    command: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _safe_remote_url(repo: Path) -> str | None:
    result = _run(["git", "remote", "get-url", "origin"], cwd=repo, check=False)
    if result.returncode != 0:
        return None
    raw = result.stdout.strip()
    if "://" not in raw:
        return raw
    parsed = urlsplit(raw)
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, parsed.query, parsed.fragment))


def _capture_environment(repo: Path) -> dict[str, str | None]:
    commands = {
        "git": ["git", "--version"],
        "python": [os.environ.get("PYTHON", "python3"), "--version"],
        "uname": ["uname", "-a"],
        "rocm_smi": ["rocm-smi", "--showproductname"],
    }
    output: dict[str, str | None] = {}
    for name, command in commands.items():
        try:
            result = _run(command, cwd=repo, check=False)
        except FileNotFoundError:
            output[name] = None
            continue
        output[name] = result.stdout.strip() or None
    return output


def _write_working_tree_archive(repo: Path, archive: Path) -> int:
    excluded = 0

    def filter_entry(info: tarfile.TarInfo) -> tarfile.TarInfo | None:
        nonlocal excluded
        relative = Path(info.name).relative_to(repo.name)
        if _is_excluded(relative):
            excluded += 1
            return None
        return info

    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as handle:
        handle.add(repo, arcname=repo.name, recursive=True, filter=filter_entry)
    return excluded


def _verify_tar(archive: Path) -> None:
    with tarfile.open(archive, "r:gz") as handle:
        for member in handle.getmembers():
            if member.name.startswith("/") or ".." in Path(member.name).parts:
                raise ValueError(f"Unsafe archive member: {member.name}")


def _write_manifest(backup_dir: Path) -> Path:
    manifest = backup_dir / "SHA256SUMS"
    lines = []
    for path in sorted(item for item in backup_dir.rglob("*") if item.is_file()):
        if path == manifest:
            continue
        lines.append(f"{_sha256(path)}  {path.relative_to(backup_dir).as_posix()}")
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return manifest


def create_backup(
    repo: Path,
    *,
    persistence_root: Path | None = None,
    include_files: tuple[Path, ...] = (),
    timestamp: str | None = None,
) -> BackupResult:
    repo = repo.expanduser().resolve()
    if not (repo / ".git").exists():
        raise ValueError(f"Not a Git working tree: {repo}")

    root = resolve_persistence_root(persistence_root)
    root.mkdir(parents=True, exist_ok=True)
    stamp = timestamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    head = _run(["git", "rev-parse", "--short=12", "HEAD"], cwd=repo).stdout.strip()
    backup_dir = root / "GuardianSim-backups" / f"{stamp}-{head}"
    backup_dir.mkdir(parents=True, exist_ok=False)

    bundle = backup_dir / "GuardianSim.bundle"
    _run(["git", "bundle", "create", str(bundle), "--all"], cwd=repo)
    _run(["git", "bundle", "verify", str(bundle)], cwd=repo)

    archive = backup_dir / "GuardianSim-working-tree.tar.gz"
    excluded_count = _write_working_tree_archive(repo, archive)
    _verify_tar(archive)

    copied_extras: list[str] = []
    extras_dir = backup_dir / "external-artifacts"
    for source in include_files:
        source = source.expanduser().resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        extras_dir.mkdir(exist_ok=True)
        target = extras_dir / source.name
        shutil.copy2(source, target)
        copied_extras.append(target.relative_to(backup_dir).as_posix())

    status = _run(["git", "status", "--short"], cwd=repo).stdout
    (backup_dir / "git-status.txt").write_text(status, encoding="utf-8")

    metadata_path = backup_dir / "backup-metadata.json"
    metadata = {
        "schema_version": 1,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "source_repo": str(repo),
        "persistence_root": str(root),
        "git_head": _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip(),
        "git_branch": _run(["git", "branch", "--show-current"], cwd=repo).stdout.strip(),
        "git_origin": _safe_remote_url(repo),
        "environment": _capture_environment(repo),
        "excluded_entry_count": excluded_count,
        "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
        "excluded_file_suffixes": sorted(EXCLUDED_FILE_SUFFIXES),
        "copied_external_artifacts": copied_extras,
        "restore": {
            "committed_history": "git clone GuardianSim.bundle GuardianSim",
            "working_tree": "tar -xzf GuardianSim-working-tree.tar.gz",
        },
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    readme = backup_dir / "README.md"
    readme.write_text(
        "# GuardianSim Radeon maintenance backup\n\n"
        f"- Source commit: `{metadata['git_head']}`\n"
        f"- Source branch: `{metadata['git_branch']}`\n"
        f"- Persistence root: `{root}`\n"
        "- `GuardianSim.bundle` preserves committed Git history and refs.\n"
        "- `GuardianSim-working-tree.tar.gz` preserves tracked and untracked workspace files.\n"
        "- Caches, private keys, credential files, and `.env*` files are deliberately excluded.\n"
        "- Verify this directory with `sha256sum -c SHA256SUMS` before restoring.\n",
        encoding="utf-8",
    )

    manifest = _write_manifest(backup_dir)
    return BackupResult(
        backup_dir=str(backup_dir),
        bundle=str(bundle),
        working_tree_archive=str(archive),
        manifest=str(manifest),
        metadata=str(metadata_path),
        excluded_entry_count=excluded_count,
    )


def result_as_json(result: BackupResult) -> str:
    return json.dumps(asdict(result), indent=2)
