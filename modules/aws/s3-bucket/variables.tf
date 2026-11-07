variable "name" {
  description = "Bucket name prefix; the module appends the AWS account ID."
  type        = string
}

variable "aws_account_id" {
  description = "AWS account that owns the bucket; it makes the bucket name globally unique."
  type        = string
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN for default object encryption."
  type        = string
}
