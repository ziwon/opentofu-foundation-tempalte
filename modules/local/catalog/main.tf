resource "terraform_data" "catalog" {
  input = {
    name = var.name
    # Preserve the object type stored by existing terraform_data state.
    tags        = merge(var.tags, {})
    description = var.description
  }
}
