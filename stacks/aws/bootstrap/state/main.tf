module "key" {
  source      = "../../../../modules/aws/kms-key"
  description = "Encrypt infrastructure state for ${var.context.id}"
}

module "bucket" {
  source         = "../../../../modules/aws/s3-bucket"
  name           = var.context.id
  aws_account_id = var.aws_account_id
  kms_key_arn    = module.key.arn
}
