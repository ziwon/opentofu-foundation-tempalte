"""Trace managed resource addresses through local modules and moved blocks."""

from pathlib import Path
import re

UNREAD = ("*.tofu", "*.tf.json", "*.tofu.json", "override.tf", "*_override.tf")
INTERPOLATION, ESCAPE = "\0", "\1"
LABEL = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")
SOURCE = re.compile(r"\.{1,2}/[A-Za-z0-9._/-]*")
BLOCK = re.compile(r'^(resource|module|moved)((?:[ \t]+"[^"]*")*)[ \t]*\{', re.M)


def strip(text: str) -> str:
    """Drop comments, interpolations, and braces inside strings; reject what it cannot read."""
    out, i, stack = [], 0, []
    while i < len(text):
        char, pair = text[i], text[i:i + 2]
        if stack and stack[-1] == "string":
            if pair == "%{" or text.startswith("$${", i):
                raise ValueError("Cannot trace template directives or escaped interpolations")
            if pair == "${":
                if "code" not in stack:
                    out.append(INTERPOLATION)
                stack.append("code")
                i += 1
            elif char == "\\":
                if "code" not in stack:
                    out.append(ESCAPE)
                i += 1
            else:
                if char == '"':
                    stack.pop()
                if char not in "{}" and "code" not in stack:
                    out.append(char)
        elif pair == "/*":
            close = text.find("*/", i + 2)
            i = len(text) if close < 0 else close + 1
        elif pair == "//" or char == "#":
            close = text.find("\n", i)
            i = len(text) if close < 0 else close - 1
        elif pair == "<<":
            raise ValueError("Cannot trace heredocs")
        elif stack:
            if char in '"{':
                stack.append("string" if char == '"' else "code")
            elif char == "}":
                stack.pop()
        else:
            if char == '"':
                stack.append("string")
            out.append(char)
        i += 1
    return "".join(out)


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
    match = re.search(rf"^\s*{name}\s*=[ \t]*(.*?)\s*$", top, re.M)
    return match.group(1) if match else None


def parse_module(text: str) -> tuple[set[str], dict[str, str], list[tuple[str, str]]]:
    """Return one module's resources, local module calls, and moves, relative to that module."""
    resources, calls, moves = set(), {}, []
    if any(char.isspace() and char not in " \t\n" for char in text):
        raise ValueError("Cannot trace whitespace other than spaces, tabs, and line feeds")
    text = strip(text)
    for match in BLOCK.finditer(text):
        kind, labels = match.group(1), re.findall(r'"([^"]*)"', match.group(2))
        if not all(LABEL.fullmatch(label) for label in labels):
            raise ValueError(f"Cannot trace {kind} labels {labels!r}")
        body = block_body(text, match.end())
        if kind == "moved":
            move = attribute(body, "from"), attribute(body, "to")
            if not all(move):
                raise ValueError("Cannot trace a moved block without from and to")
            moves.append(move)
            continue
        address = ".".join(labels) if kind == "resource" else f"module.{labels[0]}"
        for meta in ("count", "for_each"):
            if attribute(body, meta) is not None:
                raise ValueError(f"Cannot trace {address} with {meta}")
        for lifecycle in re.finditer(r"^\s*lifecycle\s*\{", body, re.M):
            if attribute(block_body(body, lifecycle.end()), "enabled") is not None:
                raise ValueError(f"Cannot trace {address} with lifecycle enabled")
        if kind == "resource":
            resources.add(address)
            continue
        source = (attribute(body, "source") or "").strip('"')
        if not SOURCE.fullmatch(source):
            raise ValueError(f"Cannot trace {address} with source {source.replace(INTERPOLATION, '${...}')!r}")
        calls[labels[0]] = source
    return resources, calls, moves


def managed_addresses(directory: Path, prefix: str = "") -> tuple[set[str], list[tuple[str, str]]]:
    """Return absolute resource addresses and moves for a root and every local module it calls."""
    unread = sorted(path.name for pattern in UNREAD for path in directory.glob(pattern))
    if unread:
        raise ValueError(f"Cannot trace {directory.name} with {', '.join(unread)}")
    names = sorted(path for path in directory.glob("*.tf") if path.is_file() and not path.name.startswith("."))
    text = "\n".join(path.read_bytes().decode() for path in names)
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
