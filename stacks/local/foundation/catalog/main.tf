module "naming" {
  source      = "../../../../modules/naming"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
}

resource "terraform_data" "catalog" {
  input = {
    name        = module.naming.id
    tags        = module.naming.tags
    description = var.description
  }
}
