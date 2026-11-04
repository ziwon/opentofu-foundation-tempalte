# Operations

## Normal change

Edit the stack or its live inputs, run `test`, create a plan, review it, and apply
that saved plan. A successful plan with changes is treated as success, including
the engine's detailed exit code 2. Ordinary commands use readonly provider locks.

```sh
python3 tools/infra.py lint dev/aws/network/core
python3 tools/infra.py security dev/aws/network/core
python3 tools/infra.py test dev/aws/network/core
python3 tools/infra.py plan dev/aws/network/core
python3 tools/infra.py apply dev/aws/network/core
```

The apply prompt requires the exact deployment name. Use `--yes` only when an
external automation process has approved that plan. The native engine also
checks state freshness; the runner's source checks do not replace native locking.
Both plan and apply scan the saved binary plan with Trivy. A security failure blocks
application, including with `--yes`; see [quality checks](quality.md).

## Inspect state without changing it

```sh
python3 tools/infra.py state-list dev/local/foundation/catalog
python3 tools/infra.py state-show dev/local/foundation/catalog terraform_data.catalog
```

Queries require the selected deployment to be initialized and use its isolated
working directory and native backend. Resource addresses are passed as one argument;
quote addresses containing map keys, for example `'aws_instance.worker["blue"]'`.
`state-show` can print sensitive attributes. Use an authorized terminal and do not
redirect the output into committed files or public logs. State mutation commands
are intentionally outside this interface.

## A failed plan or apply

A failed plan removes any prior saved plan, so it cannot accidentally be applied.
After an apply attempt, the plan is discarded even if the command failed. Inspect
the engine's output and actual state, then plan again. Partial applies may have
created or changed resources. Do not delete state to retry.

For stale-plan errors, run `plan` again. The runner checks inputs, backend,
engine/version, provider lock, stack code, local module code, and plan bytes.
Quality-tool/policy changes also invalidate plans; documentation-only changes do not.

The AWS storage example now creates a customer-managed KMS key. For an existing
deployment, review permissions and charges; changing default encryption affects new
objects, not existing objects. The Azure storage example now denies networks outside
its allowlist; configure operator and workload access before applying to avoid 403s.

## Delete a deployment

```sh
python3 tools/infra.py plan dev/local/foundation/catalog --destroy
python3 tools/infra.py apply dev/local/foundation/catalog
```

Review the destruction plan before applying. Storage examples deliberately
retain data, protect storage/key resources with `prevent_destroy`, or refuse
deletion of nonempty buckets. An approved data-retention
decision is separate from deleting an infrastructure deployment. Do not delete
the live directory until the deployment has been retired and its state retained
according to your recovery policy.

## Provider updates

Update the version constraint in the stack's `versions.tf`, then resolve and
review the lock file explicitly:

```sh
python3 tools/infra.py lock dev/aws/network/core --upgrade
python3 tools/infra.py test dev/aws/network/core
python3 tools/infra.py --engine terraform test dev/aws/network/core
```

Commit both version and lock changes. Inspect upstream major-version migration
notes and any externally downloaded artifacts; a module version and its runtime
artifacts sometimes need to change together. Mock tests do not prove compatibility
with existing state, so review a live plan before deployment.

Provider sources explicitly use `registry.opentofu.org` so both engines install
the same package addresses and verify the same lock entries. Changing registries
is a provider/state migration; do not casually rewrite lock-file addresses.

## Backend or engine migration

Initialization does not silently reconfigure or migrate state. If backend data
changes, native `init` will request a migration/reconfiguration decision.

1. Back up the existing state through a secure, authorized mechanism.
2. Stop other operations on that deployment and verify both old/new identities.
3. Generate the new backend configuration with the runner's `init` command; it
   may stop when it detects the changed backend.
4. Follow the selected engine's documented `init -migrate-state` procedure using
   the deployment's `.infra/<engine>/<deployment>/data` as `TF_DATA_DIR` and the
   generated `.infra/<engine>/<deployment>/backend.generated.hcl`.
5. Run the runner's `init` again, then inspect a fresh plan and verify resources.

Do not use `-reconfigure` as a substitute for moving existing state. A new empty
backend can make existing resources appear unmanaged. Switching engines also
requires reviewing state-format/provider compatibility; the CI compatibility
matrix tests code execution, not arbitrary cross-engine state migrations.

See [OpenTofu initialization](https://opentofu.org/docs/cli/commands/init/) and
[Terraform initialization](https://developer.hashicorp.com/terraform/cli/commands/init).

## Deployment automation

CI is intentionally credential-free. To add GitHub Actions deployments, use a
trusted workflow, cloud OIDC, environment approvals, deployment-scoped permissions,
and one concurrency group per deployment. Treat plan artifacts as confidential:
limit access/retention and bind approval to the reviewed commit and plan checksum.
Never run untrusted pull-request code with deployment credentials.

Atlantis or another orchestrator can call the same runner with an explicit
deployment ID. Give each concurrent deployment isolated working data and retain
its plan files until application. Decide approval and apply requirements in the
trusted server configuration, and keep deployment access out of fork checks.
