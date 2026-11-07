"""The layout check accepts ordinary OpenTofu stacks and rejects roots with a broken shape."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import atlantis

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_STACK = '''module "buckets" {
  source   = "terraform-aws-modules/s3-bucket/aws"
  version  = "~> 4.0"
  for_each = toset(["logs", "assets"])

  bucket = each.key
  policy = <<-EOT
    {"Statement": []}
  EOT
}

resource "terraform_data" "replicas" {
  count = 2
  input = "%{if count.index == 0}primary%{else}replica%{endif}"
}
'''


def copy_local_template(root):
    for name in ("live/dev/local", "stacks/local", "modules/context", "modules/local"):
        shutil.copytree(ROOT / name, root / name,
                        ignore=shutil.ignore_patterns(".terraform", "*.md", "*.tfplan"))
    shutil.copyfile(ROOT / "mise.toml", root / "mise.toml")
    shutil.copytree(ROOT / "tools", root / "tools", ignore=shutil.ignore_patterns("__pycache__"))
    (root / atlantis.EXAMPLE).parent.mkdir(parents=True)
    atlantis.write_configuration(atlantis.configuration(root), root / atlantis.EXAMPLE)


def add_real_world_stack(root):
    stack = root / "stacks/local/foundation/catalog"
    (stack / "registry.tf").write_text(REGISTRY_STACK)
    (stack / "label.tofu").write_text('module "label" {\n  source = "../../../../modules/local/label"\n}\n')
    for name, source in {"label": "../part", "part": "../label"}.items():
        (root / "modules/local" / name).mkdir(parents=True)
        (root / "modules/local" / name / "main.tf").write_text(f'module "next" {{\n  source = "{source}"\n}}\n')


def check_layout(root):
    return subprocess.run([sys.executable, str(root / "tools/check_layout.py")],
                          cwd=root, capture_output=True, text=True)


class LayoutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        copy_local_template(self.root)
        self.stack = self.root / "stacks/local/foundation/catalog"
        self.live = self.root / "live/dev/local/foundation/catalog"

    def assertRejected(self, *fragments):
        result = check_layout(self.root)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertTrue(result.stderr.startswith("error:"), result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_current_repository_passes(self):
        result = check_layout(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_registry_modules_meta_arguments_heredocs_and_tofu_files_are_accepted(self):
        add_real_world_stack(self.root)
        root_main = self.live / "main.tf"
        root_main.write_text(root_main.read_text() + '\nmodule "copies" {\n  source   = "../../../../../modules/context"\n'
                             '  for_each = toset(["a"])\n}\n')
        result = check_layout(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_wrong_state_identity_is_rejected(self):
        backend = self.live / "backend.tf"
        backend.write_text(backend.read_text().replace("dev/local/", "prod/local/"))
        self.assertRejected("State identity differs", "dev/local/foundation/catalog")

    def test_malformed_backend_reports_error_naming_root(self):
        backends = {
            "no backend block": "terraform {}\n",
            "unsupported kind": 'terraform {\n  backend "consul" {}\n}\n',
            "missing identity": 'terraform {\n  backend "local" {}\n}\n',
        }
        backend = self.live / "backend.tf"
        original = backend.read_text()
        for case, content in backends.items():
            with self.subTest(case):
                backend.write_text(content)
                atlantis.write_configuration(atlantis.configuration(self.root), self.root / atlantis.EXAMPLE)
                self.assertRejected("dev/local/foundation/catalog")
        backend.write_text(original)

    def test_root_must_call_its_stack_not_mention_it(self):
        shadow = self.root / "vendor/local/foundation/shadow"
        shutil.copytree(self.stack, shadow)
        main = self.live / "main.tf"
        main.write_text(main.read_text().replace(
            "stacks/local/foundation/catalog", "vendor/local/foundation/shadow").replace(
            'module "stack" {\n', 'module "stack" {\n  # source = "../../../../../stacks/local/foundation/catalog"\n'))
        self.assertRejected("Root does not call its stack", "dev/local/foundation/catalog")

    def shadow_stack(self):
        shadow = self.root / "vendor/local/foundation/shadow"
        shutil.copytree(self.stack, shadow)
        return "../../../../../vendor/local/foundation/shadow"

    def test_override_and_json_files_cannot_redirect_the_stack(self):
        wrong = self.shadow_stack()
        for name in ("override.tf", "a_override.tf", "main_override.tofu"):
            with self.subTest(name):
                (self.live / name).write_text(f'module "stack" {{\n  source = "{wrong}"\n}}\n')
                self.assertRejected(name, "dev/local/foundation/catalog")
                (self.live / name).unlink()
        (self.live / "extra.tf.json").write_text("{}\n")
        self.assertRejected("extra.tf.json", "dev/local/foundation/catalog")

    def test_block_comments_and_nested_keys_cannot_name_the_stack(self):
        wrong = self.shadow_stack()
        main = self.live / "main.tf"
        original = main.read_text()
        expected = "../../../../../stacks/local/foundation/catalog"
        cases = {
            "block comment": original.replace(f'  source      = "{expected}"', f'  /* source = "{expected}" */\n  source      = "{wrong}"'),
            "comment after code": original.replace(f'  source      = "{expected}"', f'  description = var.description /*\n  source = "{expected}"\n  */\n  source      = "{wrong}"'),
            "nested map key": original.replace(f'  source      = "{expected}"', f'  labels = {{\n    source = "{expected}"\n  }}\n  source      = "{wrong}"'),
        }
        for case, text in cases.items():
            with self.subTest(case):
                assert text != original, case
                main.write_text(text)
                self.assertRejected("Root does not call its stack", "dev/local/foundation/catalog")
        main.write_text(original)

    def test_policy_strings_with_slash_star_do_not_hide_the_stack(self):
        main = self.live / "main.tf"
        main.write_text('locals {\n  object_arns = "arn:aws:s3:::bucket/*"\n}\n' + main.read_text()
                        + 'locals {\n  suffix = "*/logs"\n}\n')
        result = check_layout(self.root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_opentofu_decides_which_stack_a_root_calls(self):
        wrong = self.shadow_stack()
        main = self.live / "main.tf"
        original = main.read_text()
        fake = 'module "stack" {\n  source = "EXPECTED"\n}\n'.replace("EXPECTED", "../../../../../stacks/local/foundation/catalog")
        cases = {
            "tofu file shadows main.tf": {"main.tofu": 'module "stack" { source = "WRONG" }\n'},
            "escaped backslash before a comment": {"main.tf": original.replace("../../../../../stacks/local/foundation/catalog", "WRONG")
                + 'locals {\n  path = "C:\\\\" /*\n' + fake + '*/\n}\n'},
            "heredoc after the real call": {"main.tf": original.replace("../../../../../stacks/local/foundation/catalog", "WRONG")
                + 'locals {\n  doc = <<EOT\n' + fake + 'EOT\n}\n'},
            "slash star inside a hash comment": {"main.tf": "# see /* below\n" + original.replace("../../../../../stacks/local/foundation/catalog", "WRONG")
                + "# */\n" + 'locals {\n  doc = <<EOT\n' + fake + 'EOT\n}\n'},
            "one-line call before a heredoc": {"main.tf": 'module "stack" { source = "WRONG" }\n'
                + 'locals {\n  doc = <<EOT\n' + fake + 'EOT\n}\n'},
        }
        for case, files in cases.items():
            with self.subTest(case):
                for name, text in files.items():
                    (self.live / name).write_text(text.replace("WRONG", wrong))
                self.assertRejected("Root does not call its stack", "dev/local/foundation/catalog")
                main.write_text(original)
                for name in files:
                    if name != "main.tf":
                        (self.live / name).unlink()

    def test_stack_without_main_tf_is_discovered(self):
        orphan = self.root / "stacks/local/foundation/orphan"
        orphan.mkdir()
        (orphan / "resources.tf").write_text('resource "terraform_data" "orphan" {}\n')
        self.assertRejected("stacks/local/foundation/orphan")

    def test_stacks_must_not_configure_providers_in_tofu_files(self):
        (self.stack / "providers.tofu").write_text('provider "aws" {}\n')
        self.assertRejected("must not configure providers", "providers.tofu")

    def test_root_without_json_inputs_is_not_skipped(self):
        (self.live / "terraform.tfvars").write_text('namespace = "starter"\n')
        (self.live / "terraform.tfvars.json").unlink()
        self.assertRejected("dev/local/foundation/catalog")


if __name__ == "__main__":
    unittest.main()
