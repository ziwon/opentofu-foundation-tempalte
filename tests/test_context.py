"""Contexts let recipes take <group> <stack> and show what a command will touch before it runs."""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_preflight import CONFIGURED, FAKE_CLI, aws

ROOT = Path(__file__).resolve().parents[1]
DEPLOYMENTS = ("dev/aws/network/core", "prod/aws/network/core", "dev/gcp/network/core",
               "dev/local/foundation/catalog")
AWS_DEV = "DEPLOY_ENV=dev\nDEPLOY_CLOUD=aws\nAWS_PROFILE=sandbox\nAWS_REGION=us-east-1\n"
LOCAL_DEV = "DEPLOY_ENV=dev\nDEPLOY_CLOUD=local\n"


class ContextTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.repository = self.temporary / "repository"
        shutil.copytree(ROOT / "tools", self.repository / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(ROOT / "justfile", self.repository / "justfile")
        for example in ROOT.glob(".env.*.example"):
            shutil.copy(example, self.repository / example.name)
        for deployment in DEPLOYMENTS:
            source, target = ROOT / "live" / deployment, self.repository / "live" / deployment
            target.mkdir(parents=True)
            for name in ("terraform.tfvars.json", "backend.tf"):
                text = (source / name).read_text()
                for placeholder, value in CONFIGURED.items():
                    text = text.replace(placeholder, value)
                (target / name).write_text(re.sub(r"REPLACE_ME_\w+", "configuredstate", text))
        self.bin = self.temporary / "bin"
        self.bin.mkdir()

    def context(self, name, text):
        (self.repository / f".env.{name}").write_text(text)

    def fake(self, clis):
        for name, responses in clis.items():
            fake = self.bin / name
            fake.write_text(FAKE_CLI.format(python=sys.executable, responses=responses))
            fake.chmod(0o755)

    def run_tool(self, *args, stdin="", **environment):
        result = subprocess.run([sys.executable, str(self.repository / "tools/context.py"), *args],
                                input=stdin, capture_output=True, text=True,
                                env={"PATH": str(self.bin), "HOME": str(self.temporary),
                                     "PREFLIGHT_TIMEOUT_SECONDS": "2", **environment})
        self.assertNotIn("Traceback", result.stderr)
        return result

    def assertFails(self, result, *fragments):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def rows(self, result):
        pairs = (line.split(" : ", 1) for line in result.stderr.splitlines() if " : " in line)
        return {label.strip(): value.strip() for label, value in pairs}

    def selected(self):
        link = self.repository / ".env"
        return os.readlink(link) if link.is_symlink() else None

    def test_use_selects_a_context_by_name_or_number(self):
        self.context("aws.dev", AWS_DEV)
        self.context("local.dev", LOCAL_DEV)
        result = self.run_tool("use", "local.dev")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.selected(), ".env.local.dev")
        result = self.run_tool("use", stdin="1\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1) aws.dev", result.stdout)
        self.assertIn("2) local.dev", result.stdout)
        self.assertEqual(self.selected(), ".env.aws.dev")

    def test_use_names_the_available_contexts_or_an_example_to_copy(self):
        self.assertFails(self.run_tool("use", "aws.dev"), "cp .env.aws.dev.example .env.aws.dev")
        self.context("local.dev", LOCAL_DEV)
        self.assertFails(self.run_tool("use", "aws.prod"), "aws.prod", "local.dev")
        self.assertIsNone(self.selected())

    def test_use_keeps_a_hand_written_env_file(self):
        self.context("aws.dev", AWS_DEV)
        (self.repository / ".env").write_text("AWS_PROFILE=mine\n")
        self.assertFails(self.run_tool("use", "aws.dev"), ".env")
        self.assertEqual((self.repository / ".env").read_text(), "AWS_PROFILE=mine\n")

    def test_use_rejects_an_unedited_example(self):
        shutil.copy(self.repository / ".env.aws.dev.example", self.repository / ".env.aws.dev")
        self.assertFails(self.run_tool("use", "aws.dev"), "placeholder", "AWS_PROFILE")
        self.assertIsNone(self.selected())

    def test_use_rejects_values_just_would_read_differently(self):
        for value in ("sandbox # mine", "$HOME/.aws", 'sand\\"box'):
            with self.subTest(value):
                self.context("aws.dev", AWS_DEV.replace("AWS_PROFILE=sandbox", f"AWS_PROFILE={value}"))
                self.assertFails(self.run_tool("use", "aws.dev"), "AWS_PROFILE", "plain value")
                self.assertIsNone(self.selected())

    def test_use_without_an_answer_selects_nothing(self):
        self.context("aws.dev", AWS_DEV)
        result = self.run_tool("use", stdin="")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("no context selected", result.stderr)
        self.assertIsNone(self.selected())

    def test_use_rejects_a_context_that_names_no_deployments(self):
        for text, fragment in (("DEPLOY_ENV=dev\n", "DEPLOY_CLOUD"), ("DEPLOY_ENV=qa\nDEPLOY_CLOUD=aws\n", "live/qa/aws")):
            with self.subTest(fragment):
                self.context("broken", text)
                self.assertFails(self.run_tool("use", "broken"), fragment)
                self.assertIsNone(self.selected())

    def test_short_target_resolves_through_the_selected_context(self):
        self.context("aws.dev", AWS_DEV)
        self.run_tool("use", "aws.dev")
        result = self.run_tool("root", "network", "core", AWS_PROFILE="sandbox", AWS_REGION="us-east-1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "live/dev/aws/network/core\n")
        for fragment in (".env.aws.dev", "dev", "aws", "AWS_PROFILE=sandbox", "stacks/aws/network/core",
                         "live/dev/aws/network/core/.terraform", "s3", "configuredstate",
                         "dev/aws/network/core/terraform.tfstate"):
            self.assertIn(fragment, result.stderr)

    def test_short_target_needs_a_context(self):
        self.assertFails(self.run_tool("root", "network", "core"), "just use")

    def test_a_deleted_context_stops_every_target(self):
        (self.repository / ".env").symlink_to(".env.gone")
        for target in (("network", "core"), ("dev/local/foundation/catalog",)):
            with self.subTest(target):
                self.assertFails(self.run_tool("root", *target), ".env.gone", "just use")

    def test_a_hand_written_env_file_is_not_a_context(self):
        (self.repository / ".env").write_text("AWS_PROFILE=mine\n")
        result = self.run_tool("root", "dev/local/foundation/catalog")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not a context", self.rows(result)["Env file"])
        self.assertFails(self.run_tool("root", "network", "core"), "just use")

    def test_an_env_file_above_the_repository_stops_every_target(self):
        (self.temporary / ".env").write_text("AWS_PROFILE=elsewhere\n")
        self.assertFails(self.run_tool("root", "dev/local/foundation/catalog"), str(self.temporary / ".env"))

    def test_full_target_works_without_a_context_but_must_match_a_selected_one(self):
        result = self.run_tool("root", "dev/local/foundation/catalog")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "live/dev/local/foundation/catalog\n")
        self.assertEqual(self.rows(result)["State"], ".infra/state/dev/local/foundation/catalog/terraform.tfstate")
        self.assertEqual(self.rows(result)["Env file"], "none")
        result = self.run_tool("root", "dev/gcp/network/core")
        self.assertEqual(self.rows(result)["State"], "dev/gcp/network/core/default.tfstate")
        self.context("aws.dev", AWS_DEV)
        self.run_tool("use", "aws.dev")
        self.assertFails(self.run_tool("root", "prod/aws/network/core", AWS_PROFILE="sandbox",
                                       AWS_REGION="us-east-1"), "prod/aws", ".env.aws.dev")

    def test_unknown_or_malformed_targets_fail(self):
        self.context("aws.dev", AWS_DEV)
        self.run_tool("use", "aws.dev")
        environment = {"AWS_PROFILE": "sandbox", "AWS_REGION": "us-east-1"}
        for target in (("network", "missing"), ("dev/aws/network",), ("network",), ("../../etc", "core")):
            with self.subTest(target):
                self.assertFails(self.run_tool("root", *target, **environment))

    def test_stale_shell_credentials_fail(self):
        self.context("aws.dev", AWS_DEV)
        self.run_tool("use", "aws.dev")
        self.assertFails(self.run_tool("root", "network", "core", AWS_PROFILE="production",
                                       AWS_REGION="us-east-1"), "AWS_PROFILE", "production", "sandbox", "direnv")

    def test_check_adds_the_active_identity_and_fails_on_a_mismatch(self):
        self.context("aws.dev", AWS_DEV)
        self.run_tool("use", "aws.dev")
        environment = {"AWS_PROFILE": "sandbox", "AWS_REGION": "us-east-1"}
        self.fake(aws())
        result = self.run_tool("root", "--check", "network", "core", **environment)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "live/dev/aws/network/core\n")
        self.assertIn("arn:aws:iam::111111111111:user/operator", result.stderr)
        self.fake(aws(account="222222222222"))
        self.assertFails(self.run_tool("root", "--check", "network", "core", **environment), "222222222222")

    @unittest.skipUnless(shutil.which("just"), "just is not installed")
    def test_recipes_take_group_and_stack_from_the_context(self):
        def just(*args):
            return subprocess.run(["just", *args], cwd=self.repository, capture_output=True, text=True,
                                  env={"PATH": os.environ["PATH"], "HOME": str(self.temporary)})

        result = just("init", "foundation", "catalog")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("just use", result.stderr)
        self.assertFalse((self.repository / "live/dev/local/foundation/catalog/.terraform").exists())
        self.context("local.dev", LOCAL_DEV)
        self.assertEqual(just("use", "local.dev").returncode, 0)
        result = just("preflight", "foundation", "catalog")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("live/dev/local/foundation/catalog", result.stderr)
        self.assertIn("nothing to check", result.stderr)


if __name__ == "__main__":
    unittest.main()
