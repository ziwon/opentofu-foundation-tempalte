"""Check project selection and trusted workflow controls for native roots."""

import json
from pathlib import Path
import re
import tempfile
import unittest

from tools import atlantis


class AtlantisProjectsTests(unittest.TestCase):
    def test_default_projects_exclude_bootstrap_and_local_state(self):
        document = atlantis.configuration(atlantis.ROOT)
        projects = document["projects"]
        self.assertTrue(projects)
        self.assertEqual(len({project["dir"] for project in projects}), len(projects))
        for project in projects:
            self.assertNotIn("/bootstrap/", project["dir"])
            self.assertNotIn("/local/", project["dir"])
            self.assertTrue((atlantis.ROOT / project["dir"] / "backend.tf").is_file())
            self.assertEqual(project["terraform_distribution"], "opentofu")
            self.assertEqual(project["workspace"], "default")
            self.assertFalse(project["autoplan"]["enabled"])
            patterns = project["autoplan"]["when_modified"]
            self.assertIn("*.tf", patterns)
            self.assertIn(".terraform.lock.hcl", patterns)
            self.assertTrue(any("modules/context/" in pattern for pattern in patterns))
            module = "/".join(project["name"].split("/")[1:])
            self.assertTrue(any(f"modules/{module}/" in pattern for pattern in patterns))
        self.assertFalse(document["automerge"])
        self.assertFalse(document["parallel_apply"])
        self.assertEqual(document["autodiscover"]["mode"], "disabled")

    def test_explicit_local_selection_and_invalid_selections(self):
        document = atlantis.configuration(atlantis.ROOT, ["dev/local/foundation/catalog"], True)
        project, = document["projects"]
        self.assertTrue(project["autoplan"]["enabled"])
        self.assertEqual(project["dir"], "live/dev/local/foundation/catalog")
        for name in ("dev/aws/bootstrap/state", "../../etc", "missing/aws/network/core"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                atlantis.configuration(atlantis.ROOT, [name])

    def test_checked_in_projects_are_current_and_check_does_not_overwrite(self):
        document = atlantis.configuration(atlantis.ROOT)
        self.assertEqual(json.loads((atlantis.ROOT / atlantis.EXAMPLE).read_text()), document)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "atlantis.yaml"
            output.write_text("stale\n")
            with self.assertRaisesRegex(ValueError, "stale"):
                atlantis.write_configuration(document, output, check=True)
            self.assertEqual(output.read_text(), "stale\n")

    def test_trusted_workflow_gates_the_native_saved_plan(self):
        repos = (atlantis.ROOT / "integrations/atlantis/repos.yaml.example").read_text()
        plan, apply = repos.split("    plan:\n", 1)[1].split("    apply:\n", 1)
        for stage in (plan, apply):
            self.assertIn('run: test -z "$COMMENT_ARGS"', stage)
            self.assertIn('tools/quality.py source .', stage)
            self.assertIn('tools/quality.py plan . "$PLANFILE"', stage)
        self.assertLess(plan.index("- init"), plan.index("tools/quality.py source"))
        self.assertLess(plan.index("tools/quality.py source"), plan.index("- plan\n"))
        self.assertLess(plan.index("- plan\n"), plan.index("tools/quality.py plan"))
        self.assertLess(apply.index("tools/quality.py plan"), apply.index("- apply\n"))
        for requirement in ("apply_requirements: [approved, mergeable, undiverged]", "allow_custom_workflows: false", "allowed_overrides: []"):
            self.assertIn(requirement, repos)
        server = (atlantis.ROOT / "integrations/atlantis/server.yaml.example").read_text()
        self.assertIn("allow-fork-prs: false", server)
        self.assertIn("default-tf-distribution: opentofu", server)
        self.assertIn("disable-apply-all: true", server)

    def test_policy_that_atlantis_executes_requires_code_owner_review(self):
        repos = (atlantis.ROOT / "integrations/atlantis/repos.yaml.example").read_text()
        executed = set(re.findall(r"run: python3 (?:\.\./){5}(\S+)", repos))
        self.assertIn("tools/quality.py", executed)
        policy = executed | {"tools/", "mise.toml", ".tflint.hcl", "atlantis.yaml",
                             "integrations/atlantis/mise.toml",
                             ".github/CODEOWNERS", ".github/workflows/check.yml"}
        text = (atlantis.ROOT / ".github/CODEOWNERS").read_text()
        rules = [line.split() for line in text.splitlines() if line.strip() and not line.startswith("#")]
        for pattern, *_ in rules:
            self.assertTrue(pattern.startswith("/") and not set("*?[") & set(pattern),
                            f"Use anchored CODEOWNERS paths without globs: {pattern}")
        for path in sorted(policy):
            matches = [owners for pattern, *owners in rules
                       if (path.startswith(pattern[1:]) if pattern.endswith("/") else path == pattern[1:])]
            with self.subTest(path=path):
                self.assertTrue(matches and matches[-1], "Atlantis policy must have a code owner")


if __name__ == "__main__":
    unittest.main()
