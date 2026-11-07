variables {
  location     = "eastus"
  network_cidr = "10.10.0.0/16"
  subnet_cidr  = "10.10.1.0/24"
  context      = { "id" : "starter-fixture-dev", "tags" : { "project" : "starter", "environment" : "dev", "managed_by" : "iac" } }
}

mock_provider "azurerm" {
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
    condition     = one(azurerm_network_security_group.this.security_rule).access == "Deny" && one(azurerm_network_security_group.this.security_rule).source_address_prefix == "Internet"
    error_message = "The subnet must explicitly deny inbound Internet traffic."
  }
}
