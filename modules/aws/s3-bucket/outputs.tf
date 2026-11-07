output "id" {
  description = "Bucket name, which S3 uses as the bucket ID."
  value       = aws_s3_bucket.this.id
}
output "kms_key_arn" {
  description = "KMS key that default object encryption uses."
  value       = one(one(aws_s3_bucket_server_side_encryption_configuration.this.rule).apply_server_side_encryption_by_default).kms_master_key_id
}
