"""README badges state the tool versions the repository actually pins."""

from pathlib import Path
import re
import unittest
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
READMES = ("README.md", "README.ko.md")
BADGE = re.compile(r"https://img\.shields\.io/badge/([^?\"]+)")
PINS = {
    "OpenTofu": ("mise.toml", "opentofu"),
    "Trivy": ("mise.toml", "trivy"),
    "TFLint": ("mise.toml", "tflint"),
    "Gitleaks": ("mise.toml", "gitleaks"),
    "Atlantis": ("integrations/atlantis/mise.toml", "aqua:runatlantis/atlantis"),
    "Prowler": ("integrations/prowler/mise.toml", "pipx:prowler"),
    "Infracost": ("integrations/infracost/mise.toml", "aqua:infracost/infracost"),
}


def pinned(path, tool):
    match = re.search(rf'^"?{re.escape(tool)}"?\s*=\s*"([^"]+)"', (ROOT / path).read_text(), re.M)
    return match.group(1)


def badges(readme):
    return [unquote(badge).replace("--", "\0").split("-")[1].replace("\0", "-")
            for badge in BADGE.findall((ROOT / readme).read_text())]


class ReadmeBadgeTests(unittest.TestCase):
    def test_version_badges_match_pinned_tools(self):
        for readme in READMES:
            messages = badges(readme)
            for tool, (path, key) in PINS.items():
                with self.subTest(readme=readme, tool=tool):
                    self.assertIn(f"{tool} {pinned(path, key)}", messages)

    def test_both_readmes_show_the_same_badges(self):
        english, korean = (BADGE.findall((ROOT / readme).read_text()) for readme in READMES)
        self.assertEqual(english, korean)
        self.assertIn("actions/workflows/check.yml/badge.svg", (ROOT / "README.md").read_text())
        self.assertTrue((ROOT / ".github/workflows/check.yml").is_file())


if __name__ == "__main__":
    unittest.main()
