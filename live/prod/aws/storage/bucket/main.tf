module "stack" {
  source         = "../../../../../modules/aws/storage/bucket"
  context        = { id = module.context.id, tags = module.context.tags }
  aws_account_id = var.aws_account_id
}
