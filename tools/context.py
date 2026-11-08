#!/usr/bin/env python3
"""Select a deployment context and turn recipe targets into native roots.

`use` points `.env` at one `.env.<name>` file. `root` writes what a target will touch
to stderr and the root directory to stdout, for a recipe to pass to `tofu -chdir`.
It never runs init, plan, or apply.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from preflight import preflight

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("DEPLOY_ENV", "DEPLOY_CLOUD")
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
# just expands variables, escapes, and inline comments; this reader does not, so it refuses them.
NOT_PLAIN = re.compile(r"[$\\]|\s#")
CREDENTIALS = {"aws": ("AWS_PROFILE", "AWS_REGION"), "azure": ("AZURE_CONFIG_DIR",),
               "gcp": ("CLOUDSDK_ACTIVE_CONFIG_NAME",), "local": ()}
STATE = {"local": "path", "s3": "key", "azurerm": "key", "gcs": "prefix"}
LOCATION = {"s3": ("bucket", "region"), "azurerm": ("storage_account_name", "container_name"),
            "gcs": ("bucket",)}
USAGE = """usage: context.py use [NAME]
       context.py root [--check] <group> <stack>
       context.py root [--check] <environment>/<cloud>/<group>/<stack>"""


class ContextError(Exception):
    pass


def read(path):
    values = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            key, _, value = line.removeprefix("export ").partition("=")
            if NOT_PLAIN.search(value):
                raise ContextError(f"{path.name}: write {key.strip()} as a plain value, "
                                   "without $, \\, or a trailing comment")
            values[key.strip()] = value.strip().strip("'\"")
    if missing := [key for key in KEYS if not values.get(key)]:
        raise ContextError(f"{path.name} does not set {', '.join(missing)}")
    if placeholders := [key for key, value in values.items() if "REPLACE_ME" in value]:
        raise ContextError(f"{path.name} still has a placeholder in {', '.join(placeholders)}")
    selected = (values["DEPLOY_ENV"], values["DEPLOY_CLOUD"])
    if not all(NAME.fullmatch(part) for part in selected) or not (ROOT / "live").joinpath(*selected).is_dir():
        raise ContextError(f"{path.name} selects live/{'/'.join(selected)}, which does not exist")
    return values


def available():
    return sorted(path.name.removeprefix(".env.") for path in ROOT.glob(".env.*")
                  if path.is_file() and not path.name.endswith(".example"))


def use(name):
    names = available()
    if not name and names:
        print("Available contexts:")
        for number, choice in enumerate(names, 1):
            print(f"  {number}) {choice}")
        try:
            name = input("Select context: ").strip()
        except EOFError:
            raise ContextError("no context selected") from None
        if name.isdigit() and 0 < int(name) <= len(names):
            name = names[int(name) - 1]
    if name not in names:
        example = ROOT / f".env.{name}.example"
        examples = [example] if example.is_file() else sorted(ROOT.glob(".env.*.example"))
        if names:
            hint = f"Available: {', '.join(names)}"
        elif examples:
            hint = f"Create one from an example: `cp {examples[0].name} {examples[0].stem}`"
        else:
            hint = "Create a .env.<name> file"
        raise ContextError(f"no context named {name or '(none)'}. {hint}")
    link = ROOT / ".env"
    if link.exists() and not link.is_symlink():
        raise ContextError(".env is a regular file. Rename it to .env.<name> so `just use` can select it")
    read(ROOT / f".env.{name}")
    link.unlink(missing_ok=True)
    link.symlink_to(f".env.{name}")
    return f".env.{name}"


def selected():
    link = ROOT / ".env"
    if link.is_symlink():
        target = ROOT / os.readlink(link)
        if not target.is_file():
            raise ContextError(f"the selected context {os.readlink(link)} no longer exists. Run `just use`")
        return target.name, read(target)
    if link.exists():
        return ".env (not a context)", None
    if inherited := next((parent / ".env" for parent in ROOT.parents if (parent / ".env").exists()), None):
        raise ContextError(f"this repository has no .env, so just loads {inherited} instead. "
                           "Run `just use`, or move that file")
    return None, None


def resolve(target, context):
    name, values = context
    if len(target) == 2 and values is None:
        raise ContextError("give <environment>/<cloud>/<group>/<stack>, "
                           "or select a context with `just use` to give <group> <stack>")
    if len(target) == 2:
        parts = (values["DEPLOY_ENV"], values["DEPLOY_CLOUD"], *target)
    elif len(target) == 1:
        parts = tuple(target[0].strip("/").split("/"))
    else:
        raise ContextError(USAGE)
    deployment = "/".join(parts)
    if len(parts) != 4 or not all(NAME.fullmatch(part) for part in parts):
        raise ContextError(f"{deployment} is not <environment>/<cloud>/<group>/<stack>")
    if not (ROOT / "live" / deployment / "terraform.tfvars.json").is_file():
        raise ContextError(f"no root at live/{deployment}")
    if values and parts[:2] != (values["DEPLOY_ENV"], values["DEPLOY_CLOUD"]):
        raise ContextError(f"{deployment} is in {parts[0]}/{parts[1]}, but {name} selects "
                           f"{values['DEPLOY_ENV']}/{values['DEPLOY_CLOUD']}. Run `just use` to switch")
    return deployment


def apply_credentials(context):
    """Use the context's credential settings, and refuse ones the shell already overrides."""
    name, values = context
    for key, value in (values or {}).items():
        if key not in KEYS and (active := os.environ.setdefault(key, value)) != value:
            raise ContextError(f"this shell sets {key}={active}, but {name} sets {key}={value}. "
                               "Run `direnv reload` or start a new shell")


def tofu_version():
    if shutil.which("tofu") is None:
        return "not installed"
    result = subprocess.run(["tofu", "version"], capture_output=True, text=True, timeout=60)
    return result.stdout.splitlines()[0] if result.returncode == 0 and result.stdout else "unknown"


def summary(deployment, context):
    cloud, group, stack = deployment.split("/")[1:]
    root = Path("live", deployment)
    text = (ROOT / root / "backend.tf").read_text()
    kind = re.search(r'backend\s+"([^"]+)"', text)[1]
    attributes = dict(re.findall(r'^\s*(\w+)\s*=\s*"([^"]*)"', text, re.M))
    state = attributes.get(STATE.get(kind, ""), "unknown")
    if kind == "local":
        state = os.path.normpath(root / state)
    elif kind == "gcs":
        state = f"{state}/default.tfstate"
    location = ", ".join(f"{key} {attributes[key]}" for key in LOCATION.get(kind, ()) if key in attributes)
    data = Path(os.environ.get("TF_DATA_DIR") or ".terraform")
    credentials = ", ".join(f"{key}={os.environ[key]}" if os.environ.get(key) else f"{key} unset"
                            for key in CREDENTIALS.get(cloud, ())) or "none needed"
    return [
        ("Env file", context[0] or "none"),
        ("Environment", deployment.split("/")[0]),
        ("Cloud", cloud),
        ("Credentials", credentials),
        ("OpenTofu", tofu_version()),
        ("Stack", f"stacks/{cloud}/{group}/{stack}"),
        ("Root", str(root)),
        ("Backend", f"{kind} ({location})" if location else kind),
        ("State", state),
        ("TF data dir", str(data if data.is_absolute() else root / data)),
    ]


def root(arguments):
    check = arguments[:1] == ["--check"]
    context = selected()
    deployment = resolve(arguments[1:] if check else arguments, context)
    apply_credentials(context)
    rows = summary(deployment, context)
    ok = True
    if check:
        lines, ok = preflight(deployment)
        rows += [("Identity", line.removeprefix(f"{deployment}: ")) for line in lines]
    print("\nContext", file=sys.stderr)
    for label, value in rows:
        print(f"  {label:<12}: {value}", file=sys.stderr)
    print(file=sys.stderr)
    if not ok:
        raise ContextError(f"live/{deployment} failed the preflight check")
    return f"live/{deployment}"


def main(arguments):
    try:
        if arguments[:1] == ["use"] and len(arguments) <= 2:
            name = use(arguments[1] if len(arguments) == 2 else "")
            print(f"Selected {name}. Recipes use it now. For native tofu commands in this shell, "
                  "run `direnv reload` or start a new shell.")
            return 0
        if arguments[:1] == ["root"]:
            print(root(arguments[1:]))
            return 0
    except ContextError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
