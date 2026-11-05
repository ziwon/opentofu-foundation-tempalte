module "stack" {
  source      = "../../../../../modules/gcp/network/core"
  context     = { id = module.context.id, tags = module.context.tags }
  region      = var.region
  subnet_cidr = var.subnet_cidr
}
