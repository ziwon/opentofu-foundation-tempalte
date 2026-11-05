resource "terraform_data" "catalog" {
  input = {
    name = var.context.id
    # Preserve the object type stored by existing terraform_data state.
    tags        = merge(var.context.tags, {})
    description = var.description
  }
}
