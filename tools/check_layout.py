#!/usr/bin/env python3
"""Check native root structure, state identity, and documentation links."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from addresses import managed_addresses, verify_continuity
from atlantis import EXAMPLE, ROOT, configuration, write_configuration


def check(root: Path):
    write_configuration(configuration(root), root / EXAMPLE, check=True)
    roots = sorted((root / "live").glob("*/*/*/*/terraform.tfvars.json"))
    if not roots or (root / "stacks").exists():
        raise ValueError("Use native live roots and reusable modules; no stacks runtime layer")
    legacy = json.loads((root / "tools/legacy-addresses.json").read_text())
    states = set()
    compositions = set()
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
        module = root / "modules" / cloud / group / stack
        compositions.add(module)
        source = f'../../../../../modules/{cloud}/{group}/{stack}'
        if not re.search(r'source\s*=\s*"' + re.escape(source) + '"', (directory / "main.tf").read_text()):
            raise ValueError(f"Root does not call its resource module: {deployment}")
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
        try:
            verify_continuity(legacy.get(f"{cloud}/{group}/{stack}", []), *managed_addresses(directory))
        except ValueError as error:
            raise ValueError(f"{error}: {deployment}") from None
    discovered = {path.parent for path in (root / "modules").glob("*/*/*/main.tf")}
    if compositions != discovered:
        raise ValueError(f"Composition modules and live roots differ: {compositions ^ discovered}")
    for path in (root / "modules").rglob("*.tf"):
        if ".terraform" not in path.parts and re.search(r'\b(?:provider|backend)\s+"', path.read_text()):
            raise ValueError(f"Reusable modules must not configure providers or backends: {path}")
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
    print(f"Layout OK: {len(compositions)} modules, {len(roots)} native roots, unique state paths, valid local links")


if __name__ == "__main__":
    try:
        check(ROOT)
    except (ValueError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
