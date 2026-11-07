# gcp/storage/bucket

Stack that each `live/<environment>/gcp/storage/bucket` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The bucket lives in the core module [`modules/gcp/storage-bucket`](../../../../modules/gcp/storage-bucket),
called as `module "bucket"`. `migrations.tf` moves the bucket from this stack into it.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
