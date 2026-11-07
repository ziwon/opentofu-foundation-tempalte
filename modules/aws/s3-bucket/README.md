# aws/s3-bucket

Core module that owns one private, versioned S3 bucket. It blocks public access,
enforces bucket-owner object ownership, encrypts objects with the supplied KMS key
and an S3 bucket key, and denies requests made without TLS. `prevent_destroy`
protects the bucket in every stack that calls it.

The bucket name is `<name>-<aws_account_id>`. A plan fails when that exceeds 63
characters. Pass `name`, `aws_account_id`, and `kms_key_arn`. The `id` output is the
bucket name.

`stacks/aws/bootstrap/state` and `stacks/aws/storage/bucket` call it as `module "bucket"`.

Run plan-only mocked checks with `tofu init -backend=false` and `tofu test`.
