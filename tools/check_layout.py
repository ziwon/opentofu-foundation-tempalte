#!/usr/bin/env python3
"""Check deployment structure and local documentation links without cloud access."""

import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from infra import ROOT, UserError, inventory, source_files


def check(root: Path):
    deployments = inventory(root)
    if not deployments:
        raise UserError("No live deployments found")
    declared = {deployment.stack for deployment in deployments}
    discovered = {path.parent for path in (root / "stacks").rglob("backend.tf.json")}
    if declared != discovered:
        raise UserError(f"Stacks and deployment inventory differ: {declared ^ discovered}")
    state_addresses = set()
    for deployment in deployments:
        deployment.validate()
        address = (deployment.backend_type, json.dumps(deployment.backend(), sort_keys=True))
        if address in state_addresses:
            raise UserError(f"Duplicate state address: {deployment.name}")
        state_addresses.add(address)
        if "required_providers" in (deployment.stack / "versions.tf").read_text():
            if not (deployment.stack / ".terraform.lock.hcl").is_file():
                raise UserError(f"Missing provider lock file: {deployment.stack}; run infra.py lock")
    for path in source_files(root / "modules"):
        if re.search(r'\b(?:provider|backend)\s+"', path.read_text()):
            raise UserError(f"Reusable modules must not configure providers or backends: {path}")
    for path in root.rglob("*.md"):
        if any(part.startswith(".") for part in path.relative_to(root).parts[:-1]):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            link = urlsplit(target.strip("<>"))
            if link.scheme or link.netloc or not link.path:
                continue
            destination = (path.parent / unquote(link.path)).resolve()
            if not destination.is_relative_to(root.resolve()) or not destination.exists():
                raise UserError(f"Broken local link in {path.relative_to(root)}: {target}")
    print(f"Layout OK: {len(declared)} stacks, {len(deployments)} deployments, unique states, valid local links")


if __name__ == "__main__":
    try:
        check(ROOT)
    except (UserError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
