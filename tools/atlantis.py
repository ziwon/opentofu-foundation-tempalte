#!/usr/bin/env python3
"""Generate optional Atlantis project configuration from committed native roots."""

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = Path("integrations/atlantis/atlantis.yaml.example")
MODULE = re.compile(r'^module\s+"([^"]+)"\s*\{(.*?)^\}', re.MULTILINE | re.DOTALL)
ONE_LINE = re.compile(r'^module\s+"([^"]+)"\s*\{([^\n]*)\}\s*$', re.MULTILINE)
SOURCE = re.compile(r'^  source\s*=\s*"([^"]*)"', re.MULTILINE)
INLINE_SOURCE = re.compile(r'\bsource\s*=\s*"([^"]*)"')


def strip_block_comments(text: str) -> str:
    """Drop /* */ comments that start outside a string, such as an S3 ARN ending in /*."""
    out, position = [], 0
    while (start := text.find("/*", position)) >= 0:
        line = text[text.rfind("\n", 0, start) + 1:start]
        if line.replace('\\"', "").count('"') % 2:
            out.append(text[position:start + 2])
            position = start + 2
            continue
        end = text.find("*/", start + 2)
        out.append(text[position:start])
        position = len(text) if end < 0 else end + 2
    return "".join(out) + text[position:]


def module_sources(directory: Path) -> dict[str, str]:
    """Return each module call's top-level source, as `tofu fmt` lays it out."""
    files = sorted(path for pattern in ("*.tf", "*.tofu") for path in directory.glob(pattern) if path.is_file())
    text = strip_block_comments("\n".join(path.read_text() for path in files))
    sources = {name: source.group(1) for name, body in ONE_LINE.findall(text)
               if (source := INLINE_SOURCE.search(body))}
    text = ONE_LINE.sub("", text)
    sources.update({name: source.group(1) for name, body in MODULE.findall(text) if (source := SOURCE.search(body))})
    return sources


def module_directories(directory: Path) -> set[Path]:
    """Return every local module directory a root reaches, directly or through other modules."""
    reached, pending = set(), [directory]
    while pending:
        current = pending.pop()
        for source in module_sources(current).values():
            child = Path(os.path.normpath(current / source))
            if source.startswith(("./", "../")) and child not in reached:
                reached.add(child)
                pending.append(child)
    return reached


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
        modules = sorted(Path(os.path.relpath(module, root)).as_posix() for module in module_directories(directory))
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
                    *(f"{repository}/{module}/**/*.{extension}" for module in modules for extension in ("tf", "tofu")),
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
