"""Deployment boundaries and saved-plan behavior, independent of any cloud."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.infra import ROOT, Deployment, Runner, UserError, command_lock, engine_environment, inventory, scaffold
from tools.infra import main
from tools.quality import QualityError


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="infra tests ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "modules", self.root / "modules")
        shutil.copytree(ROOT / "stacks/local", self.root / "stacks/local")
        for environment in ("dev", "prod"):
            shutil.copytree(ROOT / f"live/{environment}/local", self.root / f"live/{environment}/local")
        self.dev = Deployment(self.root, "dev/local/foundation/catalog")
        self.prod = Deployment(self.root, "prod/local/foundation/catalog")

    def receipt(self):
        runner = Runner(self.dev, "tofu")
        runner.initialized.write_text(json.dumps(runner.backend_identity()))
        runner.plan.write_bytes(b"reviewed-plan")
        runner.receipt.write_text(json.dumps({
            "deployment": self.dev.name, "engine": "tofu", "version": "1.12.5",
            "fingerprint": self.dev.fingerprint(),
            "plan_sha256": hashlib.sha256(runner.plan.read_bytes()).hexdigest(),
        }))
        return runner

    def test_environments_share_code_but_never_state_or_working_data(self):
        self.assertEqual(self.dev.stack, self.prod.stack)
        self.assertNotEqual(self.dev.backend()["path"], self.prod.backend()["path"])
        self.assertNotEqual(Runner(self.dev, "tofu").work, Runner(self.prod, "tofu").work)
        self.assertNotEqual(Runner(self.dev, "tofu").work, Runner(self.dev, "terraform").work)

    def test_rejects_traversal_and_ambiguous_targets(self):
        for value in ("../aws/network/core", "dev/aws/network/../../x", "/dev/aws/network/core", "prod", "dev/AWS/network/core"):
            with self.subTest(value=value), self.assertRaises(UserError):
                Deployment(self.root, value)

    def test_rejects_symlinked_input_files(self):
        self.dev.variables.unlink()
        self.dev.variables.symlink_to(ROOT / "live/dev/local/foundation/catalog/terraform.tfvars.json")
        with self.assertRaises(UserError):
            self.dev.validate()

    def test_environment_in_data_must_match_target(self):
        values = json.loads(self.dev.variables.read_text())
        values["environment"] = "prod"
        self.dev.variables.write_text(json.dumps(values))
        with self.assertRaises(UserError):
            self.dev.validate()

    def test_backend_cannot_override_derived_state_path(self):
        (self.dev.live / "backend.json").write_text('{"path":"shared.tfstate"}')
        with self.assertRaises(UserError):
            self.dev.validate()

    def test_new_environment_reuses_stack_and_preserves_original(self):
        before = self.dev.variables.read_bytes()
        scaffold(self.root, "stage/local/foundation/catalog", self.dev.name)
        created = Deployment(self.root, "stage/local/foundation/catalog")
        self.assertEqual(created.stack, self.dev.stack)
        self.assertEqual(json.loads(created.variables.read_text())["environment"], "stage")
        self.assertEqual(self.dev.variables.read_bytes(), before)
        self.assertEqual(len(inventory(self.root)), 3)
        with self.assertRaises(UserError):
            scaffold(self.root, created.name, self.dev.name)
        self.assertEqual(self.dev.variables.read_bytes(), before)

    def test_new_stack_has_separate_code_and_state(self):
        scaffold(self.root, "dev/local/foundation/second", self.dev.name)
        created = Deployment(self.root, "dev/local/foundation/second")
        self.assertNotEqual(created.stack, self.dev.stack)
        self.assertNotEqual(created.backend(), self.dev.backend())
        self.assertEqual(json.loads(created.variables.read_text())["name"], "second")

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_saved_plan_rejects_changed_input_and_modified_binary(self, _version):
        runner = self.receipt()
        runner.verify_plan()
        original = self.dev.variables.read_bytes()
        self.dev.variables.write_text(original.decode().replace("starter", "changed"))
        with self.assertRaises(UserError):
            runner.verify_plan()
        self.dev.variables.write_bytes(original)
        runner.plan.write_bytes(b"different-plan")
        with self.assertRaises(UserError):
            runner.verify_plan()

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_saved_plan_rejects_changed_shared_module(self, _version):
        runner = self.receipt()
        with (self.root / "modules/context/main.tf").open("a") as stream:
            stream.write('\noutput "new_output" { value = "new" }\n')
        with self.assertRaises(UserError):
            runner.verify_plan()

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_plan_cannot_be_transplanted_to_another_environment(self, _version):
        runner = self.receipt()
        other = Runner(self.prod, "tofu")
        other.initialized.write_text(json.dumps(other.backend_identity()))
        shutil.copyfile(runner.plan, other.plan)
        shutil.copyfile(runner.receipt, other.receipt)
        with self.assertRaises(UserError):
            other.verify_plan()

    def test_mutating_commands_exclude_same_deployment_only(self):
        with command_lock(self.root, self.dev.name):
            with self.assertRaises(UserError):
                with command_lock(self.root, self.dev.name):
                    self.fail("Concurrent command acquired the lock")
            with command_lock(self.root, self.prod.name):
                pass

    def test_implicit_cli_and_variable_overrides_are_rejected(self):
        for values in ({"TF_WORKSPACE":"prod"}, {"TF_CLI_ARGS_plan":"-out=elsewhere"}, {"TF_VAR_environment":"prod"}):
            with self.subTest(values=values), patch.dict(os.environ, values, clear=True):
                with self.assertRaises(UserError):
                    engine_environment(self.root / "data")

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_security_failure_removes_old_and_new_saved_plan(self, _version):
        runner = self.receipt()

        def plan(*_args, **_kwargs):
            runner.plan.write_bytes(b"new-plan")
            return type("Result", (), {"returncode": 2})()

        with patch.object(runner, "run", side_effect=plan), patch.object(runner, "security", side_effect=QualityError("rejected")):
            with self.assertRaises(QualityError):
                runner.make_plan(False)
        self.assertFalse(runner.plan.exists())
        self.assertFalse(runner.receipt.exists())

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_security_failure_blocks_apply_even_with_yes(self, _version):
        runner = self.receipt()
        with patch.object(runner, "run") as native, patch.object(runner, "security", side_effect=QualityError("rejected")):
            with self.assertRaises(QualityError):
                runner.apply(True)
            native.assert_not_called()

    @patch.object(Runner, "version", return_value="1.12.5")
    def test_policy_changes_invalidate_reviewed_plan(self, _version):
        (self.root / "mise.toml").write_text('[tools]\ntrivy = "0.76.1"\n')
        runner = self.receipt()
        (self.root / "mise.toml").write_text('[tools]\ntrivy = "0.0.0"\n')
        with self.assertRaises(UserError):
            runner.verify_plan()

    def test_bootstrap_requires_explicit_command_and_local_state(self):
        shutil.copytree(ROOT / "stacks/aws/bootstrap", self.root / "stacks/aws/bootstrap")
        shutil.copytree(ROOT / "live/dev/aws/bootstrap", self.root / "live/dev/aws/bootstrap")
        target = "dev/aws/bootstrap/state"
        with patch.object(Runner, "init") as initialize:
            self.assertEqual(main(["init", target], root=self.root), 1)
            initialize.assert_not_called()
            self.assertEqual(main(["bootstrap", "init", target], root=self.root), 0)
            initialize.assert_called_once()
        self.assertEqual(main(["bootstrap", "plan", self.dev.name], root=self.root), 1)

    def test_state_show_rejects_flags(self):
        runner = self.receipt()
        with patch.object(runner, "run") as native:
            with self.assertRaises(UserError):
                runner.state("-state=another-deployment")
            native.assert_not_called()


if __name__ == "__main__":
    unittest.main()
