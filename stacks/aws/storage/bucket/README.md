# aws/storage/bucket

Stack that each `live/<environment>/aws/storage/bucket` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
