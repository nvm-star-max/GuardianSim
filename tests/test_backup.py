import hashlib
import json
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from guardian_sim.backup import create_backup


class RadeonBackupTests(unittest.TestCase):
    def test_backup_preserves_repo_and_excludes_secrets_and_caches(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            repo = root / "repo"
            persistence = root / "persistent"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "backup-test"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
            (repo / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)

            (repo / "outputs").mkdir()
            (repo / "outputs" / "report.json").write_text('{"ok": true}\n', encoding="utf-8")
            (repo / ".env.local").write_text("SECRET=do-not-copy\n", encoding="utf-8")
            (repo / "__pycache__").mkdir()
            (repo / "__pycache__" / "cache.pyc").write_bytes(b"cache")
            extra = root / "raw-report.json"
            extra.write_text('{"source": "cloud"}\n', encoding="utf-8")

            result = create_backup(
                repo,
                persistence_root=persistence,
                include_files=(extra,),
                timestamp="20260729T120000Z",
            )

            backup_dir = Path(result.backup_dir)
            self.assertTrue(Path(result.bundle).is_file())
            self.assertTrue(Path(result.manifest).is_file())
            self.assertTrue((backup_dir / "external-artifacts/raw-report.json").is_file())

            with tarfile.open(result.working_tree_archive, "r:gz") as archive:
                names = set(archive.getnames())
            self.assertIn("repo/tracked.txt", names)
            self.assertIn("repo/outputs/report.json", names)
            self.assertNotIn("repo/.env.local", names)
            self.assertFalse(any("__pycache__" in name for name in names))

            metadata = json.loads(Path(result.metadata).read_text(encoding="utf-8"))
            self.assertEqual(metadata["git_branch"], "backup-test")
            self.assertEqual(metadata["copied_external_artifacts"], ["external-artifacts/raw-report.json"])

            for line in Path(result.manifest).read_text(encoding="utf-8").splitlines():
                expected, relative = line.split("  ", maxsplit=1)
                payload = (backup_dir / relative).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), expected)

    def test_rejects_non_git_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with self.assertRaisesRegex(ValueError, "Not a Git working tree"):
                create_backup(root, persistence_root=root / "persistent")
