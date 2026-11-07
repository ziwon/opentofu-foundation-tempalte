variables {
  name           = "starter-fixture-dev"
  aws_account_id = "000000000000"
  kms_key_arn    = "arn:aws:kms:us-east-1:000000000000:key/00000000-0000-0000-0000-000000000000"
}

mock_provider "aws" {}
run "private_versioned_bucket" {
  command = plan
  assert {
    condition     = aws_s3_bucket.this.bucket == "starter-fixture-dev-000000000000" && !aws_s3_bucket.this.force_destroy
    error_message = "The bucket must be named <name>-<account id> and refuse deletion while nonempty."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_acls && aws_s3_bucket_public_access_block.this.block_public_policy && aws_s3_bucket_public_access_block.this.ignore_public_acls && aws_s3_bucket_public_access_block.this.restrict_public_buckets
    error_message = "All four public access protections must be enabled."
  }
  assert {
    condition     = one(aws_s3_bucket_ownership_controls.this.rule).object_ownership == "BucketOwnerEnforced"
    error_message = "The bucket owner must own every object, with ACLs disabled."
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled"
    error_message = "The bucket must retain object versions."
  }
  assert {
    condition     = one(one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms" && one(one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default).kms_master_key_id == var.kms_key_arn && one(aws_s3_bucket_server_side_encryption_configuration.this.rule).bucket_key_enabled
    error_message = "Objects must be encrypted with the supplied customer-managed key and an S3 bucket key."
  }
  assert {
    condition     = jsondecode(aws_s3_bucket_policy.tls.policy).Statement == [{ Sid = "RequireTLS", Effect = "Deny", Principal = "*", Action = "s3:*", Resource = [aws_s3_bucket.this.arn, "${aws_s3_bucket.this.arn}/*"], Condition = { Bool = { "aws:SecureTransport" = "false" } } }]
    error_message = "The bucket policy must deny every request made without TLS."
  }
  assert {
    condition     = output.id == aws_s3_bucket.this.id
    error_message = "The module must expose the bucket ID."
  }
}

run "longest_bucket_name" {
  command = plan
  variables {
    name = "a234567890123456789012345678901234567890123456789b"
  }
  assert {
    condition     = length(aws_s3_bucket.this.bucket) == 63
    error_message = "A 63-character bucket name must be accepted."
  }
}

run "bucket_name_too_long" {
  command = plan
  variables {
    name = "a2345678901234567890123456789012345678901234567890b"
  }
  expect_failures = [aws_s3_bucket.this]
}
