locals {
  id = "${var.namespace}-${var.name}-${var.environment}"
  tags = merge(var.tags, {
    project     = var.namespace
    environment = var.environment
    managed_by  = "iac"
  })
}
