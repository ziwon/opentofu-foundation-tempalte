resource "azurerm_resource_group" "this" {
  name     = "${var.context.id}-rg"
  location = var.location
  tags     = var.context.tags
}
module "network" {
  source              = "../../../../modules/azure/network"
  name                = var.context.id
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  network_cidr        = var.network_cidr
  subnet_cidr         = var.subnet_cidr
  tags                = var.context.tags
}
