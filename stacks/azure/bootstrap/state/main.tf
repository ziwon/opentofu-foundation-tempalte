resource "azurerm_resource_group" "this" {
  name     = "${var.context.id}-rg"
  location = var.location
  tags     = var.context.tags
  lifecycle { prevent_destroy = true }
}
module "storage_account" {
  source                = "../../../../modules/azure/storage-account"
  name_base             = var.context.id
  subscription_id       = var.subscription_id
  resource_group_name   = azurerm_resource_group.this.name
  location              = azurerm_resource_group.this.location
  replication_type      = "ZRS"
  delete_retention_days = 30
  container_name        = "tfstate"
  allowed_ip_ranges     = var.allowed_ip_ranges
  allowed_subnet_ids    = var.allowed_subnet_ids
  tags                  = var.context.tags
}
