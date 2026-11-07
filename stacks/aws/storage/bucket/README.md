# aws/storage/bucket

Stack that each `live/<environment>/aws/storage/bucket` root calls as
`module "stack"`. Pass `context` from `modules/context` and the declared resource inputs.
Provider configuration and backend state belong to the calling root.

The encryption key lives in [`modules/aws/kms-key`](../../../../modules/aws/kms-key),
called as `module "key"`. The bucket lives in [`modules/aws/s3-bucket`](../../../../modules/aws/s3-bucket),
called as `module "bucket"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
