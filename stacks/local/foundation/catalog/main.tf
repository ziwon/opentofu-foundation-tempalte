module "catalog" {
  source      = "../../../../modules/local/catalog"
  name        = var.context.id
  tags        = var.context.tags
  description = var.description
}
