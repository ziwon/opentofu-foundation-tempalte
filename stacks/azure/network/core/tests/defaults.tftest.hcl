variables {
  location     = "eastus"
  network_cidr = "10.10.0.0/16"
  subnet_cidr  = "10.10.1.0/24"
  context      = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "azurerm" {
  mock_resource "azurerm_virtual_network" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example" }
  }
  mock_resource "azurerm_subnet" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example/subnets/private" }
  }
  mock_resource "azurerm_network_security_group" {
    defaults = { id = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/networkSecurityGroups/example" }
  }
}
run "private_network" {
  command = plan
  assert {
    condition     = output.resource_id == module.network.virtual_network_id && output.resource_id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example"
    error_message = "The stack must expose the virtual network that the network module manages."
  }
  assert {
    condition     = azurerm_resource_group.this.name == "starter-fixture-dev-rg" && azurerm_resource_group.this.location == var.location && azurerm_resource_group.this.tags == tomap(var.context.tags)
    error_message = "The resource group must use the deployment name, location, and context tags."
  }
  assert {
    condition     = module.network.network_cidr == "10.10.0.0/16" && module.network.subnet_cidr == "10.10.1.0/24"
    error_message = "The network and private subnet must use network_cidr and subnet_cidr."
  }
}
