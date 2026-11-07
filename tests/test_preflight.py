"""The preflight compares the active cloud CLI identity with a root's inputs and changes nothing."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
AWS = "dev/aws/network/core"
AZURE = "dev/azure/network/core"
GCP = "dev/gcp/network/core"
CONFIGURED = {
    "00000000-0000-0000-0000-000000000000": "11111111-1111-1111-1111-111111111111",
    "000000000000": "111111111111",
    "REPLACE_ME_SUBSCRIPTION_ID": "11111111-1111-1111-1111-111111111111",
    "example-project": "demo-project-1",
}
FAKE_CLI = '''#!{python}
import sys
responses = {responses!r}
for word, (output, code) in responses.items():
    if word in sys.argv[1:]:
        sys.stdout.write(output)
        sys.exit(code)
sys.exit(99)
'''


def aws(account="111111111111", region="us-east-1", code=0):
    identity = json.dumps({"UserId": "AIDAEXAMPLE", "Account": account,
                           "Arn": f"arn:aws:iam::{account}:user/operator"})
    return {"aws": {"get-caller-identity": (identity, code), "configure": (region + "\n", 0)}}


def az(subscription="11111111-1111-1111-1111-111111111111", code=0):
    account = json.dumps({"id": subscription, "tenantId": "22222222-2222-2222-2222-222222222222",
                          "user": {"name": "operator@example.com", "type": "user"}})
    return {"az": {"show": (account, code)}}


def gcloud(project="demo-project-1", accounts=("operator@example.com",)):
    listing = json.dumps([{"account": account, "status": "ACTIVE"} for account in accounts])
    return {"gcloud": {"get-value": (project + "\n", 0), "list": (listing, 0)}}


class PreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.repository = self.temporary / "repository"
        shutil.copytree(ROOT / "tools", self.repository / "tools", ignore=shutil.ignore_patterns("__pycache__"))
        for deployment in (AWS, AZURE, GCP):
            source, target = ROOT / "live" / deployment, self.repository / "live" / deployment
            target.mkdir(parents=True)
            for name in ("terraform.tfvars.json", "backend.tf"):
                text = (source / name).read_text()
                for placeholder, value in CONFIGURED.items():
                    text = text.replace(placeholder, value)
                (target / name).write_text(re.sub(r"REPLACE_ME_\w+", "configuredstate", text))

    def preflight(self, deployment, clis=None, repository=None):
        directory = self.temporary / "bin"
        shutil.rmtree(directory, ignore_errors=True)
        directory.mkdir()
        for name, responses in (clis or {}).items():
            fake = directory / name
            fake.write_text(FAKE_CLI.format(python=sys.executable, responses=responses))
            fake.chmod(0o755)
        repository = repository or self.repository
        result = subprocess.run([sys.executable, str(repository / "tools/preflight.py"), deployment],
                                capture_output=True, text=True,
                                env={"PATH": str(directory), "HOME": str(self.temporary)})
        self.assertNotIn("Traceback", result.stderr)
        return result

    def assertFails(self, result, *fragments):
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for fragment in fragments:
            self.assertIn(fragment, result.stderr)

    def test_matching_identity_passes(self):
        for deployment, clis in ((AWS, aws()), (AZURE, az()), (GCP, gcloud())):
            with self.subTest(deployment):
                result = self.preflight(deployment, clis)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(deployment, result.stdout)

    def test_wrong_identity_names_expected_and_actual_values(self):
        cases = {
            "aws account": (AWS, aws(account="222222222222"), "111111111111", "222222222222"),
            "aws region": (AWS, aws(region="eu-west-1"), "us-east-1", "eu-west-1"),
            "azure subscription": (AZURE, az(subscription="33333333-3333-3333-3333-333333333333"),
                                   "11111111-1111-1111-1111-111111111111", "33333333-3333-3333-3333-333333333333"),
            "gcp project": (GCP, gcloud(project="other-project"), "demo-project-1", "other-project"),
        }
        for case, (deployment, clis, expected, actual) in cases.items():
            with self.subTest(case):
                self.assertFails(self.preflight(deployment, clis), deployment, expected, actual)

    def test_every_mismatch_gets_its_own_line(self):
        result = self.preflight(AWS, aws(account="222222222222", region="eu-west-1"))
        self.assertFails(result)
        self.assertEqual(len(result.stderr.strip().splitlines()), 2, result.stderr)

    def test_committed_placeholders_fail_even_when_the_identity_reports_them(self):
        clis = {**aws(account="000000000000"), **az(subscription="00000000-0000-0000-0000-000000000000"),
                **gcloud(project="example-project")}
        for deployment in (AWS, AZURE, GCP, "dev/aws/bootstrap/state"):
            with self.subTest(deployment):
                self.assertFails(self.preflight(deployment, clis, repository=ROOT), deployment, "not configured")

    def test_placeholder_state_storage_fails(self):
        backend = self.repository / "live" / AWS / "backend.tf"
        backend.write_text(backend.read_text().replace("configuredstate", "REPLACE_ME_STATE_BUCKET"))
        self.assertFails(self.preflight(AWS, aws()), "not configured", "REPLACE_ME_STATE_BUCKET")

    def test_missing_cli_fails(self):
        for deployment, cli in ((AWS, "aws"), (AZURE, "az"), (GCP, "gcloud")):
            with self.subTest(deployment):
                self.assertFails(self.preflight(deployment), cli)

    def test_missing_login_fails(self):
        for deployment, clis in ((AWS, aws(code=255)), (AZURE, az(code=1)), (GCP, gcloud(accounts=()))):
            with self.subTest(deployment):
                result = self.preflight(deployment, clis)
                self.assertFails(result, deployment)
                self.assertIn("log", result.stderr.lower())

    def test_local_roots_pass_without_any_cli(self):
        result = self.preflight("dev/local/foundation/catalog", repository=ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("nothing to check", result.stdout)

    def test_unknown_root_fails(self):
        self.assertFails(self.preflight("dev/aws/network/missing", aws()), "dev/aws/network/missing")


if __name__ == "__main__":
    unittest.main()
