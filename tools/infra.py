#!/usr/bin/env python3
"""Run one explicit deployment with isolated data, state, and saved plans."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

if __package__:
    from . import quality
else:
    import quality


ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
BACKEND_FIELDS = {
    "local": set(),
    "s3": {"bucket", "region", "encrypt", "use_lockfile", "profile", "allowed_account_ids", "kms_key_id"},
    "azurerm": {"resource_group_name", "storage_account_name", "container_name", "subscription_id",
                "tenant_id", "use_azuread_auth", "use_oidc", "use_cli"},
    "gcs": {"bucket", "impersonate_service_account"},
}


class UserError(Exception):
    """An actionable configuration or workflow error."""


def read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise UserError(f"Cannot read {path}: {error}") from error


def contained(root: Path, path: Path) -> Path:
    if not path.resolve().is_relative_to(root.resolve()):
        raise UserError(f"Path escapes the repository: {path}")
    relative = path.relative_to(root)
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise UserError(f"Symlinks are not supported in deployment paths: {cursor}")
    return path


def digest(paths: list[Path], root: Path) -> str:
    result = hashlib.sha256()
    for path in sorted(set(paths)):
        contained(root, path)
        result.update(str(path.relative_to(root)).encode() + b"\0")
        result.update(path.read_bytes() + b"\0")
    return result.hexdigest()


def source_files(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*") if p.is_file()
            and not any(part.startswith(".") for part in p.relative_to(directory).parts[:-1])
            and (p.suffix == ".tf" or p.name.endswith(".tf.json") or p.name == ".terraform.lock.hcl")]


@dataclass(frozen=True)
class Deployment:
    root: Path
    name: str

    def __post_init__(self):
        parts = self.name.split("/")
        if len(parts) != 4 or not all(SLUG.fullmatch(part) for part in parts):
            raise UserError("Use environment/cloud/group/stack, e.g. dev/aws/network/core")

    @property
    def environment(self) -> str:
        return self.name.split("/")[0]

    @property
    def is_bootstrap(self) -> bool:
        return self.name.split("/")[2] == "bootstrap"

    @property
    def stack(self) -> Path:
        return contained(self.root, self.root / "stacks" / self.name.split("/", 1)[1])

    @property
    def live(self) -> Path:
        return contained(self.root, self.root / "live" / self.name)

    @property
    def variables(self) -> Path:
        return self.live / "terraform.tfvars.json"

    @property
    def backend_type(self) -> str:
        config = read_json(contained(self.root, self.stack / "backend.tf.json"))
        try:
            backend = config["terraform"]["backend"]
            kind, = backend
            if kind not in BACKEND_FIELDS or backend[kind] != {}:
                raise ValueError("expected one supported, empty backend block")
            return kind
        except (KeyError, TypeError, ValueError) as error:
            raise UserError(f"Invalid partial backend in {self.stack / 'backend.tf.json'}") from error

    def backend(self) -> dict:
        kind = self.backend_type
        values = read_json(contained(self.root, self.live / "backend.json"))
        if not isinstance(values, dict) or set(values) - BACKEND_FIELDS[kind]:
            raise UserError(f"Unsupported backend fields in {self.live / 'backend.json'}; state paths are derived")
        if kind == "local":
            values["path"] = str(contained(self.root, self.root / ".infra/state" / self.name / "terraform.tfstate"))
        elif kind == "gcs":
            values["prefix"] = self.name
        else:
            values["key"] = f"{self.name}/terraform.tfstate"
        if kind == "s3" and (values.get("encrypt") is not True or values.get("use_lockfile") is not True):
            raise UserError("S3 backends must enable encrypt and use_lockfile")
        if kind == "azurerm" and values.get("use_azuread_auth") is not True:
            raise UserError("Azure backends must use Microsoft Entra authentication (use_azuread_auth=true)")
        return values

    def validate(self):
        for required in (self.stack / "main.tf", self.stack / "versions.tf", self.variables):
            if not contained(self.root, required).is_file():
                raise UserError(f"Missing required file: {required}")
        values = read_json(self.variables)
        if not isinstance(values, dict) or values.get("environment") != self.environment:
            raise UserError(f"environment in {self.variables} must equal {self.environment!r}")
        if list(self.live.rglob("*.tf")) or list(self.live.rglob("*.tf.json")):
            raise UserError(f"Live directories contain data only: {self.live}")
        if list(self.stack.glob("*.tfvars")) or list(self.stack.glob("*.tfvars.json")):
            raise UserError(f"Keep variable values in live/, not {self.stack}")
        self.backend()

    def fingerprint(self) -> str:
        policy = [self.root / name for name in ("mise.toml", ".tflint.hcl", "tools/quality.py")]
        return digest([self.variables, self.live / "backend.json", *source_files(self.stack),
                       *source_files(self.root / "modules"), *[p for p in policy if p.is_file()]], self.root)


def inventory(root: Path) -> list[Deployment]:
    return [Deployment(root, p.parent.relative_to(root / "live").as_posix())
            for p in sorted((root / "live").rglob("terraform.tfvars.json"))]


@contextmanager
def command_lock(root: Path, name: str):
    path = contained(root, root / ".infra/locks" / (hashlib.sha256(name.encode()).hexdigest() + ".lock"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise UserError(f"Another command is running for {name}; retry after it finishes") from error
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def engine_environment(data: Path) -> dict:
    if os.environ.get("TF_WORKSPACE", "default") != "default":
        raise UserError("Named workspaces are unsupported; select an explicit deployment instead")
    overrides = [key for key, value in os.environ.items()
                 if value and (key.startswith("TF_CLI_ARGS") or key.startswith("TF_VAR_"))]
    if overrides:
        raise UserError("Unset implicit input/flag overrides: " + ", ".join(sorted(overrides)))
    return {**os.environ, "TF_DATA_DIR": str(data), "TF_WORKSPACE": "default", "TF_IN_AUTOMATION": "1"}


class Runner:
    def __init__(self, deployment: Deployment, engine: str):
        if engine not in {"tofu", "terraform"}:
            raise UserError("TF_CLI must be tofu or terraform")
        self.deployment = deployment
        deployment.validate()
        self.engine = engine
        self.work = contained(deployment.root, deployment.root / ".infra" / engine / deployment.name)
        self.work.mkdir(parents=True, exist_ok=True)
        self.plan = self.work / "plan.tfplan"
        self.receipt = self.work / "plan.json"
        self.initialized = self.work / "initialized.json"

    def run(self, *arguments: str, check_data: bool = False, capture: bool = False, changes: bool = False):
        data = self.work / ("check-data" if check_data else "data")
        env = engine_environment(data)
        cache = contained(self.deployment.root, self.deployment.root / ".infra/provider-cache")
        cache.mkdir(parents=True, exist_ok=True)
        env["TF_PLUGIN_CACHE_DIR"] = str(cache)
        try:
            result = subprocess.run([self.engine, f"-chdir={self.deployment.stack}", *arguments],
                                    env=env, text=True, capture_output=capture, check=False)
        except FileNotFoundError as error:
            raise UserError(f"{self.engine} is not installed; run mise install") from error
        if result.returncode not in ({0, 2} if changes else {0}):
            if capture:
                print(result.stderr, file=sys.stderr)
            raise UserError(f"{self.engine} {arguments[0]} failed (exit {result.returncode})")
        return result

    def initialize(self, *arguments: str, check_data: bool = False):
        # Provider cache installation is the only shared write across deployments.
        with command_lock(self.deployment.root, "provider-cache"):
            return self.run("init", *arguments, check_data=check_data)

    def version(self) -> str:
        return json.loads(self.run("version", "-json", capture=True).stdout)["terraform_version"]

    def backend_identity(self) -> dict:
        return {"type": self.deployment.backend_type, "config": self.deployment.backend(), "engine": self.engine}

    def require_initialized(self):
        if not self.initialized.exists() or read_json(self.initialized) != self.backend_identity():
            raise UserError(f"Backend not initialized or configuration changed; run init {self.deployment.name}")

    def init(self):
        if "REPLACE_ME" in json.dumps(self.deployment.backend()):
            raise UserError(f"Configure the placeholder state storage in {self.deployment.live / 'backend.json'} first; see docs/cloud-setup.md")
        config = self.work / "backend.generated.hcl"
        config.write_text("".join(f"{key} = {json.dumps(value)}\n" for key, value in sorted(self.deployment.backend().items())))
        if self.deployment.backend_type == "local":
            Path(self.deployment.backend()["path"]).parent.mkdir(parents=True, exist_ok=True)
        self.initialize("-input=false", "-lockfile=readonly", f"-backend-config={config}")
        self.initialized.write_text(json.dumps(self.backend_identity(), indent=2) + "\n")

    def validate(self):
        self.initialize("-backend=false", "-input=false", "-lockfile=readonly", check_data=True)
        self.run("validate", check_data=True)

    def lock_providers(self, upgrade: bool):
        with command_lock(self.deployment.root, str(self.deployment.stack)):
            args = ["-backend=false", "-input=false"]
            if upgrade:
                args.append("-upgrade")
            self.initialize(*args, check_data=True)

    def test(self):
        self.initialize("-backend=false", "-input=false", "-lockfile=readonly", check_data=True)
        self.run("test", f"-var-file={self.deployment.variables}", check_data=True)

    def lint(self):
        engine_environment(self.work / "check-data")
        with command_lock(self.deployment.root, "tflint-plugins"):
            quality.lint(self.deployment.root, self.deployment.stack, self.deployment.variables,
                         self.deployment.name.split("/")[1])

    def security(self, saved_plan: bool = False):
        engine_environment(self.work / "check-data")
        quality.security(self.deployment.root, self.deployment.stack, self.deployment.variables,
                         plan=self.plan if saved_plan else None)

    def state(self, address: str | None = None):
        self.require_initialized()
        if address is None:
            return self.run("state", "list")
        if not address.strip() or address.startswith("-"):
            raise UserError("state-show requires a resource address, not a flag")
        return self.run("state", "show", "-no-color", address)

    def make_plan(self, destroy: bool):
        self.require_initialized()
        self.plan.unlink(missing_ok=True)
        self.receipt.unlink(missing_ok=True)
        before = self.deployment.fingerprint()
        args = ["plan", "-input=false", "-lock-timeout=60s", "-detailed-exitcode",
                f"-var-file={self.deployment.variables}", f"-out={self.plan}"]
        if destroy:
            args.append("-destroy")
        try:
            result = self.run(*args, changes=True)
            plan_hash = hashlib.sha256(self.plan.read_bytes()).hexdigest()
            self.security(saved_plan=True)
            if hashlib.sha256(self.plan.read_bytes()).hexdigest() != plan_hash:
                raise UserError("Saved plan changed during its security scan; plan again")
            if self.deployment.fingerprint() != before:
                raise UserError("Configuration changed while planning; generate a fresh plan")
            receipt = {"deployment": self.deployment.name, "engine": self.engine, "version": self.version(),
                       "fingerprint": before, "plan_sha256": plan_hash,
                       "destroy": destroy, "changes": result.returncode == 2}
            self.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
        except (UserError, quality.QualityError, OSError, KeyboardInterrupt):
            self.plan.unlink(missing_ok=True)
            self.receipt.unlink(missing_ok=True)
            raise

    def verify_plan(self):
        self.require_initialized()
        if not self.plan.is_file() or not self.receipt.is_file():
            raise UserError("No saved plan; run plan for this deployment first")
        receipt = read_json(self.receipt)
        if not isinstance(receipt, dict):
            raise UserError("Invalid plan receipt; generate a fresh plan")
        expected = {"deployment": self.deployment.name, "engine": self.engine, "version": self.version(),
                    "fingerprint": self.deployment.fingerprint(),
                    "plan_sha256": hashlib.sha256(self.plan.read_bytes()).hexdigest()}
        if any(receipt.get(key) != value for key, value in expected.items()):
            raise UserError("Saved plan no longer matches the deployment, inputs, engine, or source; plan again")

    def apply(self, yes: bool):
        self.verify_plan()
        if not yes and input(f"Type {self.deployment.name} to apply this saved plan: ") != self.deployment.name:
            raise UserError("Apply cancelled")
        self.verify_plan()
        self.security(saved_plan=True)
        self.verify_plan()
        try:
            self.run("apply", "-input=false", "-lock-timeout=60s", str(self.plan))
        finally:
            self.plan.unlink(missing_ok=True)
            self.receipt.unlink(missing_ok=True)


def scaffold(root: Path, name: str, source: str):
    target, original = Deployment(root, name), Deployment(root, source)
    original.validate()
    if name.split("/")[1] != source.split("/")[1]:
        raise UserError("A new deployment must use the source cloud; choose that cloud's example")
    if target.live.exists():
        raise UserError(f"Deployment already exists; nothing overwritten: {name}")
    if target.stack.exists() and target.stack != original.stack:
        raise UserError("Target stack already exists; use a source deployment of that same stack")
    variables = read_json(original.variables)
    variables["environment"] = target.environment
    variables["name"] = name.split("/")[-1]
    created_stack = not target.stack.exists()
    try:
        if created_stack:
            shutil.copytree(original.stack, target.stack, ignore=shutil.ignore_patterns(".terraform", "__pycache__", "*.tfstate*", "*.tfplan"))
        target.live.mkdir(parents=True)
        shutil.copyfile(original.live / "backend.json", target.live / "backend.json")
        target.variables.write_text(json.dumps(variables, indent=2) + "\n")
        target.validate()
    except Exception:
        if target.live.exists():
            shutil.rmtree(target.live)
        if created_stack and target.stack.exists():
            shutil.rmtree(target.stack)
        raise
    print(f"Created {name}. Review {target.variables.relative_to(root)} and backend.json before initializing.")


def check(root: Path, engine: str):
    subprocess.run([sys.executable, str(root / "tools/check_layout.py")], cwd=root, check=True)
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root, check=True)
    subprocess.run([engine, "fmt", "-check", "-recursive", "modules"], cwd=root, check=True)
    subprocess.run([engine, "fmt", "-check", "-recursive", "stacks"], cwd=root, check=True)
    validated = set()
    for deployment in inventory(root):
        with command_lock(root, deployment.name):
            runner = Runner(deployment, engine)
            if deployment.stack not in validated:
                runner.validate()
                validated.add(deployment.stack)
            runner.lint()
            runner.security()
            runner.test()


def main(argv=None, root: Path = ROOT):
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=["tofu", "terraform"], default=os.environ.get("TF_CLI", "tofu"))
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("list", "check", "fmt"):
        commands.add_parser(command)
    for command in ("show", "init", "validate", "test", "lint", "security", "lock", "plan", "apply", "output", "state-list", "state-show"):
        sub = commands.add_parser(command)
        sub.add_argument("deployment")
        if command == "plan":
            sub.add_argument("--destroy", action="store_true", help="save a destroy plan for later review and apply")
        if command == "apply":
            sub.add_argument("--yes", action="store_true", help="apply the verified saved plan without a prompt")
        if command == "lock":
            sub.add_argument("--upgrade", action="store_true", help="resolve newer versions allowed by constraints")
        if command == "security":
            sub.add_argument("--plan", action="store_true", help="verify and scan this deployment's saved plan")
        if command == "state-show":
            sub.add_argument("address")
    bootstrap = commands.add_parser("bootstrap", help="explicitly manage a cloud's state storage using local state")
    bootstrap.add_argument("action", choices=["init", "plan", "apply", "output"])
    bootstrap.add_argument("deployment")
    bootstrap.add_argument("--yes", action="store_true", help="skip the bootstrap apply prompt")
    new = commands.add_parser("new", help="copy a deployment's code/data without overwriting existing files")
    new.add_argument("deployment")
    new.add_argument("--from", dest="source", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            for deployment in inventory(root):
                deployment.validate()
                print(deployment.name)
        elif args.command == "new":
            with command_lock(root, "scaffold"):
                scaffold(root, args.deployment, args.source)
        elif args.command == "check":
            check(root, args.engine)
        elif args.command == "fmt":
            for directory in ("modules", "stacks"):
                subprocess.run([args.engine, "fmt", "-recursive", directory], cwd=root, check=True)
        else:
            deployment = Deployment(root, args.deployment)
            deployment.validate()
            if args.command == "bootstrap":
                if not deployment.is_bootstrap or deployment.backend_type != "local":
                    raise UserError("bootstrap requires a bootstrap stack with a local backend")
                if args.yes and args.action != "apply":
                    raise UserError("--yes is only valid for bootstrap apply")
                args.command = args.action
                args.destroy = False
            elif deployment.is_bootstrap and args.command in {"init", "plan", "apply"}:
                raise UserError(f"Use bootstrap {args.command} {deployment.name} to manage state storage explicitly")
            if args.command == "show":
                print(json.dumps({"deployment": deployment.name, "stack": str(deployment.stack.relative_to(root)),
                                  "live": str(deployment.live.relative_to(root)), "backend": deployment.backend_type,
                                  "state": deployment.backend().get("key", deployment.backend().get("prefix", deployment.backend().get("path")))}, indent=2))
                return 0
            with command_lock(root, deployment.name):
                runner = Runner(deployment, args.engine)
                if args.command == "plan":
                    runner.make_plan(args.destroy)
                elif args.command == "apply":
                    runner.apply(args.yes)
                elif args.command == "lock":
                    runner.lock_providers(args.upgrade)
                elif args.command == "security":
                    if args.plan:
                        runner.verify_plan()
                    runner.security(saved_plan=args.plan)
                elif args.command in {"state-list", "state-show"}:
                    runner.state(args.address if args.command == "state-show" else None)
                elif args.command == "output":
                    runner.require_initialized()
                    if getattr(args, "action", None) == "output":
                        runner.run("output", "-json", "backend_config")
                    else:
                        runner.run("output")
                else:
                    getattr(runner, args.command)()
        return 0
    except (UserError, quality.QualityError, OSError, subprocess.CalledProcessError, EOFError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
