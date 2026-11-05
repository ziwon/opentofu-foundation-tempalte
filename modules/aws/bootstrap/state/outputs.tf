output "backend_config" {
  description = "Backend settings for a workload root; add its explicit state key or prefix."
  value = {
    bucket              = aws_s3_bucket.this.id
    region              = var.region
    encrypt             = true
    use_lockfile        = true
    allowed_account_ids = [var.aws_account_id]
    kms_key_id          = aws_kms_key.state.arn
  }
}
