# gcp/bootstrap/state

Stack that each `live/<environment>/gcp/bootstrap/state` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The state bucket lives in the core module [`modules/gcp/storage-bucket`](../../../../modules/gcp/storage-bucket),
called as `module "bucket"` with a 30-day soft delete retention.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
