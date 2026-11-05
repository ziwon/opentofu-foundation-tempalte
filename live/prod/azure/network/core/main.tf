module "stack" {
  source       = "../../../../../modules/azure/network/core"
  context      = { id = module.context.id, tags = module.context.tags }
  location     = var.location
  network_cidr = var.network_cidr
  subnet_cidr  = var.subnet_cidr
}
