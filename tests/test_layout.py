"""New deployments and resources do not need a historical state migration."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import atlantis

ROOT = Path(__file__).resolve().parents[1]


def copy_local_template(root):
    for name in ("live/dev/local", "stacks/local", "modules/context"):
        shutil.copytree(ROOT / name, root / name,
                        ignore=shutil.ignore_patterns(".terraform", "*.md", "*.tfplan"))
    shutil.copyfile(ROOT / "mise.toml", root / "mise.toml")
    shutil.copytree(ROOT / "tools", root / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    inventory = root / "tools/legacy-addresses.json"
    local = {key: value for key, value in json.loads(inventory.read_text()).items() if key.startswith("local/")}
    inventory.write_text(json.dumps(local))
    (root / atlantis.EXAMPLE).parent.mkdir(parents=True)
    atlantis.write_configuration(atlantis.configuration(root), root / atlantis.EXAMPLE)


class LayoutExtensionTests(unittest.TestCase):
    def test_new_resource_without_historical_moves_preserves_state_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_local_template(root)
            module = root / "stacks/local/foundation/catalog/main.tf"
            module.write_text(module.read_text() + '\nresource "terraform_data" "new_metadata" {}\n')
            directory = root / "live/dev/local/foundation/catalog"
            command = [sys.executable, str(root / "tools/check_layout.py")]
            accepted = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            backend = directory / "backend.tf"
            backend.write_text(backend.read_text().replace("dev/local/", "prod/local/"))
            rejected = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("State identity differs", rejected.stderr)

    def test_malformed_backend_reports_error_naming_root(self):
        backends = {
            "no backend block": "terraform {}\n",
            "unsupported kind": 'terraform {\n  backend "consul" {}\n}\n',
            "missing identity": 'terraform {\n  backend "local" {}\n}\n',
        }
        for case, content in backends.items():
            with self.subTest(case), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                copy_local_template(root)
                (root / "live/dev/local/foundation/catalog/backend.tf").write_text(content)
                atlantis.write_configuration(atlantis.configuration(root), root / atlantis.EXAMPLE)
                result = subprocess.run([sys.executable, str(root / "tools/check_layout.py")],
                                        cwd=root, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("Traceback", result.stderr)
                self.assertTrue(result.stderr.startswith("error:"), result.stderr)
                self.assertIn("dev/local/foundation/catalog", result.stderr)


def check_layout(root):
    return subprocess.run([sys.executable, str(root / "tools/check_layout.py")],
                          cwd=root, capture_output=True, text=True)


class AddressContinuityTests(unittest.TestCase):
    """Every address from the shared-root layout must reach a current resource through moved blocks."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        copy_local_template(self.root)
        self.module = self.root / "stacks/local/foundation/catalog"
        self.live = self.root / "live/dev/local/foundation/catalog"

    def assertRejected(self, *fragments):
        result = check_layout(self.root)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(result.stderr.startswith("error:"), result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_current_repository_preserves_legacy_addresses(self):
        result = check_layout(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_move_names_the_legacy_address(self):
        (self.live / "migrations.tf").unlink()
        self.assertRejected("terraform_data.catalog", "dev/local/foundation/catalog")

    def test_move_to_missing_resource_is_rejected(self):
        migrations = self.live / "migrations.tf"
        migrations.write_text(migrations.read_text() + (
            "\nmoved {\n  from = terraform_data.retired\n  to   = module.stack.terraform_data.retired\n}\n"))
        self.assertRejected("module.stack.terraform_data.retired", "dev/local/foundation/catalog")

    def test_unmodelled_constructs_are_rejected(self):
        constructs = {
            "count on a resource": (self.module / "main.tf",
                                    'resource "terraform_data" "replicas" {\n  count = 2\n}\n', "count"),
            "for_each on a module": (self.live / "main.tf",
                                     'module "copies" {\n  for_each = toset(["a"])\n'
                                     '  source   = "../../../../../modules/context"\n}\n', "for_each"),
            "registry module": (self.module / "main.tf",
                                'module "vpc" {\n  source = "terraform-aws-modules/vpc/aws"\n}\n',
                                "terraform-aws-modules/vpc/aws"),
        }
        for case, (path, block, fragment) in constructs.items():
            with self.subTest(case):
                original = path.read_text()
                path.write_text(original + "\n" + block)
                self.assertRejected(fragment, "dev/local/foundation/catalog")
                path.write_text(original)

    def test_nested_module_move_chains_from_legacy_address(self):
        entry = self.module / "entry"
        entry.mkdir()
        (entry / "main.tf").write_text(
            'resource "terraform_data" "catalog" {\n  input = var.input\n}\n\nvariable "input" {}\n')
        (self.module / "main.tf").write_text(
            'module "entry" {\n  source = "./entry"\n  input = {\n    name        = var.context.id\n'
            '    tags        = merge(var.context.tags, {})\n    description = var.description\n  }\n}\n')
        self.assertRejected("terraform_data.catalog", "module.stack.terraform_data.catalog")
        (self.module / "migrations.tf").write_text(
            "moved {\n  from = terraform_data.catalog\n  to   = module.entry.terraform_data.catalog\n}\n")
        result = check_layout(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_renamed_stack_cannot_skip_legacy_addresses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_local_template(root)
            for base in ("stacks/local/foundation", "live/dev/local/foundation"):
                (root / base / "catalog").rename(root / base / "register")
            directory = root / "live/dev/local/foundation/register"
            (directory / "migrations.tf").unlink()
            for name in ("main.tf", "backend.tf"):
                path = directory / name
                path.write_text(path.read_text().replace("/catalog", "/register"))
            atlantis.write_configuration(atlantis.configuration(root), root / atlantis.EXAMPLE)
            result = subprocess.run([sys.executable, str(root / "tools/check_layout.py")],
                                    cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("local/foundation/catalog", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_root_without_json_inputs_is_not_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_local_template(root)
            directory = root / "live/dev/local/foundation/catalog"
            variables = directory / "terraform.tfvars.json"
            (directory / "terraform.tfvars").write_text('namespace = "starter"\n')
            variables.unlink()
            (directory / "migrations.tf").unlink()
            result = subprocess.run([sys.executable, str(root / "tools/check_layout.py")],
                                    cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dev/local/foundation/catalog", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
