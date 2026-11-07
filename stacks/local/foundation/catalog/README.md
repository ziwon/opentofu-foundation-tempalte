# local/foundation/catalog

Stack that each `live/<environment>/local/foundation/catalog` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The catalog entry lives in the core module [`modules/local/catalog`](../../../../modules/local/catalog),
called as `module "catalog"`. `migrations.tf` moves the entry from this stack into it.

Run checks with `tofu init -backend=false` and `tofu test`. The test applies and
destroys a local `terraform_data` resource, because its output is unknown until apply.
