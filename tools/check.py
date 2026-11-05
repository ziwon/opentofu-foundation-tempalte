#!/usr/bin/env python3
"""Run developer and CI checks without contacting deployment backends or cloud APIs."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from check_layout import check
from quality import lint, security

ROOT = Path(__file__).resolve().parents[1]


def run(*args, cwd=ROOT, env=None):
    subprocess.run(args, cwd=cwd, env=env, check=True)


def main():
    check(ROOT)
    run("tofu", "fmt", "-check", "-recursive")
    run("python3", "-m", "unittest", "discover", "-s", "tests", "-v")
    cache = ROOT / ".infra/provider-cache"
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
        for source in sorted((ROOT / "modules").glob("*/*/*/main.tf")):
            module = source.parent.relative_to(ROOT / "modules")
            directory = temporary / "modules" / module
            shutil.copytree(source.parent, directory, ignore=shutil.ignore_patterns(".terraform", ".terraform.lock.hcl"))
            lock = ROOT / "live/dev" / module / ".terraform.lock.hcl"
            if lock.is_file():
                shutil.copyfile(lock, directory / lock.name)
            env["TF_DATA_DIR"] = str(temporary / "module-data" / module)
            run("tofu", f"-chdir={directory}", "init", "-backend=false", "-input=false", "-lockfile=readonly", env=env)
            run("tofu", f"-chdir={directory}", "test", "-no-color", env=env)
    print("Native root validation, environment tests, resource module tests, lint and source security passed.")


if __name__ == "__main__":
    main()
