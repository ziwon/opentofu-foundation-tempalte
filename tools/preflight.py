#!/usr/bin/env python3
"""Check that the active cloud CLI identity matches a root's inputs. Reads only; never runs tofu."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDERS = {"000000000000", "00000000-0000-0000-0000-000000000000", "example-project"}
EXPECTED = {
    "aws": {"AWS account": "aws_account_id", "AWS region": "region"},
    "azure": {"Azure subscription": "subscription_id"},
    "gcp": {"GCP project": "project_id"},
}


class PreflightError(Exception):
    pass


def cli(*args, login=None):
    if shutil.which(args[0]) is None:
        raise PreflightError(f"the {args[0]} CLI is not installed")
    timeout = float(os.environ.get("PREFLIGHT_TIMEOUT_SECONDS") or 30)
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise PreflightError(f"`{' '.join(args)}` did not answer within {timeout:g} seconds") from None
    if login and result.returncode:
        raise PreflightError(f"`{' '.join(args)}` failed with exit code {result.returncode}. "
                             f"Check that {args[0]} works and that you are logged in, for example with `{login}`")
    return result.stdout.strip()


def aws():
    identity = json.loads(cli("aws", "sts", "get-caller-identity", "--output", "json", login="aws sso login"))
    region = (os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
              or cli("aws", "configure", "get", "region"))
    return {"AWS account": identity["Account"], "AWS region": region, "caller": identity["Arn"]}


def azure():
    account = json.loads(cli("az", "account", "show", "--output", "json", login="az login"))
    return {"Azure subscription": account["id"], "caller": account["user"]["name"]}


def gcp():
    accounts = json.loads(cli("gcloud", "auth", "list", "--format=json", login="gcloud auth login"))
    active = [account["account"] for account in accounts if account["status"] == "ACTIVE"]
    if not active:
        raise PreflightError("gcloud has no active account. Log in, for example with `gcloud auth login`")
    return {"GCP project": cli("gcloud", "config", "get-value", "project", login="gcloud auth login"),
            "caller": active[0]}


ACTIVE = {"aws": aws, "azure": azure, "gcp": gcp}


def placeholder(value):
    return isinstance(value, str) and ("REPLACE_ME" in value or value in PLACEHOLDERS)


def leaves(value, path):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, f"{path}.{key}" if path else key)
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item, path)
    else:
        yield path, value


def unconfigured(directory, values, keys):
    found = [f"terraform.tfvars.json has no {key}" for key in keys if key not in values]
    found += [f"terraform.tfvars.json {path} is {item}" for path, item in leaves(values, "") if placeholder(item)]
    for line in (directory / "backend.tf").read_text().splitlines():
        if attribute := re.match(r"\s*(\w+)\s*=(.*)", line):
            found += [f"backend.tf {attribute[1]} is {item}"
                      for item in re.findall(r'"([^"]*)"', attribute[2]) if placeholder(item)]
    return found


def preflight(deployment):
    """Return the lines to report and whether the root matches the active identity."""
    parts = Path(deployment).parts
    directory = ROOT / "live" / deployment
    if len(parts) != 4 or ".." in parts or not (directory / "terraform.tfvars.json").is_file():
        return [f"{deployment}: no root at live/{deployment}"], False
    cloud = parts[1]
    if cloud == "local":
        return [f"{deployment}: local root, nothing to check"], True
    if cloud not in EXPECTED:
        return [f"{deployment}: preflight does not support the {cloud} cloud"], False
    for name in ("terraform.tfvars.json", "backend.tf"):
        if not (directory / name).is_file():
            return [f"{deployment}: {name} is missing"], False
    try:
        values = json.loads((directory / "terraform.tfvars.json").read_text())
    except ValueError:
        return [f"{deployment}: terraform.tfvars.json is not valid JSON"], False
    if missing := unconfigured(directory, values, EXPECTED[cloud].values()):
        return [f"{deployment} is not configured: {item}" for item in missing], False
    try:
        active = ACTIVE[cloud]()
    except PreflightError as error:
        return [f"{deployment}: {error}"], False
    except (ValueError, KeyError, TypeError):
        return [f"{deployment}: cannot read the identity the {cloud} CLI reported"], False
    expected = {label: values[key] for label, key in EXPECTED[cloud].items()}
    mismatches = [f"{deployment}: the active {label} is {active[label] or 'unset'}, but the root expects {value}"
                  for label, value in expected.items() if active[label] != value]
    if mismatches:
        return mismatches, False
    matches = ", ".join(f"{label} {value}" for label, value in expected.items())
    return [f"{deployment}: matches {matches} as {active['caller']}"], True


def main(arguments):
    if len(arguments) != 1:
        print("usage: preflight.py <environment>/<cloud>/<group>/<stack>", file=sys.stderr)
        return 2
    lines, ok = preflight(arguments[0].strip("/"))
    for line in lines:
        print(line if ok else f"error: {line}", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
