"""New deployments and resources do not need a historical state migration."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import atlantis

ROOT = Path(__file__).resolve().parents[1]


class LayoutExtensionTests(unittest.TestCase):
    def test_new_resource_without_historical_moves_preserves_state_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("live/dev/local", "modules/local", "modules/context"):
                shutil.copytree(ROOT / name, root / name,
                                ignore=shutil.ignore_patterns(".terraform", "*.md", "*.tfplan"))
            shutil.copyfile(ROOT / "mise.toml", root / "mise.toml")
            (root / "tools").mkdir()
            for name in ("atlantis.py", "check_layout.py"):
                shutil.copyfile(ROOT / "tools" / name, root / "tools" / name)
            (root / atlantis.EXAMPLE).parent.mkdir(parents=True)
            atlantis.write_configuration(atlantis.configuration(root), root / atlantis.EXAMPLE)
            module = root / "modules/local/foundation/catalog/main.tf"
            module.write_text(module.read_text() + '\nresource "terraform_data" "new_metadata" {}\n')
            directory = root / "live/dev/local/foundation/catalog"
            (directory / "migrations.tf").unlink()
            command = [sys.executable, str(root / "tools/check_layout.py")]
            accepted = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            backend = directory / "backend.tf"
            backend.write_text(backend.read_text().replace("dev/local/", "prod/local/"))
            rejected = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("State identity differs", rejected.stderr)
