# Contributing

Use Python 3.10+ and the tool versions in `mise.toml`. Runtime tooling uses only
the Python standard library. Start with the local catalog example so contributions
do not need a cloud account.

```sh
mise trust
mise install
mise exec -- python3 tools/infra.py check
mise exec -- python3 tools/infra.py --engine terraform check
mise exec -- python3 tools/smoke.py --engine tofu
mise exec -- python3 tools/smoke.py --engine terraform
mise exec -- python3 tools/quality_smoke.py --engine tofu
mise exec -- python3 tools/quality_smoke.py --engine terraform
mise exec -- gitleaks dir . --redact --no-banner
```

Keep a PR focused on one behavior or capability. Describe the problem, resulting
behavior, validation, and deployment impact. Include migration steps for changes
to resource addresses, state layout, provider sources, or backend configuration.

Maintain the `modules/`, `stacks/`, and `live/` boundaries. Use explicit deployment
paths, native provider authentication, isolated working data, and reviewed saved
plans. Do not add an implicit active environment or store credentials in live data.

Update tests for behavior that users rely on. Cloud tests must stay credential-free
and use mocked providers with plan-only runs. Security fixtures may also use fake
credentials with all identity/metadata probes disabled to create plans, never apply.
The separate lifecycle smoke test may create
and destroy only local `terraform_data` resources in its temporary directory.

For dependency changes, update constraints and committed lock files deliberately.
Review major-version migration notes and any separately pinned runtime artifacts.
Do not remove checks simply to make an upgrade pass.

Please communicate respectfully, explain assumptions, and review the code rather
than the person. Report sensitive vulnerabilities through the private process
described in [SECURITY.md](SECURITY.md).
