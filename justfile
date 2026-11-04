set positional-arguments

default:
    @just --list

list:
    @python3 tools/infra.py list

show deployment:
    @python3 tools/infra.py show "$1"

init deployment:
    @python3 tools/infra.py init "$1"

plan deployment:
    @python3 tools/infra.py plan "$1"

destroy-plan deployment:
    @python3 tools/infra.py plan "$1" --destroy

apply deployment:
    @python3 tools/infra.py apply "$1"

output deployment:
    @python3 tools/infra.py output "$1"

state-list deployment:
    @python3 tools/infra.py state-list "$1"

state-show deployment address:
    @python3 tools/infra.py state-show "$1" "$2"

lint deployment:
    @python3 tools/infra.py lint "$1"

security deployment:
    @python3 tools/infra.py security "$1"

security-plan deployment:
    @python3 tools/infra.py security "$1" --plan

bootstrap-init deployment:
    @python3 tools/infra.py bootstrap init "$1"

bootstrap-plan deployment:
    @python3 tools/infra.py bootstrap plan "$1"

bootstrap-apply deployment:
    @python3 tools/infra.py bootstrap apply "$1"

bootstrap-output deployment:
    @python3 tools/infra.py bootstrap output "$1"

validate deployment:
    @python3 tools/infra.py validate "$1"

test deployment:
    @python3 tools/infra.py test "$1"

new deployment source:
    @python3 tools/infra.py new "$1" --from "$2"

lock deployment:
    @python3 tools/infra.py lock "$1"

fmt:
    @python3 tools/infra.py fmt

check:
    @python3 tools/infra.py check

smoke:
    @python3 tools/smoke.py

secrets:
    @gitleaks dir . --redact --no-banner
