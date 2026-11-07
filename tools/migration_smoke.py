#!/usr/bin/env python3
"""Verify the frozen shared-root catalog migrates to native roots without resource changes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile


BASELINE = "657f324df43b4b203a759011af9792a7a450cf57"
ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/legacy-local"
DEPLOYMENTS = ("dev/local/foundation/catalog", "prod/local/foundation/catalog")
OLD_ADDRESS = "terraform_data.catalog"
NEW_ADDRESS = "module.stack.terraform_data.catalog"


@dataclass(frozen=True)
class Snapshot:
    resources: dict[str, dict]
    outputs: dict[str, dict]


def run(arguments: list[str], *, cwd: Path, env: dict[str, str], log: list[str]) -> str:
    result = subprocess.run(arguments, cwd=cwd, env=env, text=True, capture_output=True)
    log.append(f"$ cd {shlex.quote(str(cwd))} && {shlex.join(arguments)}\n{result.stdout}{result.stderr}")
    if result.returncode:
        raise RuntimeError(f"Command failed in {cwd}:\n{log[-1]}")
    return result.stdout


def resources(module: dict) -> dict[str, dict]:
    found = {item["address"]: item["values"] for item in module.get("resources", [])
             if item["mode"] == "managed"}
    for child in module.get("child_modules", []):
        found.update(resources(child))
    return found


def snapshot(tofu: str, directory: Path, env: dict[str, str], log: list[str]) -> Snapshot:
    state = json.loads(run([tofu, "show", "-json"], cwd=directory, env=env, log=log))
    outputs = json.loads(run([tofu, "output", "-json"], cwd=directory, env=env, log=log))
    return Snapshot(resources(state.get("values", {}).get("root_module", {})), outputs)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify(root: Path, artifacts: Path | None) -> None:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("TF_", "TOFU_"))}
    env["TF_IN_AUTOMATION"] = "1"
    tofu = shutil.which("tofu")
    require(tofu is not None, "Install the pinned OpenTofu version from mise.toml first")
    log: list[str] = []
    report = {"baseline": BASELINE, "target_root": str(root), "deployments": {}}
    try:
        version = json.loads(run([tofu, "version", "-json"], cwd=root, env=env, log=log))
        pin = re.search(r'^opentofu\s*=\s*"([^"\n]+)"', (root / "mise.toml").read_text(), re.M)
        require(pin is not None, "mise.toml must pin OpenTofu")
        require(version["terraform_version"] == pin.group(1),
                f"Expected OpenTofu {pin.group(1)}, got {version['terraform_version']}")
        report["opentofu"] = version["terraform_version"]
        with tempfile.TemporaryDirectory(prefix="native migration ") as temporary:
            repository = Path(temporary) / "repository with spaces"
            shutil.copytree(FIXTURE, repository)
            before: dict[str, Snapshot] = {}
            for deployment in DEPLOYMENTS:
                state = repository / ".infra/state" / deployment / "terraform.tfstate"
                state.parent.mkdir(parents=True)
                shared = repository / "stacks/local/foundation/catalog"
                variables = repository / "live" / deployment / "terraform.tfvars.json"
                baseline_env = {**env, "TF_DATA_DIR": str(Path(temporary) / "old data" / deployment)}
                run([tofu, "init", "-input=false", f"-backend-config=path={state}"],
                    cwd=shared, env=baseline_env, log=log)
                plan = Path(temporary) / f"{deployment.split('/')[0]} baseline.tfplan"
                run([tofu, "plan", "-input=false", f"-var-file={variables}", f"-out={plan}"],
                    cwd=shared, env=baseline_env, log=log)
                run([tofu, "apply", "-input=false", str(plan)], cwd=shared, env=baseline_env, log=log)
                before[deployment] = snapshot(tofu, shared, baseline_env, log)
                require(set(before[deployment].resources) == {OLD_ADDRESS},
                        f"Unexpected baseline managed resources for {deployment}")
                require(state.is_file(), f"Baseline did not write the expected state: {state}")
                report["deployments"][deployment] = {
                    "before": {"resources": before[deployment].resources, "outputs": before[deployment].outputs},
                }
            require(before[DEPLOYMENTS[0]].resources[OLD_ADDRESS]["id"] !=
                    before[DEPLOYMENTS[1]].resources[OLD_ADDRESS]["id"],
                    "Baseline dev and prod must have isolated resource IDs")
            for name in ("modules", "stacks", "live"):
                shutil.rmtree(repository / name)
                shutil.copytree(root / name, repository / name,
                                ignore=shutil.ignore_patterns(".terraform", ".infra", "__pycache__"))
            for deployment in DEPLOYMENTS:
                inputs = Path("live") / deployment / "terraform.tfvars.json"
                shutil.copyfile(FIXTURE / inputs, repository / inputs)
            require(not (repository / "tools").exists(), "Fixture must not contain repository Python")
            for deployment in DEPLOYMENTS:
                native = repository / "live" / deployment
                run([tofu, "init", "-input=false"], cwd=native, env=env, log=log)
                run([tofu, "validate"], cwd=native, env=env, log=log)
                plan = Path(temporary) / f"{deployment.split('/')[0]} migration.tfplan"
                run([tofu, "plan", "-input=false", f"-out={plan}"], cwd=native, env=env, log=log)
                planned = json.loads(run([tofu, "show", "-json", str(plan)],
                                         cwd=native, env=env, log=log))
                changes = {change["address"]: change for change in planned.get("resource_changes", [])
                           if change["mode"] == "managed"}
                require(set(changes) == {NEW_ADDRESS},
                        f"Migration changed the managed-resource inventory for {deployment}: {list(changes)}")
                report["deployments"][deployment]["resource_changes"] = list(changes.values())
                change = changes[NEW_ADDRESS]
                require(change.get("previous_address") == OLD_ADDRESS,
                        f"Missing catalog address move for {deployment}")
                require(change["change"]["actions"] == ["no-op"],
                        f"Migration would change a resource for {deployment}: {change['change']['actions']}")
                require(change["change"]["before"] == change["change"]["after"] ==
                        before[deployment].resources[OLD_ADDRESS],
                        f"Migration changed catalog values for {deployment}")
                require(set(planned.get("output_changes", {})) == set(before[deployment].outputs),
                        f"Migration changed output names for {deployment}")
                for name, output in planned["output_changes"].items():
                    require(output["actions"] == ["no-op"] and
                            output["after"] == before[deployment].outputs[name]["value"],
                            f"Migration changed output {name} for {deployment}")
                run([tofu, "apply", "-input=false", str(plan)], cwd=native, env=env, log=log)
                after = snapshot(tofu, native, env, log)
                require(after.resources == {NEW_ADDRESS: before[deployment].resources[OLD_ADDRESS]},
                        f"Migration changed resource IDs or values for {deployment}")
                require(after.outputs == before[deployment].outputs,
                        f"Migration changed outputs for {deployment}")
                state = repository / ".infra/state" / deployment / "terraform.tfstate"
                stored = json.loads(state.read_text())
                require(stored["resources"][0].get("module") == "module.stack",
                        f"Native root did not migrate the original state file for {deployment}")
                require(run([tofu, "state", "list"], cwd=native, env=env, log=log).strip() == NEW_ADDRESS,
                        f"Unexpected native state address for {deployment}")
                report["deployments"][deployment]["after"] = {
                    "resources": after.resources, "outputs": after.outputs,
                }
                destroy = Path(temporary) / f"{deployment.split('/')[0]} destroy.tfplan"
                run([tofu, "plan", "-destroy", "-input=false", f"-out={destroy}"],
                    cwd=native, env=env, log=log)
                run([tofu, "apply", "-input=false", str(destroy)], cwd=native, env=env, log=log)
                require(not json.loads(state.read_text()).get("resources"),
                        f"Destroy left resources in the original state file for {deployment}")
                require(not run([tofu, "state", "list"], cwd=native, env=env, log=log).strip(),
                        f"Destroy left resources visible to the native root for {deployment}")
                report["deployments"][deployment]["destroyed"] = True
            generated = [path.relative_to(repository).as_posix() for path in repository.rglob("*")
                         if path.name in {"backend.generated.hcl", "initialized.json", "plan.json"}]
            require(not generated, f"Native migration unexpectedly required runner metadata: {generated}")
            report["passed"] = True
    finally:
        if artifacts:
            artifacts.mkdir(parents=True, exist_ok=True)
            (artifacts / "migration.log").write_text("\n".join(log))
            (artifacts / "migration.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Native migration passed from {BASELINE}: dev/prod moves are no-op, "
          "IDs and outputs unchanged, original states destroyed, no runner files required")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Native-root checkout to verify")
    parser.add_argument("--artifacts", type=Path, help="Retain the local command log and comparison JSON")
    args = parser.parse_args()
    verify(args.root.resolve(), args.artifacts.resolve() if args.artifacts else None)
