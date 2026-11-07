# Migrate an existing deployment to native roots

This guide covers the move from shared executable stacks to
`live/<environment>/<cloud>/<group>/<stack>` roots. It preserves backend storage
identity and moves managed resources into `module.stack`. It does not authorize a
cloud apply or a change of backend storage.

## Check the two identities

A state location and an address inside that state are separate identities.
Verify both before planning an existing deployment.

| Item | Previous layout | Native root |
| --- | --- | --- |
| Executable directory | `stacks/<cloud>/<group>/<stack>` | `live/<environment>/<cloud>/<group>/<stack>` |
| Local and bootstrap state | `.infra/state/<deployment>/terraform.tfstate` | Same repository-relative path |
| S3 and Azure state key | `<deployment>/terraform.tfstate` | Same explicit key in `backend.tf` |
| GCS state prefix | `<deployment>` | Same explicit prefix in `backend.tf` |
| Managed address example | `aws_vpc.this` | `module.stack.aws_vpc.this` |
| Provider identity | Existing explicit registry address and selection | Unchanged root lock entry |

Each root's `migrations.tf` contains a `moved` block for every supplied managed
resource. For example:

```hcl
moved {
  from = aws_vpc.this
  to   = module.stack.aws_vpc.this
}
```

These blocks tell OpenTofu that the resource at the old address is the same
resource at the new address. Keep them committed so roots with older state can
still upgrade. Do not remove and reimport resources merely because the code moved.

`python3 tools/check_layout.py` enforces this without state or cloud access.
`tools/legacy-addresses.json` lists the addresses each shared stack declared.
For every live root, the check follows each listed address through the `moved`
blocks in the root and in every local module it calls. Each address must end at
a distinct managed resource that the code still declares. A `moved` block must
point at a declared resource or at the `from` of another move. Every inventory
entry must match a root, so renaming a stack fails until you add moves or retire
the entry with its state.

The check reads a small HCL subset and rejects everything outside it. It rejects
`count`, `for_each`, `lifecycle { enabled }`, module sources other than `./name/...`
or leading `../` segments followed by plain names, symlinked module directories,
block labels that are not identifiers, heredocs, template directives, escaped interpolations, whitespace other than
spaces, tabs, and line feeds, override files, and `.tofu` or `.tf.json` files. It
ignores comments and hidden files, as OpenTofu does. The check catches missing or
wrong moves in ordinary configuration. It is not proof against configuration written
to mislead it. Before applying a migrated root, confirm that its saved plan has no
destroy or replace actions.
It does not know about resources you added to your own copy of the old layout.
Add those addresses to the inventory before you rely on the check.

## Prepare the existing state

1. Stop concurrent operations on the deployment. Record the current source revision,
   OpenTofu version, provider lock, backend identity, and default workspace.
2. Back up state through an authorized, access-controlled mechanism. State can contain secrets.
3. Preserve `.infra/state/` before updating or replacing a checkout. It contains
   actual local and bootstrap state, not disposable cache data.
4. Compare the new root's `backend.tf` with the previous effective backend settings.
   Retain the real bucket, container, account, key, prefix, and local path values.
5. Preserve your existing `terraform.tfvars.json` values. The checked-in cloud values
   are examples and must not replace an adopted deployment's configuration.
6. Review every moved address against your customized resources. Add moves for any
   extra managed resources that you move into the composition.

For a local or bootstrap deployment, copy the existing state and any recovery
backups to an encrypted location outside the checkout. The root's relative path
resolves to the same `.infra/state/<deployment>/terraform.tfstate` file when the
repository stays in place. If you use a new checkout, restore that state securely
to the same repository-relative path before initialization.

For remote state, use your approved backend snapshot or state-backup procedure.
Do not print state in CI or commit the backup. If expected state is missing, stop
and recover it. Do not apply a plan that recreates existing resources as a recovery step.

## Initialize and inspect a fresh plan

Discard saved plans from the old layout. Run the following from the updated repository:

```sh
tofu -chdir=live/dev/aws/network/core init -lockfile=readonly
tofu -chdir=live/dev/aws/network/core plan -out=migration.tfplan
tofu -chdir=live/dev/aws/network/core show migration.tfplan
```

Substitute the actual deployment path. Review the native backend initialization
result and confirm it selected the existing state. The layout change alone does
not require copying remote state or changing its key. Do not add `-migrate-state`
or `-reconfigure` to silence an unexpected backend warning. Investigate the
backend identity first.

For an unchanged deployment, expect address moves and no resource creates,
updates, replacements, or destroys. Check resource IDs, names, tags, and protection
settings. Investigate any resource action before continuing. Drift or custom
changes may need a separate reviewed change.

Run your source and saved-plan scans, obtain the required approval, and apply the
reviewed migration plan through your deployment process. Applying records the
new addresses in state. Then verify outputs and `tofu state list` against the
expected `module.stack` addresses, and back up state again.

Do not restore the old configuration after applying the moves without planning
an explicit reverse migration. Keep both the pre-migration backup and the source
revision according to your recovery policy.

## Update scripts and policy

Point local commands and automation at the live root. Remove old generated
backend-file arguments and old `TF_DATA_DIR` overrides. Root-local `.terraform/`
metadata replaces the former runner's working directories. Keep actual state
until its retention policy allows deletion.

Native local commands no longer enforce checkout fingerprints, plan receipts,
exact-deployment-name prompts, automatic source or plan scans, or plan cleanup.
A native saved-plan apply does not ask for confirmation. This is a deliberate
policy change, not equivalent enforcement through a different command spelling.

Trusted deployment automation must enforce scans, approvals, trusted authors,
and plan retention. Update Atlantis plan and apply together to use its built-in
steps and native `PLANFILE`. See [Atlantis setup](atlantis.md) and
[security policy](../SECURITY.md).
