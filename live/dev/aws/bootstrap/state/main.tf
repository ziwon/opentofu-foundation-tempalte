module "stack" {
  source         = "../../../../../modules/aws/bootstrap/state"
  context        = { id = module.context.id, tags = module.context.tags }
  aws_account_id = var.aws_account_id
  region         = var.region
}
