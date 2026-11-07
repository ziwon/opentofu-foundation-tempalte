output "id" {
  description = "Bucket name, which S3 uses as the bucket ID."
  value       = aws_s3_bucket.this.id
}
