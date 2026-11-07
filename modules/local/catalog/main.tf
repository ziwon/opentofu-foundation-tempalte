resource "terraform_data" "catalog" {
  input = {
    name        = var.name
    tags        = var.tags
    description = var.description
  }
}
