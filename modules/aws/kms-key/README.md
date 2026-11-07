# aws/kms-key

Core module that owns one customer-managed AWS KMS key with automatic rotation and a
30-day deletion window. `prevent_destroy` protects the key in every stack that calls it.
Pass a `description`. Use the `arn` output for encryption settings.

`stacks/aws/bootstrap/state` and `stacks/aws/storage/bucket` call it as `module "key"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
