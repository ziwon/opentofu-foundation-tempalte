"""Run pinned quality tools; keep raw security reports in memory only."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile


class QualityError(Exception):
    """A failed or incomplete quality check."""


# Trivy drops suppressed findings from its report, so they must be rejected before scanning.
SUPPRESSION = re.compile(rb"(?i)(?:trivy|tfsec):ignore")
CONFIGURATION = (".tf", ".tf.json")


def execute(arguments, root: Path, *, env=None, capture=False):
    try:
        result = subprocess.run(arguments, cwd=root, env=env, text=True,
                                capture_output=capture, check=False)
    except FileNotFoundError as error:
        raise QualityError(f"{arguments[0]} is not installed; run mise install") from error
    if result.returncode:
        # Do not echo raw scanner output: it may contain configuration secrets.
        raise QualityError(f"{arguments[0]} failed (exit {result.returncode}); no successful check recorded")
    return result


def require_version(tool: str, root: Path, env: dict):
    match = re.search(rf'^{tool}\s*=\s*"([0-9.]+)"', (root / "mise.toml").read_text(), re.MULTILINE)
    if not match:
        raise QualityError(f"Pin {tool} in mise.toml before running quality checks")
    expected = match.group(1)
    output = execute([tool, "--version"], root, env=env, capture=True).stdout
    if not re.search(rf"(?<![0-9.]){re.escape(expected)}(?![0-9.])", output.splitlines()[0] if output else ""):
        raise QualityError(f"Expected {tool} {expected}; run mise install and use mise exec")
    return expected


def lint(root: Path, stack: Path, variables: Path, cloud: str):
    env = {**os.environ, "TFLINT_PLUGIN_DIR": str(root / ".infra/tflint-plugins")}
    require_version("tflint", root, env)
    arguments = ["tflint", f"--chdir={stack}", f"--config={root / '.tflint.hcl'}", "--no-color"]
    plugin = {"aws": "aws", "azure": "azurerm", "gcp": "google"}.get(cloud)
    if plugin:
        arguments.append(f"--enable-plugin={plugin}")
    execute([*arguments, "--init"], root, env=env)
    execute([*arguments, f"--var-file={variables}"], root, env=env)
    print(f"Lint passed: {variables.parent.relative_to(root / 'live')}", flush=True)


def inspect_report(report: str, expected_type: str) -> int:
    try:
        data = json.loads(report)
        results = data["Results"]
        if not isinstance(results, list) or not any(r.get("Type") == expected_type for r in results):
            raise ValueError("scanner did not recognize the requested configuration")
        failures = []
        checks = 0
        for result in results:
            if result.get("Type") != expected_type:
                continue
            for finding in result.get("Misconfigurations") or []:
                if finding.get("Status") not in {"PASS", "FAIL", "EXCEPTION"}:
                    raise ValueError("unknown check status")
                checks += 1
                if finding["Status"] == "FAIL":
                    # Only IDs are printed; paths, code snippets, and values stay private.
                    identifier = finding.get("ID", "")
                    if not re.fullmatch(r"[A-Za-z0-9_-]+", identifier):
                        raise ValueError("invalid check identifier")
                    failures.append(identifier)
        if failures:
            raise QualityError("Security check failed: " + ", ".join(sorted(set(failures))))
        if not checks:
            raise ValueError("no security checks were reported")
        return checks
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        raise QualityError("Security scan was incomplete or unrecognized; refusing to pass") from error


def reject_suppressions(root: Path, plan: Path | None):
    if plan:
        try:
            with zipfile.ZipFile(plan) as archive:
                suppressed = any(SUPPRESSION.search(archive.read(name))
                                 for name in archive.namelist() if name.endswith(CONFIGURATION))
        except zipfile.BadZipFile as error:
            raise QualityError("Saved plan is unrecognized; refusing to pass") from error
        if suppressed:
            raise QualityError("Saved plan configuration contains inline scanner suppressions")
        return
    suppressed = []
    for directory, subdirectories, files in os.walk(root):
        subdirectories[:] = [name for name in subdirectories if name not in {".git", ".infra"}]
        for name in files:
            path = Path(directory) / name
            if name.endswith(CONFIGURATION) and SUPPRESSION.search(path.read_bytes()):
                suppressed.append(path.relative_to(root).as_posix())
    if suppressed:
        raise QualityError("Inline scanner suppressions are not allowed: " + ", ".join(sorted(suppressed)))


def security(root: Path, stack: Path, variables: Path, *, plan: Path | None = None):
    reject_suppressions(root, plan)
    env = {key: value for key, value in os.environ.items() if not key.startswith("TRIVY_")}
    version = require_version("trivy", root, env)
    kind = "terraformplan-snapshot" if plan else "terraform"
    arguments = ["trivy", "config", "--config=", "--ignorefile=", "--disable-telemetry",
                 "--skip-version-check", "--skip-check-update", "--format=json",
                 "--include-non-failures", "--severity=HIGH,CRITICAL", "--exit-code=0",
                 f"--cache-dir={root / '.infra/trivy-cache' / version}",
                 f"--module-dir={root / '.infra/trivy-modules'}", f"--misconfig-scanners={kind}"]
    if plan:
        arguments.append(str(plan))
    else:
        arguments.extend(["--skip-dirs=.terraform", "--skip-dirs=tests", f"--tf-vars={variables}", str(stack)])
    report = execute(arguments, root, env=env, capture=True).stdout
    checks = inspect_report(report, kind)
    print(f"Security passed ({kind}, {checks} reported checks): {variables.parent.relative_to(root / 'live')}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["source", "plan", "lint"])
    parser.add_argument("directory", type=Path)
    parser.add_argument("planfile", type=Path, nargs="?")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = args.directory.resolve()
    if not directory.is_relative_to(root / "live") or len(directory.relative_to(root / "live").parts) != 4:
        parser.error("directory must be a native live deployment root")
    variables = directory / "terraform.tfvars.json"
    cloud = directory.relative_to(root / "live").parts[1]
    if (args.action == "plan") != (args.planfile is not None):
        parser.error("plan requires a saved plan path; source and lint do not accept one")
    if args.action == "lint":
        lint(root, directory, variables, cloud)
    else:
        security(root, directory, variables, plan=args.planfile.resolve() if args.planfile else None)


if __name__ == "__main__":
    try:
        main()
    except (QualityError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
