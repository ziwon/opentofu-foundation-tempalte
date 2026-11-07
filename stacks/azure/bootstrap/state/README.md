# azure/bootstrap/state

Stack that each `live/<environment>/azure/bootstrap/state` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The stack owns the state resource group, with `prevent_destroy`. The storage account and
the `tfstate` container live in the core module
[`modules/azure/storage-account`](../../../../modules/azure/storage-account), called as
`module "storage_account"` with zone-redundant replication and 30-day soft deletion.
`migrations.tf` moves both resources from this stack into the module.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
