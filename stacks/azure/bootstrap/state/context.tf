module "context" {
  source      = "../../../../modules/context"
  namespace   = var.namespace
  name        = var.name
  environment = var.environment
  tags        = var.tags
}
