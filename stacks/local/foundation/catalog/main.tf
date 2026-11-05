resource "terraform_data" "catalog" {
  input = {
    name        = module.context.id
    tags        = module.context.tags
    description = var.description
  }
}
