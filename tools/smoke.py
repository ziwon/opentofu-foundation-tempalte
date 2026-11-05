#!/usr/bin/env python3
"""Exercise the real CLI using only local terraform_data resources in a temporary repository."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from infra import ROOT, Deployment, Runner


def smoke(engine: str):
    with tempfile.TemporaryDirectory(prefix="infra smoke ") as temporary:
        root = Path(temporary)
        for directory in ("tools", "modules", "stacks/local", "live/dev/local", "live/prod/local"):
            shutil.copytree(ROOT / directory, root / directory, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("mise.toml", ".tflint.hcl"):
            shutil.copyfile(ROOT / name, root / name)

        def command(action, name, *arguments, succeeds=True):
            result = subprocess.run([sys.executable, str(root / "tools/infra.py"), "--engine", engine,
                                     action, name, *arguments], text=True, capture_output=True)
            if (result.returncode == 0) != succeeds:
                raise RuntimeError(f"Unexpected result for {action} {name}:\n{result.stdout}\n{result.stderr}")
            return result

        targets = ["dev/local/foundation/catalog", "prod/local/foundation/catalog"]
        for name in targets:
            command("init", name)
            command("plan", name)
        for name in targets:
            command("apply", name, "--yes")
            runner = Runner(Deployment(root, name), engine)
            output = json.loads(runner.run("output", "-json", capture=True).stdout)
            assert output["catalog"]["value"]["tags"]["environment"] == name.split("/")[0]
            assert Path(runner.deployment.backend()["path"]).is_file()
            assert "terraform_data.catalog" in command("state-list", name).stdout
            assert name.split("/")[0] in command("state-show", name, "terraform_data.catalog").stdout
            command("state-show", name, "terraform_data.missing", succeeds=False)
            command("apply", name, "--yes", succeeds=False)

        name = targets[0]
        deployment = Deployment(root, name)
        original = deployment.variables.read_text()
        runner = Runner(deployment, engine)
        before = json.loads(runner.run("output", "-json", capture=True).stdout)["catalog"]["value"]
        inputs = json.loads(original)
        extra_tags = {"owner": "platform", "cost_center": "research"}
        deployment.variables.write_text(json.dumps({**inputs, "tags": extra_tags}))
        command("plan", name)
        command("apply", name, "--yes")
        after = json.loads(runner.run("output", "-json", capture=True).stdout)["catalog"]["value"]
        assert after["name"] == before["name"]
        assert after["tags"] == {**before["tags"], **extra_tags}

        boundary_tags = {f"tag_{index}": "" for index in range(46)}
        deployment.variables.write_text(json.dumps({**inputs, "tags": boundary_tags}))
        command("plan", name)
        for invalid_tags in (
            {"project": "override"}, {"environment": "override"}, {"managed_by": "override"},
            {"Owner": "platform"}, {"owner": "Platform"}, {"owner": None},
            {"a" * 64: "value"}, {"owner": "a" * 64}, {**boundary_tags, "overflow": ""},
        ):
            deployment.variables.write_text(json.dumps({**inputs, "tags": invalid_tags}))
            result = command("plan", name, succeeds=False)
            assert "Invalid value for variable" in result.stdout + result.stderr
            assert not runner.plan.exists() and not runner.receipt.exists()
        deployment.variables.write_text(original)

        command("plan", name)
        deployment.variables.write_text(original.replace("starter", "changed"))
        result = command("apply", name, "--yes", succeeds=False)
        assert "no longer matches" in result.stderr
        deployment.variables.write_text(original)

        command("plan", name)
        runner.plan.write_bytes(runner.plan.read_bytes() + b"tampered")
        result = command("apply", name, "--yes", succeeds=False)
        assert "no longer matches" in result.stderr

        command("plan", name)
        invalid = deployment.stack / "invalid.tf"
        invalid.write_text("this is not valid HCL @@@\n")
        command("plan", name, succeeds=False)
        invalid.unlink()
        assert not runner.plan.exists() and not runner.receipt.exists()

        for name in targets:
            command("plan", name, "--destroy")
            command("apply", name, "--yes")
            state = json.loads(Path(Deployment(root, name).backend()["path"]).read_text())
            assert not state.get("resources"), state
    print(f"{engine}: real init/plan/security/apply/output/state-list/state-show/destroy, environment isolation, tag propagation/validation, stable names, stale-plan rejection, and failed-plan cleanup passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["tofu", "terraform"], default=os.environ.get("TF_CLI", "tofu"))
    smoke(parser.parse_args().engine)
