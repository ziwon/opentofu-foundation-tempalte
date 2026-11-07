"""Trace managed resource addresses through local modules and moved blocks."""

from pathlib import Path
import re

BLOCK = re.compile(r'^(resource|module|moved)((?:[ \t]+"[^"]*")*)[ \t]*\{', re.M)


def block_body(text: str, start: int) -> str:
    depth = 1
    for end in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[end], 0)
        if depth == 0:
            return text[start:end]
    raise ValueError("Unbalanced braces in HCL block")


def attribute(body: str, name: str) -> str | None:
    """Return a block's own attribute, ignoring nested blocks such as dynamic for_each."""
    top, nested = body, 1
    while nested:
        top, nested = re.subn(r"\{[^{}]*\}", "", top)
    match = re.search(rf"^\s*{name}\s*=\s*(.+?)\s*$", top, re.M)
    return match.group(1) if match else None


def parse_module(text: str) -> tuple[set[str], dict[str, str], list[tuple[str, str]]]:
    """Return one module's resources, local module calls, and moves, relative to that module."""
    resources, calls, moves = set(), {}, []
    for match in BLOCK.finditer(text):
        kind, labels = match.group(1), re.findall(r'"([^"]*)"', match.group(2))
        body = block_body(text, match.end())
        if kind == "moved":
            moves.append((attribute(body, "from"), attribute(body, "to")))
            continue
        address = ".".join(labels) if kind == "resource" else f"module.{labels[0]}"
        for meta in ("count", "for_each"):
            if attribute(body, meta):
                raise ValueError(f"Cannot trace {address} with {meta}")
        if kind == "resource":
            resources.add(address)
            continue
        source = (attribute(body, "source") or "").strip('"')
        if not source.startswith(("./", "../")):
            raise ValueError(f"Cannot trace {address} with non-local source {source!r}")
        calls[labels[0]] = source
    return resources, calls, moves


def managed_addresses(directory: Path, prefix: str = "") -> tuple[set[str], list[tuple[str, str]]]:
    """Return absolute resource addresses and moves for a root and every local module it calls."""
    text = "\n".join(path.read_text() for path in sorted(directory.glob("*.tf")))
    local_resources, calls, local_moves = parse_module(text)
    resources = {prefix + address for address in local_resources}
    moves = [(prefix + source, prefix + target) for source, target in local_moves]
    for name, source in calls.items():
        child_resources, child_moves = managed_addresses(directory / source, f"{prefix}module.{name}.")
        resources |= child_resources
        moves += child_moves
    return resources, moves


def verify_continuity(legacy: list[str], resources: set[str], moves: list[tuple[str, str]]):
    """Require each legacy address to reach its own current resource through moved blocks."""
    targets = {}
    for source, target in moves:
        if targets.setdefault(source, target) != target:
            raise ValueError(f"Conflicting moved blocks from {source}")
    reached = {}
    for old in legacy:
        address, seen = old, {old}
        while address in targets:
            address = targets[address]
            if address in seen:
                raise ValueError(f"Moved blocks form a cycle through {address}")
            seen.add(address)
        if address not in resources:
            raise ValueError(f"Legacy address {old} ends at {address}, which is not a managed resource; add a moved block")
        if address in reached:
            raise ValueError(f"Legacy addresses {reached[address]} and {old} both reach {address}")
        reached[address] = old
    for target in targets.values():
        if target not in resources and target not in targets:
            raise ValueError(f"Moved block target {target} is not a managed resource or another move's source")
