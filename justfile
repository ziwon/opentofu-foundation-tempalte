set positional-arguments
set dotenv-load

# Root recipes take <group> <stack> after `just use` selects a context,
# or <environment>/<cloud>/<group>/<stack> without one.

default:
    @just --list

[group('context')]
use name="":
    @python3 tools/context.py use "$1"

[group('context')]
preflight +target:
    @python3 tools/context.py root --check "$@" > /dev/null

[group('opentofu')]
init +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" init

[group('opentofu')]
validate +target:
    @root=$(python3 tools/context.py root "$@") && tofu -chdir="$root" validate

[group('opentofu')]
test +target:
    @root=$(python3 tools/context.py root "$@") && tofu -chdir="$root" test

[group('opentofu')]
plan +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" plan -out=plan.tfplan

[group('opentofu')]
destroy-plan +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" plan -destroy -out=plan.tfplan

[group('opentofu')]
apply +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" apply plan.tfplan

[group('opentofu')]
output +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" output

[group('opentofu')]
lock +target:
    @root=$(python3 tools/context.py root "$@") && tofu -chdir="$root" providers lock -platform=linux_amd64 -platform=darwin_arm64

[group('opentofu')]
cost +target:
    #!/usr/bin/env bash
    set -euo pipefail
    root=$(python3 tools/context.py root "$@")
    report=".infra/cost/${root#live/}"
    umask 077
    mkdir -p "$report"
    tofu -chdir="$root" show -json plan.tfplan > "$report/plan.json"
    infracost breakdown --path "$report/plan.json"

[group('state')]
state-list +target:
    @root=$(python3 tools/context.py root --check "$@") && tofu -chdir="$root" state list

# The address comes last: `just state-show network core 'module.stack.aws_vpc.this'`.
[group('state')]
state-show +target_and_address:
    #!/usr/bin/env bash
    set -euo pipefail
    root=$(python3 tools/context.py root --check "${@:1:$#-1}")
    tofu -chdir="$root" state show "${@: -1}"

[group('quality')]
fmt:
    tofu fmt -recursive

[group('quality')]
check:
    python3 tools/check.py

[group('quality')]
secrets:
    gitleaks dir . --redact --no-banner
