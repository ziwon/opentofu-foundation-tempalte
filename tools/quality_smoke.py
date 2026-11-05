#!/usr/bin/env python3
"""Prove real linters and source/saved-plan scanners accept safe fixtures and reject unsafe ones."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from quality import QualityError, lint, security

ROOT = Path(__file__).resolve().parents[1]


def smoke(workflow_check=None):
    with tempfile.TemporaryDirectory(prefix="quality smoke ") as temporary:
        root = Path(temporary)
        directory = root / "live/dev/aws/network/fixture"
        directory.mkdir(parents=True)
        variables = directory / "terraform.tfvars.json"
        variables.write_text('{}\n')
        shutil.copyfile(ROOT / "mise.toml", root / "mise.toml")
        (root / "tools").mkdir()
        shutil.copyfile(ROOT / "tools/quality.py", root / "tools/quality.py")
        shutil.copyfile(ROOT / ".tflint.hcl", root / ".tflint.hcl")
        for name in ("versions.tf", ".terraform.lock.hcl"):
            shutil.copyfile(ROOT / "live/dev/aws/network/core" / name, directory / name)
        # Fake credentials and all identity probes disabled: creation plans only,
        # no data sources, refresh, apply, or real cloud credentials.
        (directory / "providers.tf").write_text('''provider "aws" {
  region                      = "us-east-1"
  access_key                  = "fixture"
  secret_key                  = "fixture"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation     = true
}
''')
        main = directory / "main.tf"
        main.write_text('''resource "aws_security_group" "fixture" {
  name        = "fixture"
  description = "Scanner fixture"
  vpc_id      = "vpc-0123456789abcdef0"
  ingress     = []
  egress      = []
}
''')
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("AWS_", "TF_VAR_", "TF_CLI_ARGS"))}
        (ROOT / ".infra/provider-cache").mkdir(parents=True, exist_ok=True)
        env.update(TF_DATA_DIR=str(root / ".infra/data"), TF_WORKSPACE="default",
                   TF_PLUGIN_CACHE_DIR=str(ROOT / ".infra/provider-cache"), AWS_EC2_METADATA_DISABLED="true")
        plan = root / ".infra/fixture.tfplan"

        def native(*args):
            result = subprocess.run(["tofu", f"-chdir={directory}", *args], env=env,
                                    capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError(f"Fixture {args[0]} failed:\n{result.stderr}")

        def rejected(function, *args, **kwargs):
            try:
                function(*args, **kwargs)
            except QualityError:
                return
            raise AssertionError("Unsafe fixture unexpectedly passed")

        native("init", "-backend=false", "-input=false", "-lockfile=readonly")
        security(root, directory, variables)
        native("plan", "-input=false", "-refresh=false", f"-out={plan}")
        security(root, directory, variables, plan=plan)
        if workflow_check:
            workflow_check(directory, plan, env, True)

        safe = main.read_text()
        main.write_text(safe.replace("  ingress     = []", '''  ingress {
    description = "Unsafe fixture"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }'''))
        rejected(security, root, directory, variables)
        native("plan", "-input=false", "-refresh=false", f"-out={plan}")
        rejected(security, root, directory, variables, plan=plan)
        if workflow_check:
            workflow_check(directory, plan, env, False)
        main.write_text(safe)
        rejected(security, root, directory, variables, plan=plan)
        if workflow_check:
            workflow_check(directory, plan, env, False)
        plan.write_bytes(b"unrecognized plan")
        rejected(security, root, directory, variables, plan=plan)

        lint(root, directory, variables, "local")
        (directory / "unused.tf").write_text('variable "unused" { default = "unused" }\n')
        rejected(lint, root, directory, variables, "local")
    print("OpenTofu: real safe/unsafe source and saved-plan scans, invalid-plan rejection, and linter rejection passed")


if __name__ == "__main__":
    smoke()
