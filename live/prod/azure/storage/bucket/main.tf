module "stack" {
  source             = "../../../../../modules/azure/storage/bucket"
  context            = { id = module.context.id, tags = module.context.tags }
  allowed_ip_ranges  = var.allowed_ip_ranges
  allowed_subnet_ids = var.allowed_subnet_ids
  location           = var.location
  subscription_id    = var.subscription_id
}
