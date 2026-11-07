#!/usr/bin/env python3
"""Check native root structure, state identity, and documentation links."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from atlantis import EXAMPLE, ROOT, configuration, module_sources, write_configuration


# Override and JSON files can replace a module call without changing the files this check reads.
UNREAD = ("override.tf", "*_override.tf", "override.tofu", "*_override.tofu", "*.tf.json", "*.tofu.json")


def reject_unread_files(directory: Path, label: str):
    unread = sorted(path.name for pattern in UNREAD for path in directory.glob(pattern))
    if unread:
        raise ValueError(f"Use plain .tf or .tofu files, not {', '.join(unread)}: {label}")


def stack_directories(root: Path) -> set[Path]:
    return {path.parent for path in (root / "stacks").glob("*/*/*/*.tf") if path.is_file()}


def check(root: Path):
    write_configuration(configuration(root), root / EXAMPLE, check=True)
    for directory in sorted((root / "live").glob("*/*/*/*")):
        if directory.is_dir() and not (directory / "terraform.tfvars.json").is_file():
            raise ValueError(f"Missing terraform.tfvars.json: {directory.relative_to(root / 'live')}")
    roots = sorted((root / "live").glob("*/*/*/*/terraform.tfvars.json"))
    if not roots:
        raise ValueError("No native roots under live/<environment>/<cloud>/<group>/<stack>")
    states = set()
    stacks = set()
    for variables in roots:
        directory = variables.parent
        deployment = directory.relative_to(root / "live")
        environment, cloud, group, stack = deployment.parts
        for name in ("backend.tf", "context.tf", "main.tf", "variables.tf", "outputs.tf", "versions.tf", "providers.tf", "tests/context.tftest.hcl"):
            if not (directory / name).is_file():
                raise ValueError(f"Missing native root file: {directory / name}")
        values = json.loads(variables.read_text())
        if values.get("environment") != environment:
            raise ValueError(f"Environment differs from directory: {deployment}")
        stacks.add(root / "stacks" / cloud / group / stack)
        backend = (directory / "backend.tf").read_text()
        block = re.search(r'backend\s+"([^"]+)"', backend)
        if not block:
            raise ValueError(f"Missing backend block: {deployment}")
        kind = block.group(1)
        attribute = {"local": "path", "s3": "key", "azurerm": "key", "gcs": "prefix"}.get(kind)
        if not attribute:
            raise ValueError(f"Unsupported backend kind {kind!r}: {deployment}")
        identity = re.search(r'\b' + attribute + r'\s*=\s*"([^"]+)"', backend)
        if not identity:
            raise ValueError(f"Missing backend {attribute!r} attribute: {deployment}")
        actual = identity.group(1)
        expected = deployment.as_posix() + ("" if kind == "gcs" else "/terraform.tfstate")
        if kind == "local":
            expected = "../../../../../.infra/state/" + expected
        if actual != expected:
            raise ValueError(f"State identity differs: {deployment}: {actual}")
        state = kind, actual
        if state in states:
            raise ValueError(f"Duplicate state identity: {deployment}")
        states.add(state)
        if cloud != "local" and not (directory / ".terraform.lock.hcl").is_file():
            raise ValueError(f"Missing provider lock: {deployment}")
        reject_unread_files(directory, deployment.as_posix())
        source = f"../../../../../stacks/{cloud}/{group}/{stack}"
        if module_sources(directory).get("stack") != source:
            raise ValueError(f"Root does not call its stack {source}: {deployment}")
    discovered = stack_directories(root)
    for directory in sorted(discovered):
        reject_unread_files(directory, directory.relative_to(root).as_posix())
    if stacks != discovered:
        raise ValueError(f"Stacks and the stacks live roots call differ: {sorted(path.relative_to(root).as_posix() for path in stacks ^ discovered)}")
    for path in [path for base in ("modules", "stacks") for pattern in ("*.tf", "*.tofu") for path in (root / base).rglob(pattern)]:
        if ".terraform" not in path.parts and re.search(r'\b(?:provider|backend)\s+"', path.read_text()):
            raise ValueError(f"Modules and stacks must not configure providers or backends: {path}")
    for path in root.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(root).parts[:-1]):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            link = urlsplit(target.strip("<>"))
            if link.scheme or link.netloc or not link.path:
                continue
            destination = (path.parent / unquote(link.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                raise ValueError(f"Broken local link in {path.relative_to(root)}: {target}")
    print(f"Layout OK: {len(stacks)} stacks, {len(roots)} native roots, unique state paths, valid local links")


if __name__ == "__main__":
    try:
        check(ROOT)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
