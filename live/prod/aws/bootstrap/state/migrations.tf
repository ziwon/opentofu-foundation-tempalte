moved {
  from = aws_s3_bucket.this
  to   = module.stack.aws_s3_bucket.this
}

moved {
  from = aws_s3_bucket_public_access_block.this
  to   = module.stack.aws_s3_bucket_public_access_block.this
}

moved {
  from = aws_s3_bucket_ownership_controls.this
  to   = module.stack.aws_s3_bucket_ownership_controls.this
}

moved {
  from = aws_s3_bucket_versioning.this
  to   = module.stack.aws_s3_bucket_versioning.this
}

moved {
  from = aws_s3_bucket_server_side_encryption_configuration.this
  to   = module.stack.aws_s3_bucket_server_side_encryption_configuration.this
}

moved {
  from = aws_kms_key.state
  to   = module.stack.aws_kms_key.state
}

moved {
  from = aws_s3_bucket_policy.tls
  to   = module.stack.aws_s3_bucket_policy.tls
}
