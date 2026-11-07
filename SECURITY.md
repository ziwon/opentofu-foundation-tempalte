# Security

## Report a vulnerability

Use the repository's **Security** tab and **Report a vulnerability** action when enabled.
Otherwise, contact a maintainer through a private channel listed on their profile.
Do not share credentials, state, saved plans, or exploit details in a public issue.

Maintainers should enable private vulnerability reporting before publication.
Until release support windows are defined, fixes target the default branch.
There is no support or response-time SLA.

## Deployment policy

Each native OpenTofu root has an explicit backend and independent state. Native
backend locking and saved-plan state checks still apply. Local commands do not
verify checkout fingerprints, create plan receipts, scan automatically, or ask
for an exact deployment name. Applying a saved plan has no interactive confirmation.
These changes remove the previous repository runner's local enforcement.

Use trusted automation for enforced source and saved-plan scans, deployment
approvals, and restrictions on untrusted code. The Atlantis example combines
native commands with quality checks and server-owned apply requirements.
A scan or approval does not protect against a compromised workstation, provider,
CLI, server, checkout, or cloud identity.

Cloud credentials belong in supported identity mechanisms, preferably short-lived
SSO, role assumption, or workload identity federation. Restrict workload and state
permissions independently. A state access policy is a security boundary.
An environment name or state prefix alone is not.

State and saved plans can contain secrets even when values are marked `sensitive`.
Keep them out of Git, public logs, and broadly accessible artifacts. `tofu state show`
and `tofu output -json` can reveal sensitive values. Bootstrap state needs an encrypted,
access-controlled backup independent of the storage it manages.

## Verification scope

Credential-free CI checks configuration and mocked plans. It does not audit cloud
accounts or establish production compliance. Adopters own organization-specific
IAM, logging, key management, backups, approval policy, and recovery exercises.

The quality helper blocks HIGH and CRITICAL Trivy findings and fails on missing
checks or unrecognized reports. It keeps raw reports in memory and prints diagnostic
check IDs. Trusted deployment workflows scan both source and the saved plan before
apply. Native local use can bypass these checks. See [quality checks](docs/quality.md).
Gitleaks checks secrets independently of infrastructure policy.

Atlantis runs the quality helper from the PR checkout, so plan-stage code is untrusted.
[Atlantis setup](docs/atlantis.md#know-what-the-checks-trust) lists the controls
that make its checks meaningful. Review it, [migration](docs/migration.md), and
[bootstrap recovery](docs/bootstrap.md) before enabling deployment credentials.
