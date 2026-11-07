module "network" {
  source      = "../../../../modules/gcp/network"
  name        = var.context.id
  region      = var.region
  subnet_cidr = var.subnet_cidr
}
