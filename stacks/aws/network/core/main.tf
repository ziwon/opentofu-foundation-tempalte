module "vpc" {
  source       = "../../../../modules/aws/vpc"
  name         = var.context.id
  network_cidr = var.network_cidr
  subnet_cidr  = var.subnet_cidr
}
