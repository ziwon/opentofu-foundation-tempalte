"""A successful scanner exit alone must not approve an unrecognized or unsafe plan."""

import json
import unittest

from tools.quality import QualityError, inspect_report


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
