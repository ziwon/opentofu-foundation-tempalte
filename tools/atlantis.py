#!/usr/bin/env python3
"""Generate optional Atlantis project configuration from committed native roots."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = Path("integrations/atlantis/atlantis.yaml.example")
def module_directories(directory: Path) -> dict[str, Path]:
    """Ask OpenTofu which module directory each module call in a root loads."""
    with tempfile.TemporaryDirectory(prefix="modules-") as data:
        result = subprocess.run(["tofu", f"-chdir={directory}", "get", "-no-color"],
                                env={**os.environ, "TF_DATA_DIR": data}, capture_output=True, text=True)
        if result.returncode:
            lines = [line for line in result.stderr.splitlines() if line.strip()]
            raise ValueError(f"tofu get failed in {directory}: {lines[0] if lines else result.returncode}")
        manifest = json.loads((Path(data) / "modules/modules.json").read_text())
    base = Path(os.path.realpath(directory))
    return {module["Key"]: Path(os.path.normpath(base / module["Dir"])) for module in manifest["Modules"] if module["Key"]}


def configuration(root: Path, names=(), autoplan=False) -> dict:
    version = re.search(r'^opentofu\s*=\s*"([0-9.]+)"', (root / "mise.toml").read_text(), re.MULTILINE)
    if not version:
        raise ValueError("Pin opentofu in mise.toml before generating projects")
    inventory = {path.parent.relative_to(root / "live").as_posix(): path.parent
                 for path in (root / "live").glob("*/*/*/*/backend.tf")}
    selected = sorted(set(names)) if names else sorted(inventory)
    projects = []
    for name in selected:
        if name not in inventory:
            raise ValueError(f"Unknown deployment: {name}")
        directory = inventory[name]
        if name.split("/")[2] == "bootstrap":
            if names:
                raise ValueError("Bootstrap is managed directly with OpenTofu outside Atlantis")
            continue
        if not names and re.search(r'backend\s+"local"', (directory / "backend.tf").read_text()):
            continue
        repository = os.path.relpath(root, directory)
        repository_root = Path(os.path.realpath(root))
        modules = sorted({module.relative_to(repository_root).as_posix() for module in module_directories(directory).values()
                          if module.is_relative_to(repository_root)})
        projects.append({
            "name": name,
            "dir": directory.relative_to(root).as_posix(),
            "workspace": "default",
            "terraform_distribution": "opentofu",
            "terraform_version": version.group(1),
            "autoplan": {
                "enabled": autoplan,
                "when_modified": [
                    "*.tf", "*.tofu", "*.tf.json", "*.tofu.json", "*.tfvars.json", ".terraform.lock.hcl",
                    *(f"{repository}/{module}/**/*.{extension}" for module in modules for extension in ("tf", "tofu", "tf.json", "tofu.json")),
                    f"{repository}/tools/quality.py", f"{repository}/mise.toml",
                    f"{repository}/.tflint.hcl", f"{repository}/atlantis.yaml",
                ],
            },
        })
    return {"version": 3, "autodiscover": {"mode": "disabled"}, "automerge": False,
            "parallel_plan": False, "parallel_apply": False, "projects": projects}


def write_configuration(document: dict, output: Path | None = None, check=False):
    content = json.dumps(document, indent=2) + "\n"
    if output is None:
        print(content, end="")
    elif check:
        if not output.is_file() or output.read_text() != content:
            raise ValueError(f"Atlantis configuration is stale: {output}")
        print(f"Atlantis configuration matches deployment inventory: {output}")
    else:
        output.write_text(content)
        print(f"Wrote {len(document['projects'])} Atlantis projects to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deployment", action="append", default=[])
    parser.add_argument("--autoplan", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error("--check requires --output")
    try:
        write_configuration(configuration(ROOT, args.deployment, args.autoplan), args.output, args.check)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
