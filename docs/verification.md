# Verification scope

The native-root refactor changes both layout and local policy. The former
shared-root test results do not prove the new layout or approval behavior.
Use the commands below to verify the current checkout and retain their output
with the reviewed revision.

| Check | Command or evidence |
| --- | --- |
| Layout, links, formatting, validation, lint, source security, and mock tests | `python3 tools/check.py` |
| Real native local lifecycle | `python3 tools/smoke.py` |
| Previous-address migration with stable local resource IDs | `python3 tools/migration_smoke.py` |
| Real scanner and linter acceptance and rejection | `python3 tools/quality_smoke.py` |
| Optional real Atlantis configuration and workflow checks | `mise -C integrations/atlantis exec -- python3 ../../tools/atlantis_native_smoke.py` |
| Directory secret scan | `gitleaks dir . --redact --no-banner` |
| History secret scan | `gitleaks git . --redact --no-banner` |

OpenTofu 1.12.5 is pinned in `mise.toml`. The existing provider selections remain
AWS 6.71.0, AzureRM 5.12.0, and Google 8.9.0 under their explicit
`registry.opentofu.org` addresses. TFLint 0.65.0 and Trivy 0.76.1 are pinned.
Cloud linter plugins remain AWS 0.50.0, AzureRM 0.33.0, and Google 0.41.0.

## Native-root acceptance criteria

Each of the 30 live leaves must initialize and validate as a native root.
Resource compositions must have no provider configuration or backend.
Root locks must retain the provider identities and selections from the previous layout.
Mock tests must cover cloud resource protections and meaningful environment inputs.

The local lifecycle must run native init, saved plan, apply, output, and state
commands without repository Python in the deployment path. Fixture code may use
Python to set up and inspect that test. It must not become a prerequisite for ordinary use.

The migration fixture must apply the previous local configuration, initialize the
new root against the same state, and retain resource IDs with no resource update
or replacement. Every old managed-resource address needs a checked-in moved block.
A passing local fixture does not prove a migration against deployed cloud state.

Real security checks must accept safe source and plans and reject unsafe or
unrecognized inputs. Atlantis verification must check the actual configured
native init, plan, and apply workflow with explicit quality steps.

## Limits

Mocked cloud tests and fake-credential security plans do not deploy cloud resources.
Actual fixture applies and destroys are restricted to disposable local
`terraform_data` resources. Local validation does not establish live cloud
permissions, drift, backend recovery, hosted webhook behavior, or approval enforcement.

Adopters must verify their own cloud authentication, state access, sandbox
migration, recovery, and trusted deployment controls. A workflow definition is
not evidence that hosted CI has run. Record hosted results separately.
