#!/usr/bin/env python3
"""Validate real Atlantis configuration and its configured security commands without cloud apply."""

import os
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import time
from urllib.error import URLError
from urllib.request import urlopen

from atlantis import ROOT, EXAMPLE, configuration, write_configuration
from quality_smoke import smoke as security_smoke

INTEGRATION = ROOT / "integrations/atlantis"


def check_server(directory: Path):
    for name in ("server.yaml", "repos.yaml"):
        text = (INTEGRATION / f"{name}.example").read_text()
        text = text.replace("github.com/REPLACE_OWNER/REPLACE_REPOSITORY", "github.com/local/fixture")
        text = text.replace("/etc/atlantis/repos.yaml", str(directory / "repos.yaml"))
        (directory / name).write_text(text)
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    with (directory / "server.log").open("w+") as log:
        process = subprocess.Popen([
            "atlantis", "server", "--config", str(directory / "server.yaml"),
            "--repo-config", str(directory / "repos.yaml"),
            "--data-dir", str(directory / "server-data"), "--port", str(port),
            "--gh-hostname", "127.0.0.1:9", "--gh-user", "local-test-bot",
            "--gh-token", "local-test-token", "--gh-webhook-secret", "local-test-secret",
        ], stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    with urlopen(f"http://127.0.0.1:{port}/healthz", timeout=1) as response:
                        if response.status == 200:
                            print("Atlantis accepted the server and workflow examples and returned a healthy response.", flush=True)
                            return
                except (URLError, TimeoutError):
                    time.sleep(0.1)
            log.seek(0)
            raise RuntimeError(f"Atlantis server did not become healthy:\n{log.read()}")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def configured_policy_commands(directory, plan, env, succeeds):
    workflow = (INTEGRATION / "repos.yaml.example").read_text()
    planning, applying = workflow.split("    plan:\n", 1)[1].split("    apply:\n", 1)
    for stage in (planning, applying):
        commands = re.findall(r'^\s*- run: (.+)$', stage, re.MULTILINE)
        if not any('"$PLANFILE"' in command for command in commands):
            raise AssertionError("The configured stage must scan Atlantis's saved plan")
        passed = True
        for command in commands:
            result = subprocess.run(command, shell=True, cwd=directory,
                                    env={**env, "PLANFILE": str(plan), "COMMENT_ARGS": ""},
                                    text=True, capture_output=True, check=False)
            if result.returncode:
                passed = False
                if succeeds:
                    raise AssertionError(f"Configured policy command failed: {command}\n{result.stdout}\n{result.stderr}")
                break
        if passed != succeeds:
            raise AssertionError("The configured security stage accepted an unsafe source or saved plan")
    print(f"Configured policy commands {'accepted safe' if succeeds else 'rejected unsafe'} source/plan fixture.", flush=True)


def main():
    os.umask(0o077)
    version = re.search(r'"aqua:runatlantis/atlantis"\s*=\s*"([^"]+)"', (INTEGRATION / "mise.toml").read_text()).group(1)
    installed = subprocess.run(["atlantis", "version"], capture_output=True, text=True, check=True).stdout.strip()
    if not installed.startswith(f"atlantis {version} "):
        raise RuntimeError(f"Expected Atlantis {version}, found {installed}")
    write_configuration(configuration(ROOT), ROOT / EXAMPLE, check=True)
    with tempfile.TemporaryDirectory(prefix="atlantis native configuration ") as temporary:
        check_server(Path(temporary))
    security_smoke(configured_policy_commands)
    print("Atlantis server configuration and exact configured security commands passed. Hosted events and cloud apply were not exercised.")


if __name__ == "__main__":
    main()
