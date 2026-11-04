# Security

## Report a vulnerability

Use the repository's **Security → Report a vulnerability** feature when enabled.
If it is unavailable, contact a maintainer through a private channel listed on
their profile before sharing sensitive details. Do not include credentials,
state files, saved plans, or exploit details in a public issue.

Maintainers should enable private vulnerability reporting before publication.
Until release support windows are defined, fixes target the default branch;
there is no support or response-time SLA.

## Scope and responsibilities

The template isolates deployment paths, backend metadata, command locks, and
saved plans. It rejects stale or swapped plans and keeps generated material under
ignored `.infra/`. These controls protect against mistakes by operators; they do
not defend against a compromised checkout, CLI executable, workstation, or cloud
identity. A plan receipt is not a signed approval.

Cloud credentials belong in supported identity mechanisms, preferably short-lived
SSO, role assumption, or workload identity federation. Restrict both workload and
state permissions. A remote state's access policy is a security boundary, whereas
an environment name or state prefix alone is not.

State and plans can contain secrets even when input/output values are marked
`sensitive`. Do not commit or publish them, print raw state in CI, or upload plans
as broadly accessible artifacts. Readonly CI never needs cloud credentials.

Bundled cloud tests use mocked providers; they do not audit a cloud account or
establish production compliance. Operators must configure organization-specific
policies, logging, key management, backups, and recovery procedures.

TFLint and Trivy run locally and in CI. Trivy blocks HIGH/CRITICAL source and
saved-plan misconfigurations; `apply --yes` cannot bypass the saved-plan gate.
Raw scan reports stay in memory. Gitleaks checks secrets independently.
See [quality checks](docs/quality.md) for the exact scope and failure behavior.

`state-show` is read-only but its output can reveal sensitive resource attributes.
Use it in an authorized terminal rather than public CI logs. Bootstrap state is
local and requires a secure independent backup; see [bootstrap](docs/bootstrap.md).
