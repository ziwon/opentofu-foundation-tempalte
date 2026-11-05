module "stack" {
  source       = "../../../../../modules/aws/network/core"
  context      = { id = module.context.id, tags = module.context.tags }
  network_cidr = var.network_cidr
  subnet_cidr  = var.subnet_cidr
}
