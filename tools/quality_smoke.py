#!/usr/bin/env python3
"""Prove real linters and source/saved-plan scanners accept safe fixtures and reject unsafe ones."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from infra import ROOT, command_lock
from quality import QualityError, lint, security


def smoke(engine: str):
    with tempfile.TemporaryDirectory(prefix="quality smoke ") as temporary:
        root = Path(temporary)
        stack = root / "stacks/aws/network/fixture"
        live = root / "live/dev/aws/network/fixture"
        stack.mkdir(parents=True)
        live.mkdir(parents=True)
        variables = live / "terraform.tfvars.json"
        variables.write_text('{}\n')
        shutil.copyfile(ROOT / "mise.toml", root / "mise.toml")
        # This fixture tests language linting; full checks cover pinned cloud rules.
        (root / ".tflint.hcl").write_text('plugin "terraform" {\n  enabled = true\n  preset = "recommended"\n}\n')
        for name in ("versions.tf", ".terraform.lock.hcl"):
            shutil.copyfile(ROOT / "stacks/aws/network/core" / name, stack / name)
        # Fake credentials and all identity probes disabled: creation plans only,
        # no data sources, refresh, apply, or real cloud credentials.
        (stack / "providers.tf").write_text('''provider "aws" {
  region                      = "us-east-1"
  access_key                  = "fixture"
  secret_key                  = "fixture"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true
  skip_region_validation     = true
}
''')
        main = stack / "main.tf"
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
            result = subprocess.run([engine, f"-chdir={stack}", *args], env=env,
                                    capture_output=True, text=True, check=False)
            if result.returncode:
                raise RuntimeError(f"Fixture {args[0]} failed:\n{result.stderr}")

        def rejected(function, *args, **kwargs):
            try:
                function(*args, **kwargs)
            except QualityError:
                return
            raise AssertionError("Unsafe fixture unexpectedly passed")

        with command_lock(ROOT, "provider-cache"):
            native("init", "-backend=false", "-input=false", "-lockfile=readonly")
        security(root, stack, variables)
        native("plan", "-input=false", "-refresh=false", f"-out={plan}")
        security(root, stack, variables, plan=plan)

        safe = main.read_text()
        main.write_text(safe.replace("  ingress     = []", '''  ingress {
    description = "Unsafe fixture"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }'''))
        rejected(security, root, stack, variables)
        native("plan", "-input=false", "-refresh=false", f"-out={plan}")
        rejected(security, root, stack, variables, plan=plan)
        main.write_text(safe)
        # Scanning a saved plan must still reject it after the source is fixed.
        rejected(security, root, stack, variables, plan=plan)
        plan.write_bytes(b"unrecognized plan")
        rejected(security, root, stack, variables, plan=plan)

        # The bundled language rules suffice here; cloud plugin execution is
        # covered by `check` for every actual deployment.
        lint(root, stack, variables, "local")
        (stack / "unused.tf").write_text('variable "unused" { default = "unused" }\n')
        rejected(lint, root, stack, variables, "local")
    print(f"{engine}: real safe/unsafe source and saved-plan scans, invalid-plan rejection, and linter rejection passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["tofu", "terraform"], default=os.environ.get("TF_CLI", "tofu"))
    smoke(parser.parse_args().engine)
