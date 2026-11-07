variables {
  name                = "starter-fixture-dev"
  resource_group_name = "starter-fixture-dev-rg"
  location            = "eastus"
  network_cidr        = "10.10.0.0/16"
  subnet_cidr         = "10.10.1.0/24"
  tags                = { "project" : "starter", "environment" : "dev", "managed_by" : "iac" }
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
    condition     = one(azurerm_network_security_group.this.security_rule).access == "Deny" && one(azurerm_network_security_group.this.security_rule).direction == "Inbound" && one(azurerm_network_security_group.this.security_rule).source_address_prefix == "Internet"
    error_message = "The subnet must explicitly deny inbound Internet traffic."
  }
  assert {
    condition     = azurerm_subnet_network_security_group_association.this.subnet_id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example/subnets/private" && azurerm_subnet_network_security_group_association.this.network_security_group_id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/networkSecurityGroups/example"
    error_message = "The security group must protect the private subnet."
  }
  assert {
    condition     = azurerm_virtual_network.this.address_space == toset([var.network_cidr]) && azurerm_subnet.private.address_prefixes == tolist([var.subnet_cidr])
    error_message = "The network and subnet must use the supplied ranges."
  }
}

run "names_and_tags" {
  command = plan
  assert {
    condition     = azurerm_virtual_network.this.name == "starter-fixture-dev" && azurerm_network_security_group.this.name == "starter-fixture-dev-nsg" && azurerm_subnet.private.name == "private"
    error_message = "Network names must derive from the supplied name."
  }
  assert {
    condition     = azurerm_virtual_network.this.resource_group_name == var.resource_group_name && azurerm_virtual_network.this.location == var.location && azurerm_virtual_network.this.tags == tomap(var.tags) && azurerm_network_security_group.this.tags == tomap(var.tags)
    error_message = "Network resources must use the supplied resource group, location, and tags."
  }
  assert {
    condition     = output.virtual_network_id == "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example/providers/Microsoft.Network/virtualNetworks/example"
    error_message = "The output must identify the virtual network."
  }
}
