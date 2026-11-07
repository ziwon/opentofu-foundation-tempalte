#!/usr/bin/env python3
"""Run developer and CI checks without contacting deployment backends or cloud APIs."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from check_layout import check, stack_directories
from quality import lint, security

ROOT = Path(__file__).resolve().parents[1]
LOCK = ".terraform.lock.hcl"


def run(*args, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    check(ROOT)
    run("tofu", "fmt", "-check", "-recursive")
    run("python3", "-m", "unittest", "discover", "-s", "tests", "-v")
    cache = Path(os.environ.get("TF_PLUGIN_CACHE_DIR") or ROOT / ".infra/provider-cache")
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="foundation checks ") as temporary:
        temporary = Path(temporary)
        env = {**os.environ, "TF_PLUGIN_CACHE_DIR": str(cache)}
        for variables in sorted((ROOT / "live").glob("*/*/*/*/terraform.tfvars.json")):
            directory = variables.parent
            deployment = directory.relative_to(ROOT / "live")
            cloud = deployment.parts[1]
            env["TF_DATA_DIR"] = str(temporary / "data" / deployment)
            run("tofu", f"-chdir={directory}", "init", "-backend=false", "-input=false", "-lockfile=readonly", env=env)
            run("tofu", f"-chdir={directory}", "validate", "-no-color", env=env)
            run("tofu", f"-chdir={directory}", "test", "-no-color", env=env)
            lint(ROOT, directory, variables, cloud)
            if cloud != "local":
                security(ROOT, directory, variables)
        tree = temporary / "tree"
        ignore = shutil.ignore_patterns(".terraform", LOCK)
        shutil.copytree(ROOT / "modules", tree / "modules", ignore=ignore)
        units = []
        for directory in sorted(stack_directories(ROOT)):
            stack = directory.relative_to(ROOT / "stacks")
            shutil.copytree(directory, tree / "stacks" / stack, ignore=ignore)
            units.append((Path("stacks") / stack, ROOT / "live/dev" / stack / LOCK))
        for tests in sorted((ROOT / "modules").rglob("tests")):
            module = tests.parent.relative_to(ROOT)
            if tests.is_dir() and ".terraform" not in module.parts:
                units.append((module, next(iter(sorted((ROOT / "live/dev" / module.parts[1]).glob(f"*/*/{LOCK}"))), None)))
        for unit, lock in units:
            directory = tree / unit
            if lock and lock.is_file():
                shutil.copyfile(lock, directory / LOCK)
            env["TF_DATA_DIR"] = str(temporary / "unit-data" / unit)
            run("tofu", f"-chdir={directory}", "init", "-backend=false", "-input=false", "-lockfile=readonly", env=env)
            run("tofu", f"-chdir={directory}", "test", "-no-color", env=env)
    print("Native root validation, environment tests, stack and module tests, lint and source security passed.")


if __name__ == "__main__":
    main()
