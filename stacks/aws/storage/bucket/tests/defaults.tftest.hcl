mock_provider "aws" {}
run "private_versioned_storage" {
  command = plan
  assert {
    condition     = aws_kms_key.storage.enable_key_rotation && one(one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms"
    error_message = "Storage must use a rotating customer-managed encryption key."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.this.block_public_acls && aws_s3_bucket_public_access_block.this.block_public_policy && aws_s3_bucket_public_access_block.this.ignore_public_acls && aws_s3_bucket_public_access_block.this.restrict_public_buckets
    error_message = "All four public access protections must be enabled."
  }
  assert {
    condition     = aws_s3_bucket_versioning.this.versioning_configuration[0].status == "Enabled" && !aws_s3_bucket.this.force_destroy
    error_message = "Storage must retain versions and refuse deletion of nonempty buckets."
  }
}
