moved {
  from = aws_s3_bucket.this
  to   = module.bucket.aws_s3_bucket.this
}

moved {
  from = aws_s3_bucket_public_access_block.this
  to   = module.bucket.aws_s3_bucket_public_access_block.this
}

moved {
  from = aws_s3_bucket_ownership_controls.this
  to   = module.bucket.aws_s3_bucket_ownership_controls.this
}

moved {
  from = aws_s3_bucket_versioning.this
  to   = module.bucket.aws_s3_bucket_versioning.this
}

moved {
  from = aws_s3_bucket_server_side_encryption_configuration.this
  to   = module.bucket.aws_s3_bucket_server_side_encryption_configuration.this
}

moved {
  from = aws_s3_bucket_policy.tls
  to   = module.bucket.aws_s3_bucket_policy.tls
}

moved {
  from = aws_kms_key.state
  to   = module.key.aws_kms_key.this
}
