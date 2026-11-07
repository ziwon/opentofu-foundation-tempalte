# azure/storage/bucket

Stack that each `live/<environment>/azure/storage/bucket` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The stack owns the resource group. The storage account and the `objects` container live
in the core module [`modules/azure/storage-account`](../../../../modules/azure/storage-account),
called as `module "storage_account"` with locally redundant replication and 7-day soft
deletion. `migrations.tf` moves both resources from this stack into the module.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
