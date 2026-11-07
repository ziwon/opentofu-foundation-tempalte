output "arn" {
  description = "Key ARN for encryption settings."
  value       = aws_kms_key.this.arn
}
