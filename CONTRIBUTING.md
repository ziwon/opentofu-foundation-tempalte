# Contributing

Use OpenTofu and the development tools pinned in `mise.toml`. Repository checks
use Python 3.10 or later and its standard library. Native deployment commands need
only OpenTofu and the selected cloud's authentication prerequisites.
Start with the local catalog so contributions do not need a cloud account.

```sh
mise trust
mise install
mise exec -- python3 tools/check.py
mise exec -- python3 tools/smoke.py
mise exec -- python3 tools/quality_smoke.py
mise exec -- gitleaks dir . --redact --no-banner
```

Keep a PR focused on one behavior or capability. Describe the problem, resulting
behavior, validation, and deployment impact. Include migration steps for resource
addresses, state locations, provider sources, or backend changes.

Each `live/<environment>/<cloud>/<group>/<stack>` directory is an executable root.
Keep its provider configuration, backend, values, and lock file together. Put the
root's resources in its stack under `stacks/<cloud>/<group>/<stack>`, and put
building blocks that several stacks share in core modules under `modules/`. Stacks
and modules configure no providers or backends. Keep ordinary
`tofu init`, `plan`, `apply`, `output`, and `state` usable without repository Python.
Do not add an implicit active environment or credentials in live values.

Update tests for behavior that users rely on. Cloud tests use mocked providers
and plan-only runs. Security fixtures may create plans with fake credentials and
identity probes disabled, but must never apply cloud resources. Lifecycle fixtures
may apply and destroy only local `terraform_data` resources in disposable directories.

Update provider constraints and locks deliberately. Preserve registry identities
when changing layout. Review provider migration notes before changing versions.
Do not remove security or behavior checks to make a change pass.

Review the code rather than the person. Report sensitive vulnerabilities through
the private process in [SECURITY.md](SECURITY.md).
