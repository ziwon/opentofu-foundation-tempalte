#!/usr/bin/env python3
"""Verify native local lifecycles in a disposable copy with no deployment helper."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def smoke():
    with tempfile.TemporaryDirectory(prefix="native local smoke ") as temporary:
        root = Path(temporary)
        for name in ("modules/context", "stacks/local", "live/dev/local", "live/stage/local", "live/prod/local"):
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns(".terraform", "*.tfplan"))
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("TF_VAR_", "TF_CLI_ARGS", "TF_DATA_DIR", "TF_WORKSPACE"))}

        def native(directory, *args, succeeds=True):
            result = subprocess.run(["tofu", f"-chdir={directory}", *args], env=env,
                                    capture_output=True, text=True, check=False)
            if (result.returncode == 0) != succeeds:
                raise RuntimeError(f"Native {args[0]} failed:\n{result.stdout}\n{result.stderr}")
            return result.stdout

        ids = set()
        for environment in ("dev", "stage", "prod"):
            name = f"{environment}/local/foundation/catalog"
            directory = root / "live" / name
            variables = directory / "terraform.tfvars.json"
            inputs = json.loads(variables.read_text())
            native(directory, "init", "-input=false")
            native(directory, "validate")
            native(directory, "test", "-no-color")
            native(directory, "plan", "-input=false", "-out=plan.tfplan")
            native(directory, "apply", "-input=false", "plan.tfplan")
            output = json.loads(native(directory, "output", "-json"))
            catalog = output["catalog"]["value"]
            assert catalog["name"] == f"{inputs['namespace']}-{inputs['name']}-{environment}"
            assert catalog["tags"]["environment"] == environment
            state = root / ".infra/state" / name / "terraform.tfstate"
            assert state.is_file(), state
            resources = json.loads(state.read_text())["resources"]
            identifier = resources[0]["instances"][0]["attributes"]["id"]
            assert identifier not in ids
            ids.add(identifier)
            assert native(directory, "state", "list").strip() == "module.stack.terraform_data.catalog"
            assert environment in native(directory, "state", "show", "module.stack.terraform_data.catalog")
            native(directory, "state", "show", "module.stack.terraform_data.missing", succeeds=False)
            extra_tags = {**inputs.get("tags", {}), "owner": "platform", "cost_center": "research"}
            variables.write_text(json.dumps({**inputs, "tags": extra_tags}))
            native(directory, "plan", "-input=false", "-out=plan.tfplan")
            native(directory, "apply", "-input=false", "plan.tfplan")
            changed = json.loads(native(directory, "output", "-json"))["catalog"]["value"]
            assert changed["name"] == catalog["name"]
            assert changed["tags"] == {**catalog["tags"], **extra_tags}
            boundary = {f"tag_{index}": "" for index in range(46)}
            variables.write_text(json.dumps({**inputs, "tags": boundary}))
            native(directory, "plan", "-input=false")
            for tags in ({"project": "override"}, {"environment": "override"}, {"managed_by": "override"},
                         {"Owner": "platform"}, {"owner": "Platform"}, {"owner": None},
                         {"a" * 64: "value"}, {"owner": "a" * 64}, {**boundary, "overflow": ""}):
                variables.write_text(json.dumps({**inputs, "tags": tags}))
                native(directory, "plan", "-input=false", succeeds=False)
            variables.write_text(json.dumps(inputs))
            native(directory, "plan", "-destroy", "-input=false", "-out=destroy.tfplan")
            native(directory, "apply", "-input=false", "destroy.tfplan")
            assert not json.loads(state.read_text()).get("resources")
    print("Native local init/plan/apply/output/state/destroy passed for dev, stage and prod; state isolation and context tag validation passed.")


if __name__ == "__main__":
    smoke()
