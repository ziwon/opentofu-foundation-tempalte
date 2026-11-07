set positional-arguments

default:
    @just --list

init deployment:
    tofu -chdir="live/$1" init

preflight deployment:
    python3 tools/preflight.py "$1"

plan deployment:
    tofu -chdir="live/$1" plan -out=plan.tfplan

destroy-plan deployment:
    tofu -chdir="live/$1" plan -destroy -out=plan.tfplan

cost deployment:
    umask 077 && mkdir -p ".infra/cost/$1" && tofu -chdir="live/$1" show -json plan.tfplan > ".infra/cost/$1/plan.json"
    infracost breakdown --path ".infra/cost/$1/plan.json"

apply deployment:
    tofu -chdir="live/$1" apply plan.tfplan

output deployment:
    tofu -chdir="live/$1" output

state-list deployment:
    tofu -chdir="live/$1" state list

state-show deployment address:
    tofu -chdir="live/$1" state show "$2"

validate deployment:
    tofu -chdir="live/$1" validate

test deployment:
    tofu -chdir="live/$1" test

lock deployment:
    tofu -chdir="live/$1" providers lock -platform=linux_amd64 -platform=darwin_arm64

fmt:
    tofu fmt -recursive

check:
    python3 tools/check.py

secrets:
    gitleaks dir . --redact --no-banner
