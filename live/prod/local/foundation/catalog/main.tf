module "stack" {
  source      = "../../../../../stacks/local/foundation/catalog"
  context     = { id = module.context.id, tags = module.context.tags }
  description = var.description
}
