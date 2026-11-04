output "backend_config" {
  description = "Copy this non-secret object to a regular deployment's backend.json; keys are derived by the runner."
  value = {
    bucket              = aws_s3_bucket.this.id
    region              = var.region
    encrypt             = true
    use_lockfile        = true
    allowed_account_ids = [var.aws_account_id]
    kms_key_id          = aws_kms_key.state.arn
  }
}
