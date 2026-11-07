"""A successful scanner exit alone must not approve an unrecognized or unsafe plan."""

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from tools.quality import QualityError, inspect_report, reject_suppressions


class SecurityReportTests(unittest.TestCase):
    def test_accepts_recognized_checks(self):
        report = {"Results": [{"Type": "terraformplan-snapshot", "Misconfigurations": [
            {"ID": "AWS-0001", "Status": "PASS"}]}]}
        self.assertEqual(inspect_report(json.dumps(report), "terraformplan-snapshot"), 1)

    def test_rejects_missing_wrong_empty_and_malformed_reports(self):
        for report in ("not json", "{}", '{"Results":[]}', '{"Results":[{"Type":"terraform"}]}',
                       '{"Results":[{"Type":"terraformplan-snapshot"}]}',
                       '{"Results":[{"Type":"terraformplan-snapshot","Misconfigurations":[{}]}]}'):
            with self.subTest(report=report), self.assertRaises(QualityError):
                inspect_report(report, "terraformplan-snapshot")

    def test_rejects_findings_without_echoing_source_or_secrets(self):
        report = {"Results": [{"Type": "terraform", "Misconfigurations": [
            {"ID": "AWS-0001", "Status": "FAIL", "Message": "private input value"}]}]}
        with self.assertRaises(QualityError) as raised:
            inspect_report(json.dumps(report), "terraform")
        self.assertIn("AWS-0001", str(raised.exception))
        self.assertNotIn("private input value", str(raised.exception))


class SuppressionTests(unittest.TestCase):
    def test_rejects_inline_suppressions_in_source_and_saved_plans(self):
        for marker in (b"#trivy:ignore:*", b"// tfsec:ignore:aws-ec2-no-public-ingress-sgr", b"# Trivy:Ignore:AVD-AWS-0107"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                module = root / "modules/aws/network/core"
                module.mkdir(parents=True)
                (module / "main.tf").write_bytes(marker + b"\nresource \"aws_vpc\" \"this\" {}\n")
                with self.assertRaisesRegex(QualityError, "modules/aws/network/core/main.tf"):
                    reject_suppressions(root, None)
                plan = root / "fixture.tfplan"
                with zipfile.ZipFile(plan, "w") as archive:
                    archive.writestr("tfplan", b"")
                    archive.writestr("tfconfig/m-stack/main.tf", marker)
                with self.assertRaisesRegex(QualityError, "suppressions"):
                    reject_suppressions(root, plan)

    def test_accepts_clean_configuration_and_ignores_local_caches(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "main.tf").write_text('resource "aws_vpc" "this" {}\n')
            (root / ".infra/trivy-modules").mkdir(parents=True)
            (root / ".infra/trivy-modules/main.tf").write_text("#trivy:ignore:*\n")
            reject_suppressions(root, None)
            plan = root / "fixture.tfplan"
            with zipfile.ZipFile(plan, "w") as archive:
                archive.writestr("tfconfig/m-/main.tf", 'resource "aws_vpc" "this" {}\n')
            reject_suppressions(root, plan)
